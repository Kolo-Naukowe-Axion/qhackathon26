"""Build frozen core bundles or independently evaluate normalized method output."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import time
from .audit import audit_bundle
from .contracts import load_bundle, save_json
from .decode import decode
from .domain import PROFILE, SCENARIOS, fixture, snapshot, validate_instance
from .native import solve_program_master
from .options import enumerate_options, restricted_pool
from .qubo import compile_qubo, ising
from .methods.classical import solve_exact, solve_qubo


def new_directory(path):
    if path.exists():
        raise ValueError("Choose a fresh output directory; evidence is never overwritten")
    path.mkdir(parents=True)


def summary(bundle, result):
    checked = [decode(bundle, sample["bits"]) for sample in result["samples"]]
    valid = [r for r in checked if r["valid"]]
    best = min(valid, key=lambda r: tuple(r["check"]["metrics"][k] for k in ("U", "W", "B", "R"))) if valid else None
    return dict(method=result["method_id"], status=result["status"], returns=len(checked),
                valid_returns=len(valid), best_metrics=None if best is None else best["check"]["metrics"],
                best_energy=None if best is None else best["energy"], timings=result["timings"],
                reference_status=(result.get("reference") or {}).get("status"))


def build(output, *, instance_path=None, cap=16, native_seconds=10, sa_seconds=2):
    instance = fixture() if instance_path is None else validate_instance(json.loads(Path(instance_path).read_text()))
    new_directory(output)
    started = time.monotonic()
    save_json(output / "instance.json", instance)
    rows = []
    for scenario in SCENARIOS:
        directory = output / scenario
        directory.mkdir()
        state = snapshot(instance, scenario)
        save_json(directory / "snapshot.json", state)
        before = time.monotonic()
        programs = enumerate_options(instance, state)
        generated = time.monotonic() - before
        complete = compile_qubo(instance, state, programs)
        small_programs = restricted_pool(programs, state, cap)
        quantum = compile_qubo(instance, state, small_programs,
                               representation=f"option-cap-{cap}", parent_sha256=complete["bundle_sha256"])
        if len(small_programs) == len(programs):
            # Canonical statement: this particular cap did not remove a choice.
            quantum["scope"] = "Identical complete option domain; cap removed no options"
            from .domain import digest
            quantum["bundle_sha256"] = digest({k: v for k, v in quantum.items() if k != "bundle_sha256"})
        save_json(directory / "complete-qubo.json", complete)
        save_json(directory / "quantum-qubo.json", quantum)
        save_json(directory / "quantum-ising.json", ising(quantum))
        outcomes = {}
        audits = {}
        for label, bundle in (("complete", complete), ("quantum", quantum)):
            audits[label] = audit_bundle(bundle)
            save_json(directory / f"audit-{label}.json", audits[label])
            reference = solve_program_master(bundle, dict(wall_time_limit_s=native_seconds))
            if reference["reference"]["status"] == "OPTIMAL":
                if reference["reference"]["objective"] != audits[label]["raw_enumeration"]["exact_best_energy"]:
                    raise AssertionError("Native reference differs from independent selection enumeration")
            save_json(directory / f"reference-{label}.json", reference)
            outcomes[label] = summary(bundle, reference)
            if label == "quantum":
                exact = solve_exact(bundle)
                if exact["reference"]["objective"] != audits[label]["raw_enumeration"]["exact_best_energy"]:
                    raise AssertionError("QUBO ground energy differs from independent raw minimum")
                save_json(directory / "exact-quantum.json", exact)
                outcomes["quantum_exact"] = summary(bundle, exact)
        annealed = solve_qubo(complete, dict(wall_time_limit_s=sa_seconds))
        save_json(directory / "sa-complete.json", annealed)
        outcomes["sa_complete"] = summary(complete, annealed)
        qbest = outcomes["quantum"]["best_metrics"]
        cbest = outcomes["complete"]["best_metrics"]
        gap = None if qbest is None or cbest is None else {k:qbest[k]-cbest[k] for k in ("U", "W", "B", "R")}
        row = dict(scenario=scenario, common_prefix_sha256=state["common_prefix_sha256"],
                   complete=complete["size"], quantum=quantum["size"],
                   generation_s=generated, restrictions=dict(cap=cap, original_options=len(programs),
                                                            retained_options=len(small_programs)),
                   results=outcomes, restricted_minus_complete_metrics=gap,
                   gap_status="Exact in declared program domains" if all(outcomes[k]["reference_status"]=="OPTIMAL" for k in ("complete","quantum")) else "Unresolved")
        rows.append(row)
        print(json.dumps(dict(scenario=scenario, complete_bits=complete["size"]["binary_variables"],
                              quantum_bits=quantum["size"]["binary_variables"], native=cbest, quantum=qbest)), flush=True)
    report = dict(schema_version="catering-foundation.v1", profile_id=PROFILE,
                  scope="Small complete finite-grid contiguous-packing core; frozen whole-started-batch reservations; idle cooker withdrawal",
                  not_flagship=True, rows=rows, all_checks_passed=True,
                  four_cases_share_committed_prefix=len({r["common_prefix_sha256"] for r in rows}) == 1,
                  total_s=time.monotonic()-started, physical_qpu_calls=0, veloxq_calls=0,
                  environment=dict(python=platform.python_version(),
                                   numpy=importlib.metadata.version("numpy"),
                                   ortools=importlib.metadata.version("ortools")),
                  disabled_features=["phase_aware_WIP", "interrupted_cooking", "ingredients", "holding", "power", "money"])
    if not report["four_cases_share_committed_prefix"]:
        raise AssertionError("Scenario prefixes differ")
    save_json(output / "report.json", report)
    files = {str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(output.rglob("*")) if p.is_file()}
    root = Path(__file__).resolve().parents[1]
    sources = {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted((root/"catering").rglob("*.py"))}
    save_json(output / "manifest.json", dict(schema_version="catering-foundation-manifest.v1",
                                           files=files, sources=sources))
    return report


def evaluate(bundle_path, samples_path, output):
    bundle = load_bundle(bundle_path)
    payload = json.loads(samples_path.read_text())
    if not isinstance(payload, dict) or payload.get("bundle_sha256") != bundle["bundle_sha256"]:
        raise ValueError("Method output must identify the exact bundle hash")
    samples = payload["samples"]
    results = []
    for sample in samples:
        if type(sample.get("count")) is not int or sample["count"] < 1:
            raise ValueError("Positive integer sample counts required")
        checked = decode(bundle, sample["bits"])
        if "reported_energy" in sample and int(sample["reported_energy"]) != int(checked["energy"]):
            raise ValueError("Reported energy differs from literal QUBO")
        results.append(dict(count=sample["count"], **checked))
    if output.exists():
        raise ValueError("Choose a fresh output file")
    save_json(output, dict(schema_version="catering-evaluation.v1", bundle_sha256=bundle["bundle_sha256"],
                           method_id=payload["method_id"], results=results, repair=False))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("build")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--instance", type=Path)
    p.add_argument("--quantum-cap", type=int, default=16)
    p.add_argument("--native-seconds", type=float, default=10)
    p.add_argument("--sa-seconds", type=float, default=2)
    p = sub.add_parser("evaluate")
    p.add_argument("--bundle", type=Path, required=True)
    p.add_argument("--samples", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "build":
        build(args.output, instance_path=args.instance, cap=args.quantum_cap,
              native_seconds=args.native_seconds, sa_seconds=args.sa_seconds)
    else:
        evaluate(args.bundle, args.samples, args.output)


if __name__ == "__main__":
    main()
