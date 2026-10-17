"""Read-only mathematical audit of frozen paired-meal evidence, without training.

Checks small-domain exact optima, objective/penalty coefficients, physical
conflict completeness and exported Ising energies. Never contacts a service.
"""
import argparse
import hashlib
import json
from pathlib import Path
import random

from .audit import audit_bundle
from .check import check_plan
from .contracts import load_bundle
from .decode import decode
from .domain import make_plan
from .meal_blocks import sector_data, sector_bits
from .paired_meals import active_meals
from .qubo import energy, objective_energy, ising


def score(metrics):
    return tuple(metrics[k] for k in ("U", "W", "B", "R"))


def audit_small_bundle(path):
    bundle = load_bundle(path)
    instance, state = bundle["instance"], bundle["snapshot"]
    groups, programs = bundle["onehot_groups"], bundle["options"]
    n = bundle["size"]["binary_variables"]
    if n > 40:
        raise ValueError("This exhaustive audit is for the small quantum bundles")
    flattened = [i for g in groups for i in g["indices"]]
    if sorted(flattened) != list(range(n)) or n != len(programs)+len(groups):
        raise AssertionError("One-hot blocks do not partition the register")
    membership = {}
    for g in groups:
        if g["indices"] != g["program_indices"]+[g["idle_index"]]:
            raise AssertionError("Incorrect idle/register layout")
        for i in g["program_indices"]:
            if min(programs[i]["allocation_order"]) != g["anchor"]:
                raise AssertionError("Incorrect demand anchor")
            membership[i] = g["anchor"]
    if sorted(membership) != list(range(len(programs))):
        raise AssertionError("Missing program in anchor partition")

    obj = bundle["objective"]
    span = sum(abs(int(c)) for c in obj["linear"])
    span += sum(abs(int(t["value"])) for t in obj["quadratic"])
    if int(bundle["penalty"]) != span+1:
        raise AssertionError("Incorrect full-polynomial penalty bound")
    lower_sum = 0
    for key in ("R", "B", "W", "U"):
        if obj["weights"][key] != lower_sum+1:
            raise AssertionError("Incorrect lexicographic weight recurrence")
        lower_sum += obj["weights"][key]*obj["component_bounds"][key]
    required = dict(U=sum(m["priority"] for m in active_meals(instance,state)),
                    W=sum(p["yield_lots"] for p in state["fixed_batches"])
                    +sum(max(programs[i]["yield_lots"] for i in g["program_indices"]) for g in groups),
                    B=len(groups),R=len(groups)+len({p["id"] for p in state["previous_unstarted"]}))
    if any(obj["component_bounds"][k] < v for k,v in required.items()):
        raise AssertionError("Declared bounds do not dominate feasible anchor bounds")

    idle = [int(i in {g["idle_index"] for g in groups}) for i in range(n)]
    if not decode(bundle,idle)["valid"]:
        raise AssertionError("No feasible all-idle continuation")
    conflicts = {tuple(pair) for pair in bundle["conflicts"]}
    expected = set()
    fixed = state["fixed_batches"]
    recovery = state.get("recovery_operations",[])
    for i,p in enumerate(programs):
        if not check_plan(instance,state,make_plan(instance,fixed+[p],recovery))["valid"]:
            raise AssertionError("An offered local program is not physically valid")
        for j in range(i):
            valid = check_plan(instance,state,make_plan(instance,fixed+[programs[j],p],recovery))["valid"]
            if membership[i] == membership[j]:
                if valid:
                    raise AssertionError("Anchor grouping excludes a compatible pair")
            elif not valid:
                expected.add((j,i))
    if conflicts != expected:
        raise AssertionError("Conflict graph differs from independent pair checks")

    spins = ising(bundle)
    rng = random.Random(20261017)
    for bits in [idle,[1]*n]+[[rng.randrange(2) for _ in range(n)] for _ in range(63)]:
        penalty = sum((sum(bits[i] for i in g["indices"])-1)**2 for g in groups)
        penalty += sum(bits[i]*bits[j] for i,j in conflicts)
        if energy(bundle,bits) != objective_energy(bundle,bits)+int(bundle["penalty"])*penalty:
            raise AssertionError("Expanded hard terms differ from literal QUBO")
        z = [1-2*x for x in bits]
        value = int(spins["constant"])+sum(int(c)*v for c,v in zip(spins["linear"],z))
        value += sum(int(t["value"])*z[t["i"]]*z[t["j"]] for t in spins["quadratic"])
        if value != 4*energy(bundle,bits):
            raise AssertionError("Exported Ising scale/sign differs from literal QUBO")

    sector = sector_data(bundle)
    best = decode(bundle,sector_bits(bundle,sector,int(sector["energy"].argmin())))
    if not best["valid"]:
        raise AssertionError("Sector ground state fails physical/encoding checks")
    return dict(path=str(path),file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                bundle_sha256=bundle["bundle_sha256"],bits=n,
                physically_checked_pairs=len(programs)*(len(programs)-1)//2,
                polynomial_and_ising_probes=65,sector_states=sector["states"],
                feasible_sector_states=int(sector["valid"].sum()),
                exact_best_metrics=best["check"]["metrics"],exact_best_energy=best["energy"],valid=True)


def audit(root):
    root = Path(root)
    cell = root/"output/catering-complete-cell-v3"
    cell_result = audit_small_bundle(cell/"quantum-qubo.json")
    saved_cell = json.loads((cell/"report.json").read_text())
    if cell_result["exact_best_metrics"] != saved_cell["reference"]:
        raise AssertionError("Fresh cell minimum differs from the retained report")
    independent = audit_bundle(load_bundle(cell/"quantum-qubo.json"))
    if independent["raw_enumeration"]["exact_best_energy"] != cell_result["exact_best_energy"]:
        raise AssertionError("Independent physical subset optimum differs from sector optimum")
    if independent["raw_enumeration"]["feasible_selections"] != cell_result["feasible_sector_states"]:
        raise AssertionError("Physical feasible-subset count differs from sector count")
    fixed = []
    for scenario in ("S0","S1","S2","S3"):
        directory = root/f"output/catering-foundation-v3/{scenario}"
        row = audit_small_bundle(directory/"quantum-qubo.json")
        saved = json.loads((directory/"quantum-sector-reference.json").read_text())
        if row["exact_best_metrics"] != saved["ground"]["check"]["metrics"]:
            raise AssertionError("Fresh fixed-pool minimum differs from the retained reference")
        fixed.append(row)
    final = []
    for directory in sorted((root/"output/catering-paired-pilot-v1").glob("*-seed-*")):
        report = json.loads((directory/"report.json").read_text())
        step = report["steps"][-1]["step"]
        path = directory/f"step-{step:02d}/qubo.json"
        row = audit_small_bundle(path)
        saved = json.loads((path.parent/"exact-sector-reference.json").read_text())
        if row["exact_best_metrics"] != saved["check"]["metrics"]:
            raise AssertionError("Fresh final-pool minimum differs from the retained reference")
        bundle = load_bundle(path)
        ids = {p["id"] for p in json.loads((directory/"quantum-plan.json").read_text())["plan"]["batches"]}
        fixed_ids = {p["id"] for p in bundle["snapshot"]["fixed_batches"]}
        chosen = ids-fixed_ids
        if not chosen <= {p["id"] for p in bundle["options"]}:
            raise AssertionError("Final incumbent absent from final offered domain")
        bits = [int(p["id"] in chosen) for p in bundle["options"]]+[0]*len(bundle["onehot_groups"])
        for g in bundle["onehot_groups"]:
            bits[g["idle_index"]] = int(not any(bits[i] for i in g["program_indices"]))
        checked = decode(bundle,bits)
        raw = json.loads((directory/"raw-reference.json").read_text())
        if raw["reference_status"] != "OPTIMAL":
            raise AssertionError("This audit requires the frozen certified raw references")
        raw_check = check_plan(bundle["instance"],bundle["snapshot"],raw["plan"])
        if not checked["valid"] or checked["check"]["metrics"] != report["final_metrics"]:
            raise AssertionError("Final incumbent differs from the checked report")
        if not raw_check["valid"] or raw_check["metrics"] != raw["check"]["metrics"]:
            raise AssertionError("Raw reference is not independently valid")
        if not score(raw_check["metrics"]) <= score(row["exact_best_metrics"]) <= score(report["final_metrics"]):
            raise AssertionError("Raw/offered/returned quality ordering violated")
        row.update(case=directory.name,step=step,raw_reference_status=raw["reference_status"],
                   raw_metrics=raw_check["metrics"],returned_metrics=report["final_metrics"],
                   same_portfolio_optimal=score(row["exact_best_metrics"])==score(report["final_metrics"]),
                   final_step_accepted=report["steps"][-1]["accepted"],
                   final_controls_match_returned=all(
                       control["best_metrics"] is not None and score(control["best_metrics"])==score(report["final_metrics"])
                       for control in report["steps"][-1]["controls"].values()))
        final.append(row)
    return dict(schema_version="catering-math-audit.v1",all_valid=True,
                cell=cell_result,independent_cell_selection_audit=independent,
                fixed_quantum_bundles=fixed,final_pilot_bundles=final,
                final_pilots_same_portfolio_optimal=sum(r["same_portfolio_optimal"] for r in final),
                final_control_ties=sum(r["final_controls_match_returned"] for r in final),
                physical_qpu_calls=0,veloxq_calls=0,quantum_training_runs=0,
                scope="Fresh exact classical verification of frozen small-domain evidence; no new optimization campaign")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,default=Path("."))
    parser.add_argument("--output",type=Path,required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Fresh audit output required")
    result = audit(args.root)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(dict(all_valid=True,bundles=1+len(result["fixed_quantum_bundles"])+len(result["final_pilot_bundles"]),
                          final_pilots_same_portfolio_optimal=result["final_pilots_same_portfolio_optimal"])))
