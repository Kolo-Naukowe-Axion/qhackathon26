"""Expand and structurally audit the Stage 2 design. No simulation or solver runs.

python3 scripts/stage2_blueprint.py --output output/stage2-design
"""

import argparse
import hashlib
import itertools
import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def positive(value):
    return type(value) is int and value > 0


def ratio(value):
    require(isinstance(value, list) and len(value) == 2
            and all(positive(v) for v in value), "Expected positive rational pair")
    return Fraction(*value)


def ceil_fraction(value):
    return -(-value.numerator // value.denominator)


def expand(design):
    require(design["schema"] == "metaltech-stage2-blueprint.v1", "Unknown schema")
    horizon = design["horizon_ticks"]
    require(positive(horizon) and positive(design["tick_minutes"]), "Invalid time grid")
    machines = {m["id"]: m for m in design["machines"]}
    require(len(machines) == len(design["machines"]), "Duplicate machine ids")
    for machine in machines.values():
        require(machine["hall"] in ("A", "B"), "Unknown hall")
        require(positive(machine["input_capacity"]), "Invalid input capacity")
        require(machine["process"] in design["mode_duration_factors"], "Missing modes")
        ratio(machine["duration_factor"])
    for modes in design["mode_duration_factors"].values():
        require(bool(modes), "Empty mode domain")
        for factor in modes.values():
            ratio(factor)

    bom = design["bill_of_materials"]["pump"]
    require(set(design["recipes"]) == set(bom) | {"pump"}, "Uncovered recipes")
    require(all(positive(v) for v in bom.values()), "Invalid BOM quantity")
    for recipe in design["recipes"].values():
        require(bool(recipe), "Empty recipe")
        for step in recipe:
            require(positive(step["base_ticks"]), "Invalid base duration")
            require(any(m["process"] == step["process"] for m in machines.values()),
                    "No eligible machine")

    order_spec = design["orders"]
    require(positive(order_spec["known_count"]), "Invalid order count")
    require(positive(order_spec["precision_every_nth_order"]), "Invalid precision cycle")
    require(bool(order_spec["families"]) and bool(order_spec["release_cycle_ticks"])
            and bool(order_spec["due_cycle_ticks"]), "Empty order cycle")
    orders, lots, operations = [], [], []
    for index in range(order_spec["known_count"]):
        order = f'{order_spec["prefix"]}{index + 1:02d}'
        release = order_spec["release_cycle_ticks"][index % len(order_spec["release_cycle_ticks"])]
        due = order_spec["due_cycle_ticks"][index % len(order_spec["due_cycle_ticks"])]
        require(type(release) is int and type(due) is int and 0 <= release < due <= horizon,
                "Invalid order dates")
        family = order_spec["families"][index % len(order_spec["families"])]
        orders.append(dict(id=order, family=family, release_tick=release, due_tick=due,
                           precision_required=(index + 1) % order_spec["precision_every_nth_order"] == 0))
        component_ends = []
        for recipe_name, quantity in list(bom.items()) + [("pump", 1)]:
            for copy in range(quantity):
                unit = f"{order}/{recipe_name}/{copy + 1}"
                if recipe_name != "pump":
                    lots.append(dict(id=unit, order=order, recipe=recipe_name))
                previous = list(component_ends) if recipe_name == "pump" else []
                for sequence, step in enumerate(design["recipes"][recipe_name]):
                    op_id = f"{unit}/{sequence + 1}"
                    alternatives = []
                    for machine in machines.values():
                        if machine["process"] != step["process"]:
                            continue
                        for mode, factor in design["mode_duration_factors"][step["process"]].items():
                            duration = ceil_fraction(step["base_ticks"] * ratio(factor)
                                                     * ratio(machine["duration_factor"]))
                            alternatives.append(dict(machine=machine["id"], mode=mode, duration=duration))
                    operations.append(dict(id=op_id, order=order, unit=unit,
                                           process=step["process"], predecessors=previous,
                                           alternatives=alternatives))
                    previous = [op_id]
                if recipe_name != "pump":
                    component_ends.extend(previous)
    # Independent structural traversal: every prerequisite must have appeared.
    visited = set()
    for op in operations:
        require(op["id"] not in visited, "Duplicate operation")
        require(set(op["predecessors"]) <= visited, "Unknown predecessor or cyclic DAG")
        visited.add(op["id"])

    stages = design["uncertainty_stages"]
    require(all(0 <= s["reveal_tick"] < horizon for s in stages), "Reveal outside horizon")
    require(all(a["reveal_tick"] < b["reveal_tick"] for a, b in zip(stages, stages[1:])),
            "Reveals must increase")
    for stage in stages:
        require(sum((ratio(o["probability"]) for o in stage["outcomes"]), Fraction()) == 1,
                "Conditional probabilities do not sum to one")
        require(len({o["id"] for o in stage["outcomes"]}) == len(stage["outcomes"]),
                "Duplicate outcome ids")
        for outcome in stage["outcomes"]:
            for event in outcome["events"]:
                if "machine" in event:
                    require(event["machine"] in machines, "Unknown outage machine")
                if "start" in event:
                    require(stage["reveal_tick"] <= event["start"] < event["end"] <= horizon,
                            "Event before reveal or outside horizon")
                if event["type"] == "delivery_delay":
                    require(stage["reveal_tick"] <= event["original_tick"] < event["new_tick"] <= horizon,
                            "Invalid delayed delivery")
                if event["type"] == "urgent_orders":
                    require(event["count"] == order_spec["urgent_count_if_revealed"]
                            and stage["reveal_tick"] == event["release_tick"]
                            < order_spec["urgent_due_tick"] <= horizon, "Invalid urgent orders")
    leaves = []
    for outcomes in itertools.product(*(s["outcomes"] for s in stages)):
        probability = Fraction(1)
        for outcome in outcomes:
            probability *= ratio(outcome["probability"])
        leaves.append(dict(id="/".join(o["id"] for o in outcomes),
                           probability=[probability.numerator, probability.denominator],
                           history=[dict(reveal_tick=s["reveal_tick"], outcome=o["id"],
                                         events=o["events"]) for s, o in zip(stages, outcomes)]))
    require(sum((Fraction(*leaf["probability"]) for leaf in leaves), Fraction()) == 1,
            "Leaf probabilities do not sum to one")
    workers = design["workers"]
    require(len({w["id"] for w in workers}) == len(workers), "Duplicate worker ids")
    for worker in workers:
        start, end = worker["daily_shift"]
        require(0 <= start < end <= 24 * 60 // design["tick_minutes"]
                and bool(worker["skills"]), "Invalid worker shift/skills")
    transport = design["transport"]
    require(positive(transport["agv_count"]) and 0 <= transport["agv_soc_initial"]
            <= transport["agv_soc_capacity"], "Invalid AGV capacity/SOC")
    energy = design["energy"]
    require(0 <= energy["stationary_soc_min"] <= energy["stationary_soc_initial"]
            <= energy["stationary_soc_capacity"], "Invalid stationary battery")
    require(energy["stationary_soc_initial"] <= energy["stationary_soc_terminal_min"]
            <= energy["stationary_soc_capacity"], "Invalid terminal SOC")

    alternative_count = sum(len(o["alternatives"]) for o in operations)
    start_count = sum(max(0, horizon - a["duration"] + 1)
                      for op in operations for a in op["alternatives"])
    summary = dict(
        evidence="structural blueprint audit only; no simulation, feasibility proof or QUBO solve",
        known_orders=len(orders), known_component_lots=len(lots),
        nominal_manufacturing_operations=len(operations), machines=len(machines),
        workers=len(workers), agvs=transport["agv_count"], exogenous_leaves=len(leaves),
        total_leaf_probability="1", horizon_ticks=horizon,
        horizon_hours=horizon * design["tick_minutes"] / 60,
        nominal_machine_mode_alternatives=alternative_count,
        unpruned_start_bit_ceiling=alternative_count * horizon,
        duration_only_start_bits=start_count,
        count_excludes=["order certification/release/precedence pruning", "joint batch representation",
                        "urgent orders", "rework", "setups", "transport", "workers/tools/state",
                        "energy", "scenario copies", "slack/ancillas"],
        missing_tables=design["not_yet_tabulated"],
    )
    return dict(schema="metaltech-stage2-expanded-design.v1", orders=orders,
                component_lots=lots, nominal_operations=operations,
                exogenous_leaves=leaves, audit=summary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "instances/stage2/metaltech_pressure.json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    source = args.input.read_bytes()
    expanded = expand(json.loads(source))
    expanded["blueprint_sha256"] = hashlib.sha256(source).hexdigest()
    if args.output:
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "expanded-design.json").write_text(json.dumps(expanded, indent=2) + "\n")
        (args.output / "audit.json").write_text(json.dumps(expanded["audit"], indent=2) + "\n")
    print(json.dumps(expanded["audit"], indent=2))


if __name__ == "__main__":
    main()
