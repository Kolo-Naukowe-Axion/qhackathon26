"""Causal sequential PPO and matched classical policy-search controls.

Factory transitions remain in engine.py; only documented public observations
enter the policy. Rollout workers use NumPy inference, not a CUDA allocation.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, asdict
import hashlib
import json
import math
import multiprocessing
from pathlib import Path
import random
import statistics
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TRAIN = tuple(range(32))
VALIDATION = tuple(range(100, 116))
TEST = tuple(range(1000, 1032))
WIPS = (1, 2, 3, 4, 6, 8)
ACTIONS = tuple(dict(id=f"w{wip}-{mode}-lease{lease}", weights=dict(wip_limit=wip,
    mode=mode, due=1., remaining=-4., family=0., setup=3., lease_calibration=bool(lease)))
    for wip in WIPS for mode in ("eco", "standard", "turbo") for lease in (0, 1)) + tuple(
    dict(id=f"w{wip}-{name}-standard-lease1", weights=dict(wip_limit=wip, mode="standard",
        due=due, remaining=remaining, family=family, setup=setup, lease_calibration=True))
    for wip in WIPS for name, due, remaining, family, setup in (
        ("long-tail", .5, -12., 0., 3.), ("family", .25, -4., 24., 10.)))
FEATURE_NAMES = (
    "time_fraction", "remaining_fraction", "day_sin", "day_cos", "orders_scale",
    "shipped_fraction", "completed_fraction", "active_fraction", "waiting_fraction",
    "accepted_fraction", "free_agv_fraction", "agv_soc_fraction", "free_worker_fraction",
    "free_tools_scale", "grid_cap_fraction", "battery_soc_fraction", "outage_fraction",
    "energy_cost_scale", "overdue_fraction", "shipped_delta", "completed_delta", "cost_delta",
    "queue_T", "queue_F", "queue_S", "queue_WASH", "queue_HEAT", "queue_QA",
    "queue_ASSEMBLY", "lease_previously_requested", "previous_wip_scale", "constant")


@dataclass(frozen=True)
class Config:
    orders: int = 8
    horizon: int = 5760
    profile: str = "full"


def fingerprints():
    files = ("stage2/engine.py", "stage2/spec.py", "stage2/check.py", "stage2/dispatch.py",
             "stage2/qubo.py", "stage2/quantum.py", "stage2/sequential.py",
             "instances/stage2/metaltech_pressure.json")
    return {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}


def check_sources(expected):
    actual = fingerprints()
    if actual != expected:
        changed = [p for p in actual if actual[p] != expected.get(p)]
        raise RuntimeError(f"Source changed during experiment; freeze and rerun: {changed}")


def features(obs, previous=None, memory=None):
    """32 bounded features, exclusively from observed state and own past action."""
    previous, memory = previous or obs, memory or {}
    orders = max(1, obs["observed_orders"])
    phase = 2*math.pi*obs["tick"]/max(1, obs["day_ticks"])
    t = obs["tick"]/max(1, obs["horizon_ticks"])
    values = [t, 1-t, math.sin(phase), math.cos(phase), orders/26,
        obs["shipped"]/orders, obs["completed_steps"]/(16*orders),
        obs["active_operations"]/15, obs["waiting_parts"]/(3*orders),
        obs["accepted_components"]/(3*orders), obs["agvs_free"]/max(1, obs["agvs_total"]),
        obs["agv_soc_mean"]/160, obs["workers_free"]/max(1, obs["workers_total"]),
        obs["tools_free"]/6, obs["grid_cap_kw"]/max(1, obs["normal_grid_cap_kw"]),
        obs["stationary_soc"]/max(1, obs["stationary_soc_capacity"]),
        obs["machine_outages"]/15, obs["energy_cost"]/1000, obs["overdue_orders"]/orders,
        (obs["shipped"]-previous["shipped"])/orders,
        (obs["completed_steps"]-previous["completed_steps"])/(16*orders),
        (obs["energy_cost"]-previous["energy_cost"])/1000]
    values += [obs.get(f"queue_{p}", 0)/(3*orders) for p in ("T", "F", "S", "WASH", "HEAT", "QA", "ASSEMBLY")]
    values += [float(memory.get("lease", False)), memory.get("wip", 3)/8, 1.]
    if len(values) != 32 or any(not math.isfinite(float(x)) for x in values):
        raise ValueError("Nonfinite or malformed public observation")
    return [max(-4., min(4., float(x))) for x in values]


def potential(obs):
    n = max(1, obs["observed_orders"])
    return .1*obs["shipped"]/n + .03*obs["completed_steps"]/(16*n)


def terminal_reward(metrics, valid, horizon):
    if not valid or not metrics.get("terminal_soc_satisfied", False):
        return -1000.
    missing = metrics["orders"]-metrics["shipped"]
    tardy = min(1., metrics["total_tardiness_ticks"]/max(1, metrics["orders"]*horizon))
    cost = max(0., metrics["total_cost"])
    return -missing-.2*tardy-.01*cost/(1000+cost)


def trajectory_rewards(potentials, terminal):
    """Telescoping shaping with terminal compensation: sum rewards == terminal."""
    if not potentials:
        return []
    rewards = [b-a for a, b in zip(potentials, potentials[1:])]
    rewards.append(terminal + potentials[0]-potentials[-1])
    return rewards


def make_network(torch):
    class ActorCritic(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.first = torch.nn.Linear(32, 64)
            self.second = torch.nn.Linear(64, 64)
            self.actor = torch.nn.Linear(64, len(ACTIONS))
            self.critic = torch.nn.Linear(64, 1)

        def forward(self, x):
            h = torch.tanh(self.second(torch.tanh(self.first(x))))
            return self.actor(h), self.critic(h).squeeze(-1)
    return ActorCritic()


def export_network(network):
    return {key: value.detach().cpu().tolist() for key, value in network.state_dict().items()}


class Controller:
    """An ordinary engine callback; action sampling uses its own RNG only."""
    def __init__(self, policy, policy_seed=0, deterministic=False, base_weights=None):
        import numpy as np
        self.np = np
        self.policy = policy
        self.rng = random.Random(policy_seed)
        self.deterministic = deterministic
        self.base_weights = dict(base_weights or {})
        self.base_weights.setdefault("policy_seed", 0)
        self.trajectory = []
        self.previous = None
        self.memory = {}
        self.cached_action = None
        self.parameters = {key: np.asarray(value, dtype=np.float32)
                           for key, value in policy.get("network", {}).items()}

    def infer(self, x):
        np, p = self.np, self.parameters
        h = np.tanh(p["first.weight"]@np.asarray(x, dtype=np.float32)+p["first.bias"])
        h = np.tanh(p["second.weight"]@h+p["second.bias"])
        logits = p["actor.weight"]@h+p["actor.bias"]
        probabilities = np.exp(logits-logits.max())
        probabilities /= probabilities.sum()
        value = float((p["critic.weight"]@h+p["critic.bias"])[0])
        return probabilities.tolist(), value

    def __call__(self, obs):
        x = features(obs, self.previous, self.memory)
        kind = self.policy["kind"]
        value, log_probability = 0., 0.
        if kind in ("ppo", "bandit"):
            probabilities, value = self.infer(x)
            if kind == "bandit" and self.cached_action is not None:
                action = self.cached_action
            else:
                action = (max(range(len(ACTIONS)), key=probabilities.__getitem__) if self.deterministic
                          else self.rng.choices(range(len(ACTIONS)), weights=probabilities)[0])
                self.cached_action = action
            log_probability = math.log(max(probabilities[action], 1e-30))
        elif kind == "random":
            action = self.rng.randrange(len(ACTIONS))
            log_probability = -math.log(len(ACTIONS))
        elif kind == "schedule":
            sequence = self.policy["schedule"]
            segment = min(len(sequence)-1, int(obs["tick"]/max(1, obs["horizon_ticks"])*len(sequence)))
            action = sequence[segment]
        elif kind == "static":
            action = self.policy["action"]
        else:
            raise ValueError(f"Unknown policy kind {kind}")
        # Bandit stores one choice; its repeated callbacks are not fictitious decisions.
        if kind != "bandit" or not self.trajectory:
            self.trajectory.append(dict(features=x, action=int(action), old_logp=log_probability,
                value=value, potential=potential(obs), tick=obs["tick"]))
        weights = dict(self.base_weights, **ACTIONS[action]["weights"])
        self.previous = dict(obs)
        self.memory.update(lease=self.memory.get("lease", False) or weights["lease_calibration"],
                           wip=weights["wip_limit"])
        return dict(weights=weights, action_id=ACTIONS[action]["id"])


def rollout(task):
    from .spec import build
    from .engine import run
    from .check import check_trace
    started = time.perf_counter()
    controller = Controller(task["policy"], task["policy_seed"], task.get("deterministic", False),
                            task.get("base_weights"))
    trace = run(build(**task["config"], seed=task["seed"]), controller=controller)
    checked = check_trace(trace)
    reward = terminal_reward(trace["metrics"], checked["valid"], task["config"]["horizon"])
    trajectory = controller.trajectory
    shaped = trajectory_rewards([step["potential"] for step in trajectory], reward)
    for step, r in zip(trajectory, shaped):
        step["reward"] = r
    result = dict(config=task["config"], seed=task["seed"], policy_seed=task["policy_seed"],
        reward=reward, valid=checked["valid"], issues=checked["issues"][:10], metrics=trace["metrics"],
        trajectory=trajectory, wall_seconds=time.perf_counter()-started,
        decisions=len(controller.trajectory), action_changes=sum(a["action"] != b["action"]
            for a, b in zip(trajectory, trajectory[1:])))
    if task.get("trace_path"):
        path = Path(task["trace_path"]); path.parent.mkdir(parents=True, exist_ok=True)
        trace["validation"] = checked
        path.write_text(json.dumps(trace)+"\n")
    return result


def update_ppo(torch, network, optimizer, episodes, epochs=4, minibatch=512):
    xs, actions, oldlogps, returns, advantages = [], [], [], [], []
    for episode in episodes:
        cumulative = 0.
        local_returns = []
        for step in reversed(episode["trajectory"]):
            cumulative += step["reward"]
            local_returns.append(cumulative)
        for step, target in zip(episode["trajectory"], reversed(local_returns)):
            xs.append(step["features"]); actions.append(step["action"])
            oldlogps.append(step["old_logp"]); returns.append(target)
            advantages.append(target-step["value"])
    x = torch.tensor(xs, dtype=torch.float32)
    action = torch.tensor(actions, dtype=torch.long)
    oldlogp = torch.tensor(oldlogps, dtype=torch.float32)
    target = torch.tensor(returns, dtype=torch.float32)
    advantage = torch.tensor(advantages, dtype=torch.float32)
    advantage = (advantage-advantage.mean())/advantage.std(unbiased=False).clamp_min(1e-6)
    losses, entropies, clipfractions = [], [], []
    for _ in range(epochs):
        permutation = torch.randperm(len(xs))
        for indices in permutation.split(minibatch):
            logits, values = network(x[indices])
            distribution = torch.distributions.Categorical(logits=logits)
            logp = distribution.log_prob(action[indices])
            ratio = (logp-oldlogp[indices]).exp()
            actor = -torch.minimum(ratio*advantage[indices],
                                   ratio.clamp(.8, 1.2)*advantage[indices]).mean()
            critic = torch.nn.functional.smooth_l1_loss(values, target[indices])
            entropy = distribution.entropy().mean()
            loss = actor+.5*critic-.025*entropy
            optimizer.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(network.parameters(), .5)
            optimizer.step()
            losses.append(float(loss.detach())); entropies.append(float(entropy.detach()))
            clipfractions.append(float(((ratio.detach()-1).abs()>.2).float().mean()))
    return dict(transitions=len(xs), loss=statistics.mean(losses), entropy=statistics.mean(entropies),
                clip_fraction=statistics.mean(clipfractions))


def summary(rows):
    if not rows:
        return {}
    tardy = sorted((r["metrics"]["total_tardiness_ticks"] for r in rows), reverse=True)
    return dict(episodes=len(rows), valid=sum(r["valid"] for r in rows),
        complete=sum(r["valid"] and r["metrics"]["all_orders_fulfilled"] for r in rows),
        mean_unfulfilled=statistics.mean(r["metrics"]["orders"]-r["metrics"]["shipped"] for r in rows),
        mean_reward=statistics.mean(r["reward"] for r in rows),
        mean_tardiness_ticks=statistics.mean(tardy),
        empirical_worst_decile_mean_tardiness=statistics.mean(tardy[:max(1, math.ceil(.1*len(tardy)))]),
        mean_total_cost=statistics.mean(r["metrics"]["total_cost"] for r in rows),
        simulation_cpu_seconds=sum(r["wall_seconds"] for r in rows),
        mean_action_changes=statistics.mean(r["action_changes"] for r in rows),
        global_optimality_gap=None)


def _compact(row):
    return {key: value for key, value in row.items() if key != "trajectory"}


def _write_checkpoint(path, artifact):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(artifact, indent=2)+"\n")
    temporary.replace(path)


def train(method="ppo", configs=None, seconds=300, workers=4, batch_episodes=32,
          seed=2026, max_episodes=None, base_weights=None, output=None, segments=8):
    configs = configs or [Config()]
    if method not in ("ppo", "bandit", "random", "cem", "static"):
        raise ValueError("Unsupported method")
    if seconds <= 0 or workers < 1 or batch_episodes < 1:
        raise ValueError("Positive time, workers and batch size required")
    started, rng, hashes = time.perf_counter(), random.Random(seed), fingerprints()
    base_weights = dict(base_weights or {}, policy_seed=0)
    counts = [[0]*len(ACTIONS) for _ in configs]
    totals = [[0.]*len(ACTIONS) for _ in configs]
    observations, curves, network, optimizer, torch = [], [], None, None, None
    probabilities = [[[1/len(ACTIONS)]*len(ACTIONS) for _ in range(segments)] for _ in configs]
    best_schedules, best_rewards = [[12]*segments for _ in configs], [-math.inf]*len(configs)
    grid = []
    for scenario in TRAIN:
        block = [(k, action, scenario) for k in range(len(configs)) for action in range(len(ACTIONS))]
        rng.shuffle(block); grid.extend(block)
    if method in ("ppo", "bandit"):
        import torch
        torch.set_num_threads(1); torch.manual_seed(seed)
        network = make_network(torch)
        optimizer = torch.optim.Adam(network.parameters(), lr=.0008)
    executor = (ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("spawn"))
                if workers > 1 else None)
    if output:
        output = Path(output); output.mkdir(parents=True, exist_ok=True)
        if (output/"episodes.jsonl").exists():
            raise ValueError("Choose a fresh output directory to preserve existing training episodes")
    try:
        while time.perf_counter()-started < seconds:
            check_sources(hashes)
            size = batch_episodes if max_episodes is None else min(batch_episodes, max_episodes-len(observations))
            if method == "static": size = min(size, len(grid)-len(observations))
            if size <= 0: break
            network_state = export_network(network) if network is not None else None
            tasks, metadata = [], []
            common_context, common_scenario = rng.randrange(len(configs)), rng.choice(TRAIN)
            for j in range(size):
                if method == "static":
                    context, action, scenario = grid[len(observations)+j]
                    policy = dict(kind="static", action=action)
                else:
                    context, scenario = ((common_context, common_scenario) if method == "cem"
                                         else (rng.randrange(len(configs)), rng.choice(TRAIN)))
                    if method in ("ppo", "bandit"):
                        policy = dict(kind=method, network=network_state)
                    elif method == "random": policy = dict(kind="random")
                    else:
                        sequence = [rng.choices(range(len(ACTIONS)), weights=p)[0] for p in probabilities[context]]
                        policy = dict(kind="schedule", schedule=sequence)
                tasks.append(dict(config=asdict(configs[context]), seed=scenario,
                    policy_seed=seed+len(observations)+j, policy=policy, base_weights=base_weights))
                metadata.append((context, policy))
            rows = list(executor.map(rollout, tasks)) if executor else [rollout(task) for task in tasks]
            check_sources(hashes)
            if method in ("ppo", "bandit"):
                diagnostic = update_ppo(torch, network, optimizer, rows)
            else: diagnostic = {}
            for (context, policy), row in zip(metadata, rows):
                row.update(training_context=context)
                if method == "static":
                    action = policy["action"]
                    counts[context][action] += 1; totals[context][action] += row["reward"]
                if method == "cem" and row["reward"] > best_rewards[context]:
                    best_rewards[context], best_schedules[context] = row["reward"], policy["schedule"]
                if output:
                    with (output/"episodes.jsonl").open("a") as stream:
                        stream.write(json.dumps(_compact(row))+"\n")
            observations.extend(rows)
            if method == "cem":
                elite_indices = sorted(range(len(rows)), key=lambda j: rows[j]["reward"], reverse=True)[:max(1, size//4)]
                for segment in range(segments):
                    target = [.05/len(ACTIONS)]*len(ACTIONS)
                    for j in elite_indices: target[metadata[j][1]["schedule"][segment]] += .95/len(elite_indices)
                    probabilities[common_context][segment] = [.75*a+.25*b for a, b in zip(probabilities[common_context][segment], target)]
            curve = dict(episodes=len(observations), elapsed_seconds=time.perf_counter()-started,
                         batch_summary=summary(rows), **diagnostic)
            curves.append(curve)
            print(json.dumps(dict(method=method, progress=curve)), flush=True)
            if method in ("ppo", "bandit"): final_policy = dict(kind=method, network=export_network(network))
            elif method == "static":
                chosen = [max((a for a in range(len(ACTIONS)) if counts[k][a]),
                              key=lambda a: totals[k][a]/counts[k][a], default=12) for k in range(len(configs))]
                final_policy = dict(kind="context_static", actions=chosen)
            elif method == "cem": final_policy = dict(kind="context_schedule", schedules=best_schedules)
            else: final_policy = dict(kind="random")
            artifact = dict(schema="metaltech-sequential-policy.v1", method=method, policy=final_policy,
                configs=[asdict(c) for c in configs], actions=list(ACTIONS), feature_names=list(FEATURE_NAMES),
                source_hashes=hashes, seed=seed, train_seeds=list(TRAIN), validation_seeds=list(VALIDATION),
                test_seeds=list(TEST), base_weights=base_weights, fit_episodes=len(observations),
                requested_wall_seconds=seconds, actual_wall_seconds=time.perf_counter()-started,
                workers=workers, batch_episodes=batch_episodes, curves=curves,
                reward="unfulfilled_primary_bounded_tardiness_total_cost; gamma1_telescoping_shaping_compensated",
                hardware="CPU; numpy rollout inference; torch training one CPU thread")
            if output: _write_checkpoint(output/"checkpoint.json", artifact)
            if max_episodes is not None and len(observations) >= max_episodes: break
    finally:
        if executor: executor.shutdown()
    if not observations: raise RuntimeError("No rollout completed within the training budget")
    return artifact


def evaluation_tasks(artifact, configs, seeds, policy_seed=900000):
    check_sources(artifact["source_hashes"])
    tasks = []
    for config in configs:
        policy = artifact["policy"]
        if policy["kind"] in ("context_static", "context_schedule"):
            if asdict(config) not in artifact["configs"]:
                raise ValueError("Static context baseline requires an explicitly measured training context")
            index = artifact["configs"].index(asdict(config))
            policy = (dict(kind="static", action=policy["actions"][index]) if policy["kind"] == "context_static"
                      else dict(kind="schedule", schedule=policy["schedules"][index]))
        for scenario in seeds:
            tasks.append(dict(config=asdict(config), seed=scenario, policy_seed=policy_seed,
                deterministic=True, policy=policy, base_weights=artifact["base_weights"]))
    return tasks


def evaluate(artifact, configs, seeds=TEST, workers=4, policy_seed=900000):
    tasks = evaluation_tasks(artifact, configs, seeds, policy_seed)
    started = time.perf_counter()
    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("spawn")) as executor:
            rows = list(executor.map(rollout, tasks))
    else: rows = [rollout(task) for task in tasks]
    check_sources(artifact["source_hashes"])
    return dict(schema="metaltech-sequential-evaluation.v1", method=artifact["method"],
        seeds=list(seeds), policy_seed=policy_seed, deterministic_network_argmax=True,
        configs=[asdict(c) for c in configs], summary=summary(rows), rows=[_compact(row) for row in rows],
        wall_seconds=time.perf_counter()-started)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--method", choices=("ppo", "bandit", "random", "cem", "static"), default="ppo")
    p.add_argument("--orders", default="8")
    p.add_argument("--horizon", type=int, default=5760)
    p.add_argument("--seconds", type=float, default=300)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--batch-episodes", type=int, default=32)
    p.add_argument("--max-episodes", type=int)
    p.add_argument("--seed", type=int, default=2026)
    p.add_argument("--selector", default="priority")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--checkpoint", type=Path, help="Evaluate an existing checkpoint instead of training")
    p.add_argument("--test-seed-start", type=int, default=1000)
    p.add_argument("--test-seed-count", type=int, default=32)
    p.add_argument("--skip-evaluation", action="store_true")
    a = p.parse_args()
    configs = [Config(int(n), a.horizon) for n in a.orders.split(",")]
    if a.checkpoint: artifact = json.loads(a.checkpoint.read_text())
    else:
        artifact = train(a.method, configs, a.seconds, a.workers, a.batch_episodes,
            a.seed, a.max_episodes, dict(selector=a.selector), a.output)
    if not a.skip_evaluation:
        validation = evaluate(artifact, configs, VALIDATION, a.workers)
        report = evaluate(artifact, configs, tuple(range(a.test_seed_start, a.test_seed_start+a.test_seed_count)), a.workers)
        a.output.mkdir(parents=True, exist_ok=True)
        (a.output/"validation.json").write_text(json.dumps(validation, indent=2)+"\n")
        (a.output/"test.json").write_text(json.dumps(report, indent=2)+"\n")
        print(json.dumps(dict(method=artifact["method"], validation=validation["summary"], test=report["summary"])), flush=True)


if __name__ == "__main__":
    main()
