"""Task-specific one-step RL for choosing an interpretable dispatch policy.

This is a contextual bandit, not a pretrained model or sequential factory agent.
The physical simulator and checker define rewards; no future random tape is an
input feature. All methods use the same 16 actions and disjoint seed splits.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TRAIN_SEEDS = tuple(range(32))
VALIDATION_SEEDS = tuple(range(100, 116))
TEST_SEEDS = tuple(range(1000, 1032))

# Actions alter production order, setup preference and certified machine mode.
# Their IDs and values are saved in every artifact, making policies inspectable.
ACTIONS = tuple(
    dict(id=f"{rule}-w{wip}-{mode}-lease{lease}", weights=dict(due=1.,remaining=remaining,
        family=0.,noise=0.,setup=3.,mode=mode,wip_limit=wip,lease_calibration=bool(lease)))
    for rule,remaining in (("due",-4.),("critical-tail",-16.))
    for wip in (2,3,4,6) for mode in ("eco","standard","turbo") for lease in (0,1))


@dataclass(frozen=True)
class Config:
    orders: int = 24
    horizon: int = 5760
    profile: str = "full"


def source_hashes() -> dict[str, str]:
    files = ("stage2/engine.py", "stage2/spec.py", "stage2/check.py",
             "stage2/learning.py", "instances/stage2/metaltech_pressure.json")
    return {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in files}


def context_features(config: Config) -> list[float]:
    """Observable workload context; intentionally excludes instance/random seed."""
    from .spec import build
    instance = build(**asdict(config), seed=0)
    orders = instance["orders"]
    machines = instance["machines"]
    horizon = config.horizon
    mean_due = statistics.mean(o["due_tick"] for o in orders) if orders else horizon
    return [config.orders/24., horizon/5760., config.orders*16*60/max(1,15*horizon),
            len(machines)/15., mean_due/max(1, horizon),
            sum(o.get("precision_required", False) for o in orders)/max(1, len(orders)),
            instance["energy"]["normal_grid_cap_kw"]/90., 1.]


def score(metrics: dict[str, Any], valid: bool, issues: int = 0) -> float:
    """A scalar training surrogate with strict order-count priority at fixed context.

    The full report retains the original metrics. This does not claim to optimize
    CVaR or the lexicographic problem globally. An invalid trace is always worse
    than any physically valid dispatch run on the supported context sizes.
    """
    if not valid:
        return -10000. - min(1000, issues)
    orders = metrics["orders"]
    unfulfilled = orders-metrics["shipped"]
    horizon = metrics.get("horizon_ticks", 384)
    tardiness = min(1., metrics["total_tardiness_ticks"]/max(1, orders*horizon))
    cost = metrics.get("total_cost",metrics.get("energy_cost", 0.))
    bounded_cost = max(0., cost)/(1.+max(0., cost))
    terminal = 0 if metrics.get("terminal_soc_satisfied", False) else 1
    return -float(unfulfilled) - .1*tardiness - .001*bounded_cost - 1000.*terminal


def simulate(task: tuple[dict[str, Any], int, int]) -> dict[str, Any]:
    """Top-level picklable worker; save compact measurements, never hidden state."""
    from .engine import run
    from .check import check_trace
    from .spec import build
    config_dict, action, seed = task
    started = time.perf_counter()
    trace = run(build(**config_dict, seed=seed), dict(ACTIONS[action]["weights"]))
    checked = check_trace(trace)
    metrics = dict(trace["metrics"], horizon_ticks=config_dict["horizon"])
    return dict(config=config_dict, action=action, action_id=ACTIONS[action]["id"],
                seed=seed, reward=score(metrics, checked["valid"], len(checked["issues"])),
                metrics=metrics, valid=checked["valid"], issue_count=len(checked["issues"]),
                issue_codes=sorted({i["code"] for i in checked["issues"]}),
                elapsed_seconds=time.perf_counter()-started)


def _simulate_many(tasks, workers):
    if workers is None:
        return [simulate(task) for task in tasks]
    return list(workers.map(simulate, tasks))


def make_network(torch):
    # Factory prevents importing PyTorch in simulator worker processes.
    class Policy(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.body = torch.nn.Sequential(torch.nn.Linear(8, 64), torch.nn.Tanh(),
                                             torch.nn.Linear(64, 64), torch.nn.Tanh())
            self.actor = torch.nn.Linear(64, len(ACTIONS))
            self.value = torch.nn.Linear(64, 1)

        def forward(self, x):
            h = self.body(x)
            return self.actor(h), self.value(h).squeeze(-1)
    return Policy()


def _assert_sources(hashes):
    current = source_hashes()
    if current != hashes:
        changed = [name for name in hashes if current.get(name) != hashes[name]]
        raise RuntimeError(f"Source changed during experiment; rerun from a fixed snapshot: {changed}")


def fit(method: str, configs: list[Config], seconds: float = 60, seed: int = 0,
        batch_size: int = 8, worker_count: int = 1,
        max_episodes: int | None = None) -> dict[str, Any]:
    """Equal per-method wall budget includes initialization and simulator/checker.

    A final batch may overrun the deadline; actual time/episodes are recorded.
    CPU simulation dominates this small policy. No GPU allocation is requested.
    """
    if method not in ("reinforce", "random", "cem", "grid"):
        raise ValueError("method must be reinforce, random, cem or grid")
    if seconds <= 0 or batch_size < 1 or worker_count < 1 or not configs:
        raise ValueError("Positive budget, batch size, workers and contexts required")
    if max_episodes is not None and max_episodes < 1:
        raise ValueError("max_episodes must be positive")
    started = time.perf_counter()
    hashes = source_hashes()
    rng = random.Random(seed)
    observations, updates = [], []
    counts = [[0 for _ in ACTIONS] for _ in configs]
    totals = [[0. for _ in ACTIONS] for _ in configs]
    probabilities = [[1./len(ACTIONS) for _ in ACTIONS] for _ in configs]
    grid_tasks = []
    if method == "grid":
        # Broad action coverage first, then replicate across training tapes.
        for scenario_seed in TRAIN_SEEDS:
            block = [(k, action, scenario_seed) for k in range(len(configs)) for action in range(len(ACTIONS))]
            rng.shuffle(block)
            grid_tasks.extend(block)
    torch = network = optimizer = None
    features = [context_features(c) for c in configs]
    if method == "reinforce":
        import torch
        torch.set_num_threads(1)
        torch.manual_seed(seed)
        network = make_network(torch)
        optimizer = torch.optim.Adam(network.parameters(), lr=.003)
    workers = ProcessPoolExecutor(max_workers=worker_count) if worker_count > 1 else None
    try:
        while time.perf_counter()-started < seconds:
            _assert_sources(hashes)
            size = batch_size if max_episodes is None else min(batch_size, max_episodes-len(observations))
            if size <= 0:
                break
            if method == "grid":
                block = grid_tasks[len(observations):len(observations)+size]
                if not block:
                    break
                contexts, chosen, seeds = map(list, zip(*block))
            else:
                contexts = [rng.randrange(len(configs)) for _ in range(size)]
                seeds = [rng.choice(TRAIN_SEEDS) for _ in range(size)]
            if method == "reinforce":
                x = torch.tensor([features[k] for k in contexts], dtype=torch.float32)
                logits, values = network(x)
                distribution = torch.distributions.Categorical(logits=logits)
                chosen_tensor = distribution.sample()
                chosen = chosen_tensor.tolist()
            elif method == "random":
                chosen = [rng.randrange(len(ACTIONS)) for _ in contexts]
            elif method == "cem":
                chosen = [rng.choices(range(len(ACTIONS)), weights=probabilities[k])[0] for k in contexts]
            tasks = [(asdict(configs[k]), action, s) for k, action, s in zip(contexts, chosen, seeds)]
            results = _simulate_many(tasks, workers)
            _assert_sources(hashes)
            observations.extend(results)
            for k, action, result in zip(contexts, chosen, results):
                counts[k][action] += 1
                totals[k][action] += result["reward"]
            if method == "reinforce":
                rewards = torch.tensor([r["reward"] for r in results], dtype=torch.float32)
                advantage = rewards-values.detach()
                advantage = (advantage-advantage.mean())/advantage.std(unbiased=False).clamp_min(.1)
                actor_loss = -(distribution.log_prob(chosen_tensor)*advantage).mean()
                value_loss = torch.nn.functional.smooth_l1_loss(values, rewards)
                entropy = distribution.entropy().mean()
                loss = actor_loss+.5*value_loss-.03*entropy
                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(network.parameters(), 1.)
                optimizer.step()
                updates.append(dict(episodes=len(observations), loss=float(loss.detach()),
                    entropy=float(entropy.detach()), mean_reward=float(rewards.mean())))
            elif method == "cem":
                # Context-specific categorical CEM; nonzero exploration floor.
                for k in set(contexts):
                    group = [(r["reward"], a) for context, a, r in zip(contexts, chosen, results) if context == k]
                    group.sort(reverse=True)
                    elite = group[:max(1, math.ceil(len(group)/4))]
                    target = [.02/len(ACTIONS) for _ in ACTIONS]
                    for _, action in elite:
                        target[action] += .98/len(elite)
                    probabilities[k] = [.7*old+.3*new for old, new in zip(probabilities[k], target)]
            if max_episodes is not None and len(observations) >= max_episodes:
                break
    finally:
        if workers is not None:
            workers.shutdown()
    if not observations:
        raise RuntimeError("Budget expired before collecting any simulator episode")
    state = None
    if method == "reinforce":
        with torch.no_grad():
            logits, _ = network(torch.tensor(features, dtype=torch.float32))
            selected = logits.argmax(dim=1).tolist()
        state = {k: v.detach().cpu() for k, v in network.state_dict().items()}
    else:
        # All methods report an incumbent based on measured training reward.
        # Random search gets a separate best action in each context, not a weak
        # random action at evaluation time. Untried actions cannot be selected.
        selected = [max((a for a in range(len(ACTIONS)) if counts[k][a]),
                        key=lambda a: totals[k][a]/counts[k][a], default=0) for k in range(len(configs))]
    return dict(schema="metaltech-learned-dispatch.v1", method=method,
        algorithm="one_step_REINFORCE_contextual_bandit" if method == "reinforce" else method,
        seed=seed, configs=[asdict(c) for c in configs], actions=list(ACTIONS),
        features=features, selected_actions=selected, source_hashes=hashes,
        train_seeds=list(TRAIN_SEEDS), validation_seeds=list(VALIDATION_SEEDS), test_seeds=list(TEST_SEEDS),
        fit_wall_seconds=time.perf_counter()-started, requested_fit_seconds=seconds,
        fit_episodes=len(observations), batch_size=batch_size, worker_count=worker_count,
        hardware="CPU; no GPU requested", checkpoint_state=state,
        observations=observations, updates=updates, counts=counts, totals=totals,
        cem_probabilities=probabilities if method == "cem" else None)


def choose_action(model: dict[str, Any], config: Config) -> int:
    key = asdict(config)
    if key in model["configs"]:
        return model["selected_actions"][model["configs"].index(key)]
    if model["method"] == "reinforce":
        import torch
        network = make_network(torch)
        network.load_state_dict(model["checkpoint_state"])
        with torch.no_grad():
            logits, _ = network(torch.tensor([context_features(config)], dtype=torch.float32))
            return int(logits.argmax(dim=1)[0])
    # Unseen-context baseline uses nearest observable workload context.
    feature = context_features(config)
    nearest = min(range(len(model["features"])),
                  key=lambda k: sum((a-b)**2 for a, b in zip(feature, model["features"][k])))
    return model["selected_actions"][nearest]


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {}
    tardiness = sorted((r["metrics"]["total_tardiness_ticks"] for r in rows), reverse=True)
    tail = max(1, math.ceil(len(tardiness)*.1))
    return dict(episodes=len(rows), valid_episodes=sum(r["valid"] for r in rows),
        all_fulfilled_episodes=sum(r["valid"] and r["metrics"]["all_orders_fulfilled"] for r in rows),
        mean_reward=statistics.mean(r["reward"] for r in rows),
        mean_unfulfilled_orders=statistics.mean(r["metrics"]["orders"]-r["metrics"]["shipped"] for r in rows),
        mean_total_tardiness_ticks=statistics.mean(tardiness),
        empirical_worst_decile_mean_tardiness=statistics.mean(tardiness[:tail]),
        mean_energy_cost=statistics.mean(r["metrics"]["energy_cost"] for r in rows),
        mean_carbon_kg=statistics.mean(r["metrics"]["carbon_kg"] for r in rows),
        global_optimality_gap=None)


def evaluate(model, configs: list[Config], split="test", worker_count=1):
    seeds = {"train": TRAIN_SEEDS, "validation": VALIDATION_SEEDS, "test": TEST_SEEDS}[split]
    _assert_sources(model["source_hashes"])
    tasks = [(asdict(c), choose_action(model, c), seed) for c in configs for seed in seeds]
    workers = ProcessPoolExecutor(max_workers=worker_count) if worker_count > 1 else None
    started = time.perf_counter()
    try:
        rows = _simulate_many(tasks, workers)
    finally:
        if workers is not None:
            workers.shutdown()
    _assert_sources(model["source_hashes"])
    return dict(split=split, seeds=list(seeds), configs=[asdict(c) for c in configs],
                elapsed_seconds=time.perf_counter()-started, summary=summarize(rows), rows=rows)


def save_model(model: dict[str, Any], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if model["checkpoint_state"] is not None:
        import torch
        torch.save(model, path.with_suffix(".pt"))
    serializable = {k: v for k, v in model.items() if k != "checkpoint_state"}
    serializable["checkpoint_file"] = str(path.with_suffix(".pt").name) if model["checkpoint_state"] is not None else None
    path.with_suffix(".json").write_text(json.dumps(serializable, indent=2)+"\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method", choices=("reinforce", "random", "cem", "grid", "all"), default="all")
    parser.add_argument("--orders", type=int, default=24)
    parser.add_argument("--horizon", type=int, default=5760)
    parser.add_argument("--configs", type=Path, help="JSON array of {orders,horizon,profile} contexts")
    parser.add_argument("--seconds", type=float, default=60, help="Equal fit budget per method")
    parser.add_argument("--max-episodes", type=int)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--output", type=Path, default=ROOT/"output/stage2-search/learning")
    parser.add_argument("--profile-only", action="store_true", help="Time one checked episode without training")
    args = parser.parse_args()
    configs = ([Config(**d) for d in json.loads(args.configs.read_text())] if args.configs
               else [Config(args.orders, args.horizon)])
    if args.profile_only:
        print(json.dumps(simulate((asdict(configs[0]), 0, TRAIN_SEEDS[0])), indent=2))
        return
    methods = ("reinforce", "random", "cem", "grid") if args.method == "all" else (args.method,)
    reports = []
    for method in methods:
        model = fit(method, configs, args.seconds, args.seed, args.batch_size, args.workers, args.max_episodes)
        save_model(model, args.output/method)
        # Validation is reported separately, never used to choose a test seed.
        report = dict(method=method, fit_wall_seconds=model["fit_wall_seconds"],
            fit_episodes=model["fit_episodes"], selected_actions=model["selected_actions"],
            validation=evaluate(model, configs, "validation", args.workers),
            test=evaluate(model, configs, "test", args.workers))
        (args.output/f"{method}-evaluation.json").write_text(json.dumps(report, indent=2)+"\n")
        reports.append(report)
        print(json.dumps({k: v for k, v in report.items() if k not in ("validation", "test")}, indent=2))
        print(json.dumps(dict(method=method, held_out_test=report["test"]["summary"]), indent=2))
    (args.output/"comparison.json").write_text(json.dumps(reports, indent=2)+"\n")


if __name__ == "__main__":
    main()
