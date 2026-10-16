"""Build a fresh, verified Stage 1 bundle locally; never submits to VeloxQ.

Usage: .venv/bin/python scripts/prepare-stage1.py --output output/stage1-ready
"""

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "output/stage1-ready")
    parser.add_argument("--export-final", action="store_true", help="Copy verified schedules to the required root filenames")
    parser.add_argument("--prepare-velox-packets", action="store_true", help="Explicitly prepare local SDK files, without submitting")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        parser.error("Use an empty output directory; previous run evidence is retained")
    output.mkdir(parents=True, exist_ok=True)

    def run(module, *options):
        subprocess.run([sys.executable, "-m", module, *map(str, options)], cwd=ROOT, check=True)

    run("unittest", "discover", "-s", "tests", "-p", "test_*.py")
    run("solver.quantum", "--output", output / "qaoa-2x2")
    run("solver.local", "--output", output / "anneal-3x3")
    if args.prepare_velox_packets:
        run("solver.velox", "--output", output / "velox-3x3")
        run("solver.velox", "--encoding", "domain-wall", "--output", output / "velox-3x3-domain-wall")
    run("solver.audit", "--output", output / "formulation-audit.json")
    selected = {}
    for size, directory in (("2x2", "qaoa-2x2"), ("3x3", "anneal-3x3")):
        options = ["--run", output / directory]
        if args.export_final:
            options.extend(["--export", ROOT / f"schedule_{size}.json"])
        run("solver.verify", *options)
        selected[f"instance_{size}"] = str((output / directory).relative_to(ROOT)) if output.is_relative_to(ROOT) else str(output / directory)
    manifest = dict(status="Both Stage 1 required-method runs verified locally; remote backends on hold",
                    selected_runs=selected,
                    veloxq_remote_executed=False,
                    odra5_hardware_executed=False,
                    remote_backends_on_hold=["VeloxQ", "ODRA5"],
                    note="No remote submission is part of this preparation command")
    (output / "selected-runs.json").write_text(json.dumps(manifest, indent=2) + "\n")
    if args.export_final:
        (ROOT / "output/stage1-selected.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Verified local bundle: {output}", flush=True)


if __name__ == "__main__":
    main()
