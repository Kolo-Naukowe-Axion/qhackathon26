"""Low-conflict program pools for the VeloxQ scale workload (offline study).

The frozen scale tiers (output/catering-velox-scale-v3/) are dense: about 28-30%
of variable pairs are couplers, mostly cross-block conflicts on shared cookers,
prep stations and workers. This builds pools of the same widths from the same
full local domain, choosing programs that add the fewest conflicts.

Selection: one seed program per anchor (as the frozen generator), then
round-robin over anchor blocks; each block adds the candidate with the fewest
conflicts with already selected programs of other blocks. Ties prefer more
allocations, less surplus, then id. No reference, optimum or solver output is
used. Bundles are compiled by the unchanged catering.meal_blocks compiler
(same objective weights and global penalty rule), so only the pool differs.
"""
import argparse
import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

from ..build_meal_release import save
from ..contracts import load_bundle
from ..decode import decode
from ..domain import digest
from ..meal_blocks import compile_meal_blocks
from ..meal_reference import solve_bundle
from ..options import claims, enumerate_options

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/"output/catering-velox-scale-v3"


class ConflictIndex:
    """Per-resource interval arrays; conflict(p, q) as in catering.options plus shared allocations."""

    def __init__(self, instance, programs):
        self.n = len(programs)
        self.block = [min(p["allocation_order"]) for p in programs]
        self.claims = [claims(instance, p) for p in programs]
        rows = defaultdict(lambda: ([], [], []))
        for k, cl in enumerate(self.claims):
            for r, a, b in cl:
                rows[r][0].append(a); rows[r][1].append(b); rows[r][2].append(k)
        self.resources = {r: tuple(np.array(v) for v in arrays) for r, arrays in rows.items()}
        groups = defaultdict(list)
        for k, p in enumerate(programs):
            for g in p["allocation_order"]:
                groups[g].append(k)
        self.groups = {g: np.array(v) for g, v in groups.items()}
        self.allocations = [p["allocation_order"] for p in programs]
        block_ids = {b: i for i, b in enumerate(sorted(set(self.block)))}
        self.block_index = np.array([block_ids[b] for b in self.block])

    def conflicts_of(self, k):
        mask = np.zeros(self.n, dtype=bool)
        for r, a, b in self.claims[k]:
            starts, ends, owners = self.resources[r]
            mask[owners[(starts < b) & (a < ends)]] = True
        for g in self.allocations[k]:
            mask[self.groups[g]] = True
        mask[self.block_index == self.block_index[k]] = False  # same block: one-hot, not a conflict
        return mask


def select_pool(instance, programs, width):
    anchors = {}
    for k, p in enumerate(programs):
        anchors.setdefault(min(p["allocation_order"]), k)
    target = width - len(anchors)
    index = ConflictIndex(instance, programs)
    selected = np.zeros(len(programs), dtype=bool)
    added = np.zeros(len(programs), dtype=np.int64)
    for k in anchors.values():
        selected[k] = True
        added += index.conflicts_of(k)
    tie = sorted(range(len(programs)), key=lambda k: (-len(programs[k]["allocation_order"]),
                 programs[k]["yield_lots"] - len(programs[k]["allocation_order"]), programs[k]["id"]))
    rank = np.empty(len(programs), dtype=np.int64)
    rank[tie] = np.arange(len(programs))
    blocks = sorted(anchors)
    members = {b: np.array([k for k in range(len(programs)) if index.block[k] == b]) for b in blocks}
    while selected.sum() < target:
        progressed = False
        for b in blocks:
            if selected.sum() >= target:
                break
            pool = members[b][~selected[members[b]]]
            if not len(pool):
                continue
            k = int(pool[np.lexsort((rank[pool], added[pool]))[0]])
            selected[k] = True
            added += index.conflicts_of(k)
            progressed = True
        if not progressed:
            raise ValueError("Domain exhausted before the requested width")
    return sorted((programs[k] for k in np.flatnonzero(selected)), key=lambda p: p["id"])


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", required=True, help="New directory")
    parser.add_argument("--widths", type=int, nargs="+", default=[512, 1024])
    parser.add_argument("--reference-seconds", type=float, default=30)
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    instance = json.loads((SOURCE/"instance.json").read_text())
    state = json.loads((SOURCE/"snapshot.json").read_text())
    report = json.loads((SOURCE/"report.json").read_text())
    programs = enumerate_options(instance, state)
    parent = digest([p["id"] for p in programs])
    if parent != report["full_local_domain_sha256"]:
        raise ValueError("Full local domain differs from the frozen scale release")
    save(output/"plan.json", dict(source=str(SOURCE.relative_to(ROOT)), widths=args.widths,
                                  selection=__doc__.split("Selection: ")[1].split("\n\n")[0].replace("\n", " "),
                                  reference=dict(solver="catering.meal_reference.solve_bundle", seconds=args.reference_seconds,
                                                 seed=2026), declared_unix=time.time(), veloxq_calls=0))
    rows = []
    for width in args.widths:
        started = time.monotonic()
        pool = select_pool(instance, programs, width)
        bundle = compile_meal_blocks(instance, state, pool, parent_domain_sha256=parent, tight_bounds=True)
        bundle_s = time.monotonic() - started
        if bundle["size"]["binary_variables"] != width:
            raise AssertionError("Unexpected width")
        path = output/f"lowconflict-{width}-qubo.json"
        save(path, bundle); load_bundle(path)
        witness = [0]*width
        for g in bundle["onehot_groups"]:
            witness[g["idle_index"]] = 1
        if not decode(bundle, witness)["valid"]:
            raise AssertionError("Invalid all-idle witness")
        save(output/f"lowconflict-{width}-witness.json", dict(kind="Known idle witness, not a solver result",
                                                               bundle_sha256=bundle["bundle_sha256"], bits=witness))
        ref = solve_bundle(bundle, seconds=args.reference_seconds, seed=2026)
        save(output/f"lowconflict-{width}-reference.json", ref)
        frozen = load_bundle(SOURCE/f"scale-{width}-qubo.json")
        row = dict(width=width, bundle_sha256=bundle["bundle_sha256"], build_s=bundle_s,
                   programs=bundle["size"]["option_bits"], conflicts=len(bundle["conflicts"]),
                   couplers=bundle["size"]["couplers"], density=2*bundle["size"]["couplers"]/(width*(width-1)),
                   penalty=bundle["penalty"], frozen_conflicts=len(frozen["conflicts"]),
                   frozen_couplers=frozen["size"]["couplers"], frozen_penalty=frozen["penalty"],
                   shared_programs_with_frozen=len({p["id"] for p in pool} & {p["id"] for p in frozen["options"]}),
                   reference_status=ref["reference"]["status"], reference_metrics=(ref.get("check") or {}).get("metrics"))
        rows.append(row)
        print(json.dumps(row), flush=True)
    save(output/"report.json", dict(rows=rows, full_local_program_count=len(programs), full_local_domain_sha256=parent))


if __name__ == "__main__":
    main()
