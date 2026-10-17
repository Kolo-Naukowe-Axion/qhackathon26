"""Retain raw-model classical results and a sharing-policy ablation locally."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import time

from .classical_cases import cases
from .native_slots import solve_native
from .check import check_plan
from .domain import make_plan

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+"\n")


def verify_frozen():
    root = ROOT/"output/catering-foundation-v2"
    manifest = json.loads((root/"manifest.json").read_text())
    for section, parent in (("files",root),("sources",ROOT)):
        for name, expected in manifest[section].items():
            if sha(parent/name) != expected:
                raise ValueError("Frozen foundation changed: "+name)
    return dict(manifest_sha256=sha(root/"manifest.json"),
                files_checked=len(manifest["files"]),sources_checked=len(manifest["sources"]))


def run(output, seconds=3, include_scale=True):
    start = time.monotonic()
    output = Path(output)
    if output.exists():
        raise ValueError("Choose a fresh output directory")
    frozen = verify_frozen()
    rows = []
    for case in cases(include_scale=include_scale):
        cid = case["case_id"]
        save(output/cid/"instance.json",case["instance"])
        save(output/cid/"snapshot.json",case["snapshot"])
        row = dict(case_id=cid,purpose=case["purpose"],methods={})
        for sharing, name in ((True,"joint"),(False,"no-sharing")):
            result = solve_native(case["instance"],case["snapshot"],
                                  dict(wall_time_limit_s=seconds),dict(workers=1,seed=2026,allow_sharing=sharing))
            save(output/cid/(name+".json"),result)
            row["methods"][name] = {k:result[k] for k in (
                "reference_status","timings","model_size","objective_bound","objective_weights")}
            row["methods"][name]["objective"] = result.get("objective")
            row["methods"][name]["metrics"] = (result["check"] or {}).get("metrics")
            row["methods"][name]["raw_valid"] = (result["check"] or {}).get("valid")
        if cid.startswith("core-"):
            # Independent raw reference must agree with the already frozen exact
            # complete-domain audit, not merely another new solver invocation.
            audit = json.loads((ROOT/"output/catering-foundation-v2"/cid[5:]/"audit-complete.json").read_text())
            bundle = json.loads((ROOT/"output/catering-foundation-v2"/cid[5:]/"complete-qubo.json").read_text())
            bits = audit["raw_enumeration"]["best_bits"]
            programs = bundle["snapshot"]["fixed_batches"]+[p for b,p in zip(bits,bundle["options"]) if b]
            checked = check_plan(bundle["instance"],bundle["snapshot"],make_plan(bundle["instance"],programs,bundle["snapshot"].get("recovery_operations",[])))
            if not checked["valid"]:
                raise AssertionError("Invalid frozen reference witness")
            expected = checked["metrics"]
            if row["methods"]["joint"]["metrics"] != expected:
                raise AssertionError("Frozen/direct disagreement: "+cid)
            row["frozen_complete_optimum_agreement"] = True
        joint,separate = (row["methods"][n] for n in ("joint","no-sharing"))
        row["both_optimal"] = all(m["reference_status"] == "OPTIMAL" for m in (joint,separate))
        if row["both_optimal"]:
            row["policy_delta_no_sharing_minus_joint"] = {
                k:separate["metrics"][k]-joint["metrics"][k] for k in ("U","W","B","R")}
            if tuple(joint["metrics"][k] for k in ("U","W","B","R")) > tuple(separate["metrics"][k] for k in ("U","W","B","R")):
                raise AssertionError("Restriction improved a certified lexicographic optimum")
        rows.append(row)
        print(json.dumps(dict(case=cid,methods={n:dict(status=m["reference_status"],metrics=m["metrics"])
                                               for n,m in row["methods"].items()})),flush=True)
    import ortools
    report = dict(schema_version="catering-classical-benchmark.v1",cases=rows,
                  frozen_foundation=frozen,budget_per_solve_s=seconds,
                  comparison="Same raw core model; no-sharing restricts each new batch to one demand group",
                  native_objective="Lexicographic U (weighted missed), W (waste lots), B (new batches), R (changed program IDs)",
                  quantum_advantage_claim=False,veloxq_calls=0,physical_qpu_calls=0,
                  environment=dict(python=platform.python_version(),ortools=ortools.__version__,
                                   machine=platform.machine(),system=platform.platform(),logical_cpus=os.cpu_count()),
                  total_s=time.monotonic()-start,
                  limitations=["Synthetic core inputs, not the full ambitious ingredients/holding/power profile",
                               "Time-limited feasible results are incumbents, not certified optima",
                               "No-sharing is a strong restricted-policy CP baseline, not a greedy algorithm",
                               "Scalar objectives use model-specific exact lexicographic weights; compare metric tuples",
                               "Per-solve timing includes model build and search, excludes SDK import/process startup"])
    save(output/"report.json",report)
    paths = ["catering/native_slots.py","catering/classical_cases.py","catering/benchmark_classical.py",
             "catering/domain.py","catering/check.py","catering/requirements.txt",
             "tests/catering/test_native_slots.py"]
    save(output/"manifest.json",dict(schema_version="catering-classical-manifest.v1",
         files={str(p.relative_to(output)):sha(p) for p in sorted(output.rglob("*.json"))},
         sources={p:sha(ROOT/p) for p in paths}))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--seconds",type=float,default=3)
    parser.add_argument("--small-only",action="store_true")
    args = parser.parse_args()
    run(args.output,args.seconds,not args.small_only)


if __name__ == "__main__":
    main()
