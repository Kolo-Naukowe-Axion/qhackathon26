"""Same-SA comparison of frozen bundles and their local-penalty variants (offline).

Every variant of a source bundle has the same variables, groups and conflicts, so
decoded (U,W,B,R) tuples are directly comparable; raw energies are not. Each
sample is decoded and checked by catering.run's evaluator on its own bundle,
without repair. For the local-uw variant B/R are not in the QUBO, so its best
tuple is the lexicographic minimum over valid samples (post-hoc tie-break).
"""
import argparse
import json
import sys
import time
from pathlib import Path

from ..contracts import load_bundle
from ..decode import decode
from .classical import solve_qubo

ROOT = Path(__file__).resolve().parents[2]


def reference_for(source_path):
    """Frozen same-domain CP incumbent bits for a source bundle (strongest retained run)."""
    source_path = Path(source_path)
    stronger = ROOT/"output/catering-classical-scale-v3"/source_path.name.replace("-qubo.json", "-reference.json")
    if "catering-velox-scale-v3" in str(source_path) and stronger.exists():
        return stronger
    if "complete-cell" in str(source_path):
        return source_path.parent/"reference-encoded.json"
    return source_path.parent/source_path.name.replace("-qubo.json", "-reference.json")


def tuple_of(decoded):
    m = decoded["check"]["metrics"]
    return [m["U"], m["W"], m["B"], m["R"]]


def summarize(bundle, samples):
    rows = [(s, decode(bundle, s["bits"])) for s in samples]
    valid = [tuple_of(d) for _, d in rows if d["valid"]]
    return dict(samples=len(rows), valid=len(valid), best_tuple=min(valid) if valid else None,
                valid_tuples=sorted(valid))


def run_case(source_path, variant_paths, config, budget, output, names=None):
    source = load_bundle(source_path)
    ref_path = reference_for(source_path)
    ref = json.loads(ref_path.read_text())
    if ref["bundle_sha256"] != source["bundle_sha256"]:
        raise ValueError(f"Reference {ref_path} is for another bundle")
    ref_decoded = decode(source, ref["samples"][0]["bits"])
    row = dict(source=str(source_path), source_sha256=source["bundle_sha256"], reference=str(ref_path),
               reference_status=(ref.get("reference") or {}).get("status"),
               reference_tuple=tuple_of(ref_decoded) if ref_decoded["valid"] else None, runs={})
    for name, path in [("source", source_path)] + list(variant_paths.items()):
        if names and name not in names:
            continue
        bundle = load_bundle(path)
        if name != "source" and bundle["parent_sha256"] != source["bundle_sha256"]:
            raise ValueError(f"{path} is not a variant of {source_path}")
        started = time.monotonic()
        result = solve_qubo(bundle, budget, config)
        wall = time.monotonic() - started
        summary = summarize(bundle, result["samples"])
        summary.update(bundle=str(path), bundle_sha256=bundle["bundle_sha256"], wall_s=wall, status=result["status"],
                       work=result["work"])
        best, target = summary["best_tuple"], row["reference_tuple"]
        summary["at_or_better_than_reference"] = sum(t <= target for t in summary["valid_tuples"]) if target else None
        row["runs"][name] = summary
        (output/"results").mkdir(parents=True, exist_ok=True)
        (output/"results"/f"{Path(path).stem}-sa.json").write_text(json.dumps(result, sort_keys=True) + "\n")
        print(Path(source_path).parent.name, Path(source_path).name, name, summary["valid"], "/", summary["samples"],
              best, "ref", target, f"{wall:.0f}s", flush=True)
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--study", required=True, help="Directory with bundles/build-report.json")
    parser.add_argument("--output", required=True, help="New directory")
    parser.add_argument("--only", nargs="*", help="Substrings of source paths to run")
    parser.add_argument("--variants", nargs="*", help="Subset of source and variant names")
    parser.add_argument("--restarts", type=int, default=32)
    parser.add_argument("--sweeps", type=int, default=200)
    parser.add_argument("--seconds", type=float, default=3600)
    args = parser.parse_args()
    study, output = Path(args.study), Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    config = dict(seed=2026, restarts=args.restarts, sweeps=args.sweeps)
    budget = dict(wall_time_limit_s=args.seconds)
    report = json.loads((study/"bundles"/"build-report.json").read_text())
    plan = dict(solver="catering.methods.classical.solve_qubo (seeded Metropolis SA, cold random bits, no repair)",
                config=config, budget=budget, variants=["source"] + report["variants"],
                declared_unix=time.time(), argv=sys.argv[1:])
    (output/"plan.json").write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")
    rows = []
    for item in report["rows"]:
        if args.only and not any(s in item["source"] for s in args.only):
            continue
        variants = {v: study/"bundles"/item[v]["file"] for v in report["variants"]}
        rows.append(run_case(item["source"], variants, config, budget, output, args.variants))
        (output/"comparison.json").write_text(json.dumps(dict(plan=plan, rows=rows), indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
