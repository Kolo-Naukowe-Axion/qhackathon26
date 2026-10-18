#!/usr/bin/env python3
"""Verify the E6 archive and replay saved VQE states; never train or sample."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
from catering.decode import decode
from catering.methods import vqe
from catering.qubo import energy, validate_bundle


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(study):
    manifest = json.loads((study / "manifest.json").read_text())
    archive_files = {}
    for name, expected in manifest["sha256"].items():
        actual = sha(study / name)
        if actual != expected:
            raise AssertionError(f"Archive checksum mismatch: {name}")
        archive_files[name] = actual

    cases = []
    for case in ("cell", "S0", "S1", "S2", "S3"):
        bundle_path = (ROOT / "output/catering-complete-cell-v3/quantum-qubo.json" if case == "cell"
                       else ROOT / f"output/catering-foundation-v3/{case}/quantum-qubo.json")
        result_path = study / f"method-results/{case}/result.json"
        bundle = validate_bundle(json.loads(bundle_path.read_text()))
        result = json.loads(result_path.read_text())
        if result["bundle_sha256"] != bundle["bundle_sha256"]:
            raise AssertionError(f"Input identity mismatch: {case}")
        spec = vqe.Spec(**result["configuration"]["spec"])
        # This function builds the circuit and evaluates the saved vector only.
        # It performs neither optimization nor random measurement draws.
        probabilities = vqe.replay_parameters(bundle, spec, result["work"]["seed"],
                                             result["optimized_parameters"])
        sector = vqe.Problem(bundle).sector
        p_optimal = float(probabilities[sector["opt"]].sum())
        p_valid = float(probabilities[sector["valid"]].sum())
        recorded = result["exact_distribution"]
        for key, actual in (("p_optimal", p_optimal), ("p_valid", p_valid)):
            if not np.isclose(actual, recorded[key], atol=1e-10, rtol=0):
                raise AssertionError(f"Saved distribution mismatch: {case}/{key}")
        valid_shots, total_shots, best, returned_rows = 0, 0, None, 0
        for sample in result["samples"]:
            if type(sample["count"]) is not int or sample["count"] <= 0:
                raise AssertionError(f"Invalid sample count: {case}")
            decoded = decode(bundle, sample["bits"])
            if energy(bundle, sample["bits"]) != int(sample["reported_energy"]):
                raise AssertionError(f"Literal energy mismatch: {case}")
            total_shots += sample["count"]
            returned_rows += 1
            if decoded["valid"]:
                valid_shots += sample["count"]
                metrics = tuple(decoded["check"]["metrics"][k] for k in ("U", "W", "B", "R"))
                best = metrics if best is None else min(best, metrics)
        if total_shots != result["work"]["final_sample_shots"] or best is None:
            raise AssertionError(f"Incomplete or wholly invalid export: {case}")
        cases.append(dict(case=case, bundle_sha256=bundle["bundle_sha256"],
                          input_file=str(bundle_path.relative_to(ROOT)), input_file_sha256=sha(bundle_path),
                          result_file=str(result_path.relative_to(ROOT)), result_file_sha256=sha(result_path),
                          optimized_parameters_sha256=hashlib.sha256(json.dumps(
                              result["optimized_parameters"], separators=(",", ":")).encode()).hexdigest(),
                          p_optimal=p_optimal, p_valid=p_valid, returned_rows=returned_rows,
                          valid_shots=valid_shots, total_shots=total_shots,
                          best_metrics=dict(zip(("U", "W", "B", "R"), best)),
                          objective_evaluations=result["work"]["objective_evaluations"]))

    declaration = json.loads((study / "heldout_predeclaration.json").read_text())
    with (study / "runs/heldout_runs.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    summaries = []
    for case in ("S2", "S3"):
        for label in ("primary", "baseline"):
            selected = [r for r in rows if r["case"] == case and (
                r["method"] == declaration["primary"]["name"] if label == "primary"
                else r["method"].startswith("baseline:"))]
            if sorted(int(r["seed"]) for r in selected) != sorted(declaration["seeds"]):
                raise AssertionError(f"Missing or duplicate CSV seeds: {case}/{label}")
            summaries.append(dict(case=case, method=label, seeds=len(selected),
                                  mode_optimum_over_half_hits=sum(r["mode_is_opt"] == "True" for r in selected),
                                  sampled_optimum_hits=sum(r["shot_hit_opt"] == "True" for r in selected),
                                  median_p_optimal=statistics.median(float(r["p_opt"]) for r in selected),
                                  median_objective_evaluations=statistics.median(float(r["nfev"]) for r in selected)))
    source_files = ("scripts/verify-vqe-concentration.py", "catering/methods/vqe.py",
                    "catering/decode.py", "catering/check.py", "catering/paired_meals.py",
                    "catering/qubo.py")
    return dict(schema_version="catering-vqe-concentration-verification.v1",
                verified_at=datetime.now(timezone.utc).isoformat(), all_checks_passed=True,
                execution=dict(training=False, new_sampling=False, service_calls=0, physical_qpu_calls=0),
                scope="Manifest integrity, five saved-parameter state replays, all exported sample checks, CSV aggregation",
                limits=["S2/S3 had already been evaluated in E5; they are not wholly unseen cases.",
                        "Only the five exported seed-0 vectors are replayed; ten-seed summaries are recomputed from archived CSV rows.",
                        "The 0.995 maximum-state stopping threshold explains concentration near 99.5%.",
                        "Exact one-hot-sector simulation; offered-pool optima are not full-kitchen optima.",
                        "QAOA budgets and shots differ; this is not a matched-budget ranking or quantum advantage."],
                archive_manifest_sha256=sha(study / "manifest.json"), archive_files=archive_files,
                source_files={name: sha(ROOT / name) for name in source_files},
                cases=cases, csv_summaries=summaries)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path, default=ROOT / "output/catering-methods/vqe/E6-concentration")
    parser.add_argument("--output", type=Path, required=True, help="Fresh receipt path; existing files are never overwritten")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Choose a fresh output file")
    report = verify(args.study.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(dict(output=str(args.output), all_checks_passed=True,
                          cases=len(report["cases"]), csv_summaries=report["csv_summaries"]), indent=2))


if __name__ == "__main__":
    main()
