"""Exhaust all 512,000 operation-start combinations of the official 3x3 at H=8."""

import argparse
import itertools
import json
from pathlib import Path
import time

import numpy as np

from .artifacts import digest, write_json
from .stage1 import ROOT, build_qubo, to_dimod, operations


def audit_instance(instance, horizon):
    started = time.perf_counter()
    onehot, compact = [build_qubo(instance, horizon, encoding) for encoding in ("onehot", "domain-wall")]
    ops = operations(instance)
    groups = {(op["job"], op["machine"]): i for i, op in enumerate(ops)}
    domains = [[] for _ in ops]
    for v in onehot["variables"]:
        domains[groups[(v["job"], v["machine"])]].append(v["start"])
    count = 0
    feasible_count = 0
    models = [to_dimod(onehot), to_dimod(compact)]
    combinations = iter(itertools.product(*domains))
    while batch := list(itertools.islice(combinations, 8192)):
        starts = np.array(batch, dtype=np.int64)
        independent = np.zeros(len(batch), dtype=np.int64)
        for i, a in enumerate(ops):
            for j in range(i + 1, len(ops)):
                b = ops[j]
                if a["machine"] == b["machine"]:
                    independent += ((starts[:, i] < starts[:, j] + b["duration"]) &
                                    (starts[:, j] < starts[:, i] + a["duration"]))
                if a["job"] == b["job"] and a["order"] + 1 == b["order"]:
                    independent += starts[:, i] + a["duration"] > starts[:, j]
        for model, bqm in zip((onehot, compact), models):
            values = np.column_stack([
                (starts[:, groups[(v["job"], v["machine"])]] == v["start"] if model["encoding"] == "onehot" else
                 starts[:, groups[(v["job"], v["machine"])]] > v["after_start"])
                for v in model["variables"]]).astype(np.int8)
            energies = bqm.energies((values, list(range(len(model["variables"])))))
            if not np.array_equal(energies, independent):
                raise AssertionError("QUBO energy differs from direct interval-conflict count")
        count += len(batch)
        feasible_count += int((independent == 0).sum())
    return dict(horizon=horizon, checked_start_assignments=count, feasible_assignments=feasible_count,
                both_encoding_energies_match_independent_constraints=True,
                onehot_variables=len(onehot["variables"]), domain_wall_variables=len(compact["variables"]),
                onehot_sha256=digest(onehot), domain_wall_sha256=digest(compact),
                wall_seconds=time.perf_counter() - started,
                scope="All one-start-per-operation assignments in pruned domains, not every arbitrary bitstring")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "output/stage1/formulation-audit.json")
    args = parser.parse_args()
    instance = json.loads((ROOT / "instances/instance_3x3.json").read_text())
    report = audit_instance(instance, 8)
    write_json(args.output, report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
