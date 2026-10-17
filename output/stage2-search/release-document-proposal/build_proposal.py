"""Read-only root-document review; emits an unapplied patch, never executes solvers."""
import ast
import difflib
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_text())

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()

roots = {name: (ROOT / name).read_text() for name in ("PROJECT_DESIGN.md", "README.md")}
before = {name: sha(ROOT / name) for name in roots}
selection = read(ROOT / "output/stage1-selected.json")
assert selection["veloxq_remote_executed"] is False
assert selection["odra5_hardware_executed"] is False
rows = []
evidence_paths = [ROOT / "output/stage1-selected.json"]
for size, makespan, variables, permutations, layers in (("2x2", 4, 1, 2, 1), ("3x3", 8, 3, 6, 2)):
    instance = "instance_" + size
    selected = ROOT / selection["selected_runs"][instance]
    run, model, verification, schedule = [read(selected / name) for name in ("run.json", "model.json", "verification.json", "schedule.json")]
    root_schedule = ROOT / ("schedule_" + size + ".json")
    assert read(root_schedule) == schedule
    assert run["instance"] == verification["instance"] == schedule["instance"] == instance
    assert run["method"] == verification["method"] == schedule["method"]
    assert "QAOA" in run["method"] and "simulator" in run["method"]
    assert schedule["makespan"] == verification["makespan"] == verification["exact_reference"] == makespan
    assert run["variables"] == len(model["variables"]) == variables
    assert model["encoding"] == run["encoding"] == "pairwise-order"
    assert len(model["order_costs"]) == permutations
    assert len({tuple(row["order"]) for row in model["order_costs"]}) == permutations
    assert digest(model) == run["model_sha256"] == verification["model_sha256"]
    assert digest(model["instance"]) == run["instance_sha256"]
    assert run["metadata"]["layers"] == layers
    assert run["accepted"] and verification["verified"] and run["total_samples"] == run["feasible_samples"] == 4096
    evidence_paths.extend([root_schedule, *[selected / name for name in ("run.json", "model.json", "verification.json", "schedule.json")]])
    rows.append(dict(instance=instance, selected_directory=str(selected.relative_to(ROOT)), root_schedule_matches_selected_json=True,
                     makespan_hours=makespan, method=run["method"], bits=variables,
                     all_common_order_costs_retained=permutations, model_sha256=digest(model),
                     saved_verification_record_read_not_rerun=True,
                     source_current_hash_matches={name: sha(ROOT / name) == expected for name, expected in run["source_sha256"].items()},
                     source_current_sha256={name: sha(ROOT / name) for name in run["source_sha256"]}))

old_status = "Status: presentation environment and both locally verified Stage 1 runs, 2026-10-16. VeloxQ remote and ODRA5 physical execution remain pending."
new_status = "Status: implemented presentation environment and selected local Stage 1 QAOA simulator results, verified against the saved selection on 2026-10-17. No VeloxQ service or physical ODRA5 execution is claimed; both remain on user hold."
old_problem = "Instance A requires its QUBO to be solved using a quantum algorithm on hardware or a simulator. Instance B requires its QUBO to be solved using a QUBO solver; our plan uses VeloxQ. The implemented fixed-horizon time-indexed QUBO, exact weights, window bounds, feasibility argument, and classical reference algorithm are documented in [STAGE1_OFFLINE.md](docs/STAGE1_OFFLINE.md). Both required methods have now run locally; the refined settings and validation are recorded in docs/STAGE1_REFINEMENT.md. Both remote backends are on user hold."
new_problem = "Instance A requires its QUBO to be solved using a quantum algorithm on hardware or a simulator; Instance B permits any QUBO solver. The selected outputs use Qiskit Aer QAOA simulation for both: A uses one bit and one layer at makespan 4 h; B uses three bits and two layers at makespan 8 h. The root schedules match the selected runs in `output/stage1-selected.json`.\n\nThe selected `solver/sequence.py` QUBOs preserve all two earliest-start common job orders for A and all six for B, and compute every permutation cost classically before quantum execution. They exclude arbitrary idle time and independent machine orders; no scalable compilation or quantum advantage is claimed. B's three-bit minimum is scoped to distinct representation of all six common orders. This is separate from the three-bit H8 deadline-feasibility reduction retaining five machine orders, including a non-permutation order. See [STAGE1_COMPACT.md](docs/STAGE1_COMPACT.md) for the selected formulation and [the claim register](docs/STAGE2_CLAIM_REGISTER.md) for the distinct deadline reduction. Earlier time-indexed/domain-wall formulations and refinement runs remain documented in [STAGE1_OFFLINE.md](docs/STAGE1_OFFLINE.md) and [STAGE1_REFINEMENT.md](docs/STAGE1_REFINEMENT.md); they are retained comparison evidence."
old_material = "- `PROJECT_DESIGN.md`: current display model and planned solver interface."
new_material = "- `PROJECT_DESIGN.md`: implemented display model, selected compact-QUBO/QAOA baseline pipeline, historical formulation comparisons and scoped Stage 2 architecture."
changes = {"PROJECT_DESIGN.md": [(old_status, new_status), (old_problem, new_problem)], "README.md": [(old_material, new_material)]}
patch = []
for name, replacements in changes.items():
    proposed = roots[name]
    for old, new in replacements:
        assert proposed.count(old) == 1, (name, "Root document changed; regenerate proposal before applying")
        proposed = proposed.replace(old, new, 1)
    patch.extend(difflib.unified_diff(roots[name].splitlines(True), proposed.splitlines(True), fromfile="a/" + name, tofile="b/" + name))

docstrings = {name: ast.get_docstring(ast.parse((ROOT / name).read_text())) for name in ("solver/sequence.py", "solver/stage1.py", "solver/compact.py", "solver/artifacts.py")}
result = dict(status="NOT_APPLIED", scope="Read-only saved-evidence/document consistency review; no solver, factory or test reruns",
              reason="Another chat owns Stage1/root presentation files; owner review required. This proposal grants no publication, push or deployment authority.",
              base_document_sha256=before, selected_artifacts=rows, current_module_docstrings=docstrings,
              evidence_file_sha256={str(p.relative_to(ROOT)): sha(p) for p in evidence_paths},
              selected_vs_deadline_scope="Selected B represents all six common job orders; separate H8 deadline formulation retains five machine-order classes. They are not interchangeable.",
              original_root_files_modified=False, historical_sections_modified=False, solver_calls=0, factory_calls=0, test_reruns=0)
(OUT / "proposed-root-documents.patch").write_text("".join(patch))
result["unapplied_patch_sha256"] = sha(OUT / "proposed-root-documents.patch")
assert {name: sha(ROOT / name) for name in roots} == before
(OUT / "report.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(dict(status=result["status"], root_document_hashes_unchanged=True,
                      all_current_source_hashes_match_saved_runs=all(all(row["source_current_hash_matches"].values()) for row in rows),
                      patch_sha256=result["unapplied_patch_sha256"]), indent=2))
