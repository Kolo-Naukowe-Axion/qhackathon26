"""Offline tests for the local-penalty study variants. No token or network is used."""

import json
from pathlib import Path

import pytest

from catering.contracts import load_bundle
from catering.decode import decode
from catering.methods import veloxq_penalty as vp
from catering.qubo import energy, validate_bundle

ROOT = Path(__file__).resolve().parents[2]
SMALL = [ROOT/"output/catering-complete-cell-v3/quantum-qubo.json"] + [
    ROOT/f"output/catering-foundation-v3/{s}/quantum-qubo.json" for s in ("S0", "S1", "S2", "S3")]


def reference_bits(path):
    name = "reference-encoded.json" if "complete-cell" in str(path) else "quantum-reference.json"
    return json.loads((path.parent/name).read_text())["samples"][0]["bits"]


@pytest.mark.parametrize("path", SMALL, ids=lambda p: p.parent.name)
@pytest.mark.parametrize("variant", vp.VARIANTS)
def test_variant_keeps_reference_optimum_and_meaning(path, variant):
    source = load_bundle(path)
    built = vp.build_variant(source, variant)
    validate_bundle(built)
    assert built["parent_sha256"] == source["bundle_sha256"]
    assert built["variable_order"] == source["variable_order"]
    bits = reference_bits(path)
    old, new = decode(source, bits), decode(built, bits)
    assert old["valid"] and new["valid"]
    assert old["check"]["metrics"] == new["check"]["metrics"]
    w = built["objective"]["weights"]
    assert int(new["energy"]) == sum(w[k]*new["check"]["metrics"][k] for k in "UWBR")
    assert vp.check_variant(built, source, [bits], trials=50)


@pytest.mark.parametrize("path", SMALL, ids=lambda p: p.parent.name)
def test_local_penalty_is_smaller_than_global(path):
    source = load_bundle(path)
    for variant in vp.VARIANTS:
        built = vp.build_variant(source, variant)
        assert vp.coefficient_stats(built)["penalty_over_w_U"] <= vp.coefficient_stats(source)["penalty_over_w_U"]


def test_uw_variant_drops_tiebreak_weights():
    source = load_bundle(SMALL[-1])
    built = vp.build_variant(source, "local-uw")
    bounds = source["objective"]["component_bounds"]
    assert built["objective"]["weights"] == dict(U=bounds["W"] + 1, W=1, B=0, R=0)


def test_too_small_penalty_is_detected():
    source = load_bundle(SMALL[-1])
    built = vp.build_variant(source, "local")
    weakened = dict(built, linear=list(built["linear"]), quadratic=[dict(t) for t in built["quadratic"]])
    # Remove every conflict penalty: conflicting states become as cheap as feasible ones.
    conflicts = {tuple(c) for c in built["conflicts"]}
    objective = {(t["i"], t["j"]): int(t["value"]) for t in built["objective"]["quadratic"]}
    for t in weakened["quadratic"]:
        if (t["i"], t["j"]) in conflicts:
            t["value"] = str(objective.get((t["i"], t["j"]), 0))
    with pytest.raises(AssertionError):
        vp.check_variant(weakened, source, [], trials=200)
    assert energy(built, reference_bits(SMALL[-1])) == energy(weakened, reference_bits(SMALL[-1]))


def test_low_conflict_index_matches_compiler_conflicts():
    from catering.methods.veloxq_lowconflict import ConflictIndex
    source = load_bundle(SMALL[-1])
    index = ConflictIndex(source["instance"], source["options"])
    pairs = {(k, int(j)) for k in range(index.n) for j in index.conflicts_of(k).nonzero()[0] if j > k}
    assert pairs == {tuple(c) for c in source["conflicts"]}
