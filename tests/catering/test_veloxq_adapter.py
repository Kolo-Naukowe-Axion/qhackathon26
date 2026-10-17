"""Offline tests for the VeloxQ catering adapter. No token or network is used."""

import itertools
import json
import random

import dimod
import pytest

from catering.methods import veloxq as vq


def random_bundle(n, seed, density=0.6, magnitude=50):
    rng = random.Random(seed)
    quadratic = [{"i": i, "j": j, "value": str(rng.randint(-magnitude, magnitude))}
                 for i, j in itertools.combinations(range(n), 2) if rng.random() < density]
    return {"bundle_id": f"random-{n}-{seed}", "case_id": f"random-{n}-{seed}",
            "qubo": {"constant": str(rng.randint(-magnitude, magnitude)),
                     "linear": [str(rng.randint(-magnitude, magnitude)) for _ in range(n)],
                     "quadratic": quadratic, "variable_order": [f"v{i}" for i in range(n)]}}


def all_bits(n):
    return [list(bits) for bits in itertools.product((0, 1), repeat=n)]


def test_contract_smoke_optimum_and_spin_agreement():
    q = vq.load_qubo(vq.SMOKE_BUNDLE)
    model = vq.qubo_to_spin(q)
    energies = {tuple(b): vq.qubo_energy(q, b) for b in all_bits(2)}
    assert energies == {(0, 0): 0, (1, 0): -4, (0, 1): -3, (1, 1): -1}
    assert min(energies, key=energies.get) == (1, 0)
    for bits, energy in energies.items():
        assert vq.spin_energy(model, [2 * b - 1 for b in bits]) == vq.SPIN_SCALE * energy


@pytest.mark.parametrize("n,seed", [(1, 0), (3, 1), (6, 2), (10, 3)])
def test_random_qubo_spin_energy_exact_on_all_states(n, seed):
    q = vq.load_qubo(random_bundle(n, seed))
    model = vq.qubo_to_spin(q)
    assert all(isinstance(v, int) for v in model["h"] + list(model["J"].values()) + [model["offset"]])
    for bits in all_bits(n):
        assert vq.spin_energy(model, [2 * b - 1 for b in bits]) == 4 * vq.qubo_energy(q, bits)


def test_spin_model_matches_dimod_conversion():
    q = vq.load_qubo(random_bundle(7, 11))
    bqm = dimod.BinaryQuadraticModel(dict(enumerate(q["linear"])), q["quadratic"], q["constant"], dimod.BINARY)
    spin = bqm.spin
    model = vq.qubo_to_spin(q)
    assert model["offset"] == 4 * spin.offset
    assert all(model["h"][i] == 4 * spin.linear[i] for i in range(q["n"]))
    dimod_J = {tuple(sorted(key)): 4 * v for key, v in spin.quadratic.items() if v}
    assert model["J"] == dimod_J


@pytest.mark.parametrize("bad", [
    {"constant": "1.0"}, {"constant": "1e3"}, {"constant": "NaN"}, {"constant": 3}, {"constant": "01"},
    {"linear": ["1"]}, {"variable_order": ["A", "A"]},
    {"quadratic": [{"i": 1, "j": 0, "value": "1"}]}, {"quadratic": [{"i": 0, "j": 0, "value": "1"}]},
    {"quadratic": [{"i": 0, "j": 1, "value": "1"}, {"i": 0, "j": 1, "value": "2"}]},
    {"quadratic": [{"i": 0, "j": 2, "value": "1"}]}, {"quadratic": [{"i": True, "j": 1, "value": "1"}]},
])
def test_load_qubo_rejects_malformed(bad):
    bundle = json.loads(json.dumps(vq.SMOKE_BUNDLE))
    bundle["qubo"].update(bad)
    with pytest.raises(ValueError):
        vq.load_qubo(bundle)


@pytest.mark.parametrize("n,seed,density", [(2, 0, 1.0), (8, 5, 0.9), (40, 6, 0.05)])
def test_packet_round_trip_through_sdk_writer(tmp_path, n, seed, density):
    q = vq.load_qubo(random_bundle(n, seed, density))
    model = vq.qubo_to_spin(q)
    packet = vq.read_packet(vq.write_packet(model, tmp_path / "p.h5"))
    assert packet["var_type"] == "SPIN"
    assert packet["offset"] == model["offset"]
    assert packet["h"] == {i: float(v) for i, v in enumerate(model["h"])}
    assert packet["J"] == {k: float(v) for k, v in model["J"].items()}


def test_packet_keeps_large_coefficients_exact(tmp_path):
    # Above 2^24 a float32 packet would round; the v3 scale bundles reach ~1e10.
    big = 2**40 + 7
    bundle = {"case_id": "big", "qubo": {"constant": str(big), "linear": [str(-big), str(big + 3)],
                                        "quadratic": [{"i": 0, "j": 1, "value": str(big - 5)}],
                                        "variable_order": ["a", "b"]}}
    model = vq.qubo_to_spin(vq.load_qubo(bundle))
    packet = vq.read_packet(vq.write_packet(model, tmp_path / "big.h5"))
    assert packet["dtype"].startswith("int")
    assert packet["offset"] == model["offset"]
    assert packet["h"] == {i: float(v) for i, v in enumerate(model["h"])}
    assert packet["J"] == {k: float(v) for k, v in model["J"].items()}
    result = vq.solve_qubo(bundle, {}, {"ledger_path": str(tmp_path / "l.json")}, tmp_path / "run")
    assert result["status"] == "not_run" and result["configuration"]["packet_coefficient_dtype"].startswith("int")


def test_write_packet_refuses_inexact_coefficients(tmp_path):
    bundle = json.loads(json.dumps(vq.SMOKE_BUNDLE))
    bundle["qubo"]["linear"] = [str(2**60), "0"]
    model = vq.qubo_to_spin(vq.load_qubo(bundle))
    with pytest.raises(ValueError, match="float64"):
        vq.write_packet(model, tmp_path / "p.h5")


def fake_sampleset(q, model, rows, *, vartype="SPIN", omit_offset=False, sign=1, shuffle_labels=True, labels=None):
    """Build a response like VeloxSampleSet.from_result: string labels, aggregated rows."""
    n = q["n"]
    order = list(range(n))
    if shuffle_labels:
        random.Random(0).shuffle(order)
    samples, energies = [], []
    for bits in rows:
        spins = [2 * b - 1 for b in bits]
        energy = vq.spin_energy(model, spins) - (model["offset"] if omit_offset else 0)
        values = spins if vartype == "SPIN" else bits
        samples.append([values[i] for i in order])
        energies.append(sign * energy)
    names = labels or [str(i) for i in order]
    return dimod.SampleSet.from_samples((samples, names), vartype=vartype, energy=energies)


@pytest.mark.parametrize("vartype", ["SPIN", "BINARY"])
@pytest.mark.parametrize("omit_offset", [False, True])
def test_parse_samples_accepts_known_conventions(vartype, omit_offset):
    q = vq.load_qubo(random_bundle(5, 9))
    model = vq.qubo_to_spin(q)
    rows = all_bits(5)[:12] + [[1, 0, 1, 0, 1]]
    samples, info = vq.parse_samples(fake_sampleset(q, model, rows, vartype=vartype, omit_offset=omit_offset), q, model)
    assert info["energy_convention"] == ("Ising offset omitted by result" if omit_offset else "full model")
    assert sum(s["count"] for s in samples) == len(rows)
    for s in samples:
        assert int(s["reported_energy"]) == vq.qubo_energy(q, s["bits"])
    assert [int(s["reported_energy"]) for s in samples] == sorted(int(s["reported_energy"]) for s in samples)


def test_parse_samples_smoke_bits_in_variable_order():
    q = vq.load_qubo(vq.SMOKE_BUNDLE)
    model = vq.qubo_to_spin(q)
    samples, _ = vq.parse_samples(fake_sampleset(q, model, [[1, 0], [0, 1]]), q, model)
    assert samples[0]["bits"] == [1, 0] and samples[0]["reported_energy"] == "-4"


def test_parse_samples_rejects_wrong_sign_and_labels():
    q = vq.load_qubo(random_bundle(4, 2))
    model = vq.qubo_to_spin(q)
    rows = all_bits(4)
    with pytest.raises(ValueError, match="disagree"):
        vq.parse_samples(fake_sampleset(q, model, rows, sign=-1), q, model)
    with pytest.raises(ValueError, match="label"):
        vq.parse_samples(fake_sampleset(q, model, rows, shuffle_labels=False, labels=["0", "1", "2", "x"]), q, model)
    with pytest.raises(ValueError, match="do not match"):
        vq.parse_samples(fake_sampleset(q, model, rows, shuffle_labels=False, labels=["0", "1", "2", "4"]), q, model)


def test_parse_samples_rejects_mixed_conventions():
    q = vq.load_qubo(random_bundle(4, 3))
    model = vq.qubo_to_spin(q)
    good = fake_sampleset(q, model, all_bits(4)[:2], shuffle_labels=False)
    energies = list(good.record.energy)
    energies[1] -= model["offset"] or 1
    mixed = dimod.SampleSet.from_samples((good.record.sample, list(good.variables)), vartype="SPIN", energy=energies)
    with pytest.raises(ValueError, match="disagree"):
        vq.parse_samples(mixed, q, model)


class ExplodingSolver:
    def __init__(self, **kwargs):
        raise AssertionError("solver must not be constructed offline")


def test_solve_qubo_offline_gates(tmp_path, monkeypatch):
    monkeypatch.delenv("VELOX_TOKEN", raising=False)
    ledger = tmp_path / "ledger.json"
    config = {"ledger_path": str(ledger)}
    result = vq.solve_qubo(vq.SMOKE_BUNDLE, {}, config, tmp_path / "a", solver_factory=ExplodingSolver)
    assert result["status"] == "not_run" and "not allowed" in result["failure"]["reason"]
    allowed = {"allow_external_execution": True, "max_service_jobs": 5}
    result = vq.solve_qubo(vq.SMOKE_BUNDLE, allowed, config, tmp_path / "b", solver_factory=ExplodingSolver)
    assert result["status"] == "unavailable"
    monkeypatch.setenv("VELOX_TOKEN", "dummy-not-a-real-token")
    capped = {"allow_external_execution": True, "max_service_jobs": 0}
    result = vq.solve_qubo(vq.SMOKE_BUNDLE, capped, config, tmp_path / "c", solver_factory=ExplodingSolver)
    assert result["status"] == "not_run" and "cap" in result["failure"]["reason"]
    assert not ledger.exists()
    saved = json.loads((tmp_path / "c" / "result.json").read_text())
    assert "dummy-not-a-real-token" not in json.dumps(saved)


def test_method_result_schema_on_random_bit_fixture(tmp_path):
    bundle = random_bundle(6, 42)
    result = vq.solve_qubo(bundle, {}, {"ledger_path": str(tmp_path / "l.json")}, tmp_path)
    for field in ("schema_version", "method_id", "method_version", "case_id", "bundle_sha256", "representation_id",
                  "bundle", "execution_kind", "status", "samples", "configuration", "timings", "work", "environment",
                  "raw_artifacts", "failure", "reference", "veloxq_calls", "physical_qpu_calls"):
        assert field in result
    assert result["schema_version"] == "catering-method-result.v1"
    assert result["veloxq_calls"] == 0 and result["physical_qpu_calls"] == 0
    assert result["execution_kind"] == "veloxq_service"
    assert result["bundle"]["case_id"] == "random-6-42"
    assert result["representation"]["n"] == 6
    assert len(result["raw_artifacts"]["ising_input"]["sha256"]) == 64
    # Deterministic random-bit sample run through the parser, as the central runner would receive it.
    q = vq.load_qubo(bundle)
    model = vq.qubo_to_spin(q)
    rng = random.Random(7)
    rows = [[rng.randint(0, 1) for _ in range(6)] for _ in range(20)]
    samples, _ = vq.parse_samples(fake_sampleset(q, model, rows), q, model)
    assert all(len(s["bits"]) == 6 and set(s["bits"]) <= {0, 1} for s in samples)


class FakeJob:
    """Mimics veloxq_sdk Job: completes immediately and saves a VeloxQ-layout result file."""

    def __init__(self, q, model, rows, omit_offset, dtype=float):
        self.id, self.status, self.timeline = "job-fake-1", "completed", []
        self.q, self.model, self.rows, self.omit_offset, self.dtype = q, model, rows, omit_offset, dtype

        class Stats:
            def model_dump(self, mode=None):
                return {"total_quota_usage": 1, "running_time": 0.1}
        self.statistics = Stats()

    def refresh(self):
        pass

    def save_result(self, path):
        import h5py
        import numpy as np
        states = [[2 * b - 1 for b in bits] for bits in self.rows]
        energies = [vq.spin_energy(self.model, s) - (self.model["offset"] if self.omit_offset else 0) for s in states]
        with h5py.File(path, "w") as f:
            f["Spectrum/states"] = np.array(states, dtype=np.int8)
            f["Spectrum/energies"] = np.array(energies, dtype=self.dtype)
            f["Spectrum/metadata"] = json.dumps({"solver": "fake"})
            f["Spectrum/labels"] = np.array([str(i) for i in range(self.q["n"])], dtype=h5py.string_dtype())


@pytest.mark.parametrize("omit_offset", [False, True])
def test_solve_qubo_remote_path_with_fake_service(tmp_path, monkeypatch, omit_offset):
    from veloxq_sdk.api.problems import File

    monkeypatch.setenv("VELOX_TOKEN", "dummy-not-a-real-token")
    q = vq.load_qubo(vq.SMOKE_BUNDLE)
    model = vq.qubo_to_spin(q)
    uploads = []

    class FakeFile:
        id = "file-fake-1"

    monkeypatch.setattr(File, "from_path", classmethod(lambda cls, path, name=None, **kw: uploads.append(name) or FakeFile()))

    class FakeSolver:
        id = "solver-fake"

        def __init__(self, parameters, backend=None):
            self.parameters, self.backend = parameters, backend or type("VeloxQH100_1", (), {"id": "backend-fake"})()

        def submit(self, file):
            return FakeJob(q, model, [[1, 0], [1, 0], [0, 1], [1, 1]], omit_offset)

    ledger = tmp_path / "ledger.json"
    budget = {"allow_external_execution": True, "max_service_jobs": 1, "wall_time_limit_s": 10}
    config = {"ledger_path": str(ledger), "num_rep": 4, "num_steps": 10}
    result = vq.solve_qubo(vq.SMOKE_BUNDLE, budget, config, tmp_path / "run", solver_factory=FakeSolver)
    assert result["status"] == "completed", result["failure"]
    assert result["samples"][0]["bits"] == [1, 0] and result["samples"][0]["reported_energy"] == "-4"
    assert result["samples"][0]["count"] == 2
    assert result["work"]["service_jobs_submitted"] == 1
    assert result["backend_statistics"]["total_quota_usage"] == 1
    assert json.loads(ledger.read_text())["jobs"][0]["job_id"] == "job-fake-1"
    assert len(uploads) == 1
    # Second call is refused by the ledger cap, before any upload.
    again = vq.solve_qubo(vq.SMOKE_BUNDLE, budget, config, tmp_path / "run2", solver_factory=FakeSolver)
    assert again["status"] == "not_run" and len(uploads) == 1
    assert "dummy-not-a-real-token" not in (tmp_path / "run" / "result.json").read_text()


# Frozen foundation releases. Offline: no token, no network. v3 (paired meals) is the
# current input; v2 complete-qubo is the regression profile. v1 is superseded upstream.
V3 = vq.ROOT / "output/catering-foundation-v3"
CELL = vq.ROOT / "output/catering-complete-cell-v3/quantum-qubo.json"
V2 = vq.ROOT / "output/catering-foundation-v2"
# Gitignored; restored from output/compressed-evidence (scripts/restore-compressed-evidence.mjs).
SCALE = vq.ROOT / "output/catering-velox-scale-v3"
CASES = ("S0", "S1", "S2", "S3")
FROZEN = ([V3 / c / f"{k}-qubo.json" for c in CASES for k in ("quantum", "scale-128", "scale-256")]
          + [CELL] + [SCALE / f"scale-{w}-qubo.json" for w in (512, 1024, 2048)]
          + [V2 / c / "complete-qubo.json" for c in CASES])
FROZEN_IDS = [str(p.relative_to(vq.ROOT / "output")) for p in FROZEN]
needs_v3 = pytest.mark.skipif(not V3.exists(), reason="foundation v3 release not present")


def fake_service(monkeypatch, q, model, rows, omit_offset, dtype=float):
    from veloxq_sdk.api.problems import File

    monkeypatch.setenv("VELOX_TOKEN", "dummy-not-a-real-token")

    class FakeFile:
        id = "file-fake-1"

    monkeypatch.setattr(File, "from_path", classmethod(lambda cls, p, name=None, **kw: FakeFile()))

    class FakeSolver:
        id = "solver-fake"

        def __init__(self, parameters, backend=None):
            self.backend = type("VeloxQH100_1", (), {"id": "backend-fake"})()

        def submit(self, file):
            return FakeJob(q, model, rows, omit_offset, dtype)

    return FakeSolver


@pytest.mark.parametrize("path", FROZEN, ids=FROZEN_IDS)
def test_frozen_bundle_energies_match_foundation(path):
    if not path.exists():
        pytest.skip("release not present")
    from catering.contracts import load_bundle
    from catering.qubo import energy, ising

    bundle = load_bundle(path)
    q = vq.load_qubo(bundle)
    model = vq.qubo_to_spin(q)
    assert q["variable_order"] == bundle["variable_order"]
    assert vq.coefficient_report(q, model)["float64_exact"]
    assert vq._bundle_identity(bundle, q)["bundle_sha256"] == bundle["bundle_sha256"]
    rng = random.Random(str(path))
    for _ in range(100 if q["n"] <= 256 else 5):
        bits = [rng.randint(0, 1) for _ in range(q["n"])]
        expected = int(energy(bundle, bits))
        assert vq.qubo_energy(q, bits) == expected
        assert vq.spin_energy(model, [2 * b - 1 for b in bits]) == vq.SPIN_SCALE * expected
    # Foundation's Pauli-Z form (z = 1 - 2x = -s) also represents 4E: same constant, h flips sign, J does not.
    pauli = ising(bundle)
    assert pauli["convention"] == "z=1-2*x" and int(pauli["energy_scale"]) == vq.SPIN_SCALE
    assert int(pauli["constant"]) == model["offset"]
    assert [-int(v) for v in pauli["linear"]] == model["h"]
    assert {(t["i"], t["j"]): int(t["value"]) for t in pauli["quadratic"] if int(t["value"])} == model["J"]


@needs_v3
@pytest.mark.parametrize("case", CASES)
def test_v3_references_have_literal_energy(case):
    from catering.contracts import load_bundle

    for kind in ("quantum", "scale-128", "scale-256"):
        bundle = load_bundle(V3 / case / f"{kind}-qubo.json")
        q = vq.load_qubo(bundle)
        for control in ("reference", "sa"):
            payload = json.loads((V3 / case / f"{kind}-{control}.json").read_text())
            assert payload["bundle_sha256"] == bundle["bundle_sha256"]
            for sample in payload["samples"]:
                assert vq.qubo_energy(q, sample["bits"]) == int(sample["reported_energy"])


CLASSICAL_SCALE = vq.ROOT / "output/catering-classical-scale-v3"


@pytest.mark.parametrize("width", [512, 1024, 2048])
def test_classical_scale_controls_match_frozen_scale_bundles(width):
    path = SCALE / f"scale-{width}-qubo.json"
    if not path.exists() or not CLASSICAL_SCALE.exists():
        pytest.skip("scale matrices not restored or classical scale release missing")
    from catering.contracts import load_bundle

    bundle = load_bundle(path)
    q = vq.load_qubo(bundle)
    for control in ("reference", "sa"):
        payload = json.loads((CLASSICAL_SCALE / f"scale-{width}-{control}.json").read_text())
        assert payload["bundle_sha256"] == bundle["bundle_sha256"]
        for sample in payload["samples"]:
            assert vq.qubo_energy(q, sample["bits"]) == int(sample["reported_energy"])


@needs_v3
@pytest.mark.parametrize("omit_offset", [False, True])
def test_float32_energies_on_scale_256_are_accepted(omit_offset):
    # VeloxQ returns float32 energies; on scale-256 |E_spin| ~ 1e16, far beyond float32 integers.
    import numpy as np
    from catering.contracts import load_bundle

    bundle = load_bundle(V3 / "S1/scale-256-qubo.json")
    q = vq.load_qubo(bundle)
    model = vq.qubo_to_spin(q)
    assert vq.coefficient_report(q, model)["float32_inexact_spin_coefficients"] > 0
    rng = random.Random(5)
    rows = [[rng.randint(0, 1) for _ in range(q["n"])] for _ in range(8)]
    energies = [vq.spin_energy(model, [2 * b - 1 for b in r]) - (model["offset"] if omit_offset else 0) for r in rows]
    sampleset = dimod.SampleSet.from_samples(([[2 * b - 1 for b in r] for r in rows], list(range(q["n"]))),
                                             vartype="SPIN", energy=np.array(energies, dtype=np.float32))
    samples, info = vq.parse_samples(sampleset, q, model)
    assert info["returned_energy_dtype"] == "float32"
    assert info["energy_convention"] == ("Ising offset omitted by result" if omit_offset else "full model")
    assert info["max_convention_deviation"] <= info["convention_tolerance"]
    assert all(int(s["reported_energy"]) == vq.qubo_energy(q, s["bits"]) for s in samples)
    # A shift far beyond float32 rounding (1% of the L1 bound) is still rejected.
    shifted = dimod.SampleSet.from_samples(([[2 * b - 1 for b in r] for r in rows], list(range(q["n"]))),
                                           vartype="SPIN", energy=np.array(energies, dtype=np.float32)
                                           + np.float32(0.01 * vq.spin_l1(model)))
    with pytest.raises(ValueError, match="disagree"):
        vq.parse_samples(shifted, q, model)


@needs_v3
@pytest.mark.parametrize("kind,omit_offset", [("quantum", True), ("scale-256", True), ("scale-128", False)])
def test_fake_service_result_on_v3_bundle_passes_central_evaluate(tmp_path, monkeypatch, kind, omit_offset):
    import numpy as np
    from catering.contracts import load_bundle
    from catering.run import evaluate

    path = V3 / f"S1/{kind}-qubo.json"
    bundle = load_bundle(path)
    reference = json.loads((V3 / f"S1/{kind}-reference.json").read_text())
    sa = json.loads((V3 / f"S1/{kind}-sa.json").read_text())
    q = vq.load_qubo(bundle)
    model = vq.qubo_to_spin(q)
    rng = random.Random(3)
    rows = ([s["bits"] for s in reference["samples"]] + [s["bits"] for s in sa["samples"]]
            + [[rng.randint(0, 1) for _ in range(q["n"])] for _ in range(20)])
    solver = fake_service(monkeypatch, q, model, rows, omit_offset, dtype=np.float32)
    budget = {"allow_external_execution": True, "max_service_jobs": 1, "wall_time_limit_s": 10}
    config = {"ledger_path": str(tmp_path / "ledger.json")}
    result = vq.solve_qubo(bundle, budget, config, tmp_path / "run", solver_factory=solver)
    assert result["status"] == "completed", result["failure"]
    assert result["bundle_sha256"] == bundle["bundle_sha256"] and result["veloxq_calls"] == 1
    assert result["configuration"]["returned"]["returned_energy_dtype"] == "float32"
    assert result["samples"][0]["reported_energy"] == reference["samples"][0]["reported_energy"]
    evaluated = evaluate(path, tmp_path / "run" / "result.json", tmp_path / "evaluation.json")
    assert [r["energy"] for r in evaluated] == [s["reported_energy"] for s in result["samples"]]
    assert evaluated[0]["valid"]
    saved = json.loads((tmp_path / "evaluation.json").read_text())
    assert saved["repair"] is False and saved["method_id"] == "veloxq"


def test_warm_start_packet_uses_spin_and_exact_variable_order(tmp_path):
    import h5py
    import numpy as np
    q=vq.load_qubo(vq.SMOKE_BUNDLE);model=vq.qubo_to_spin(q)
    p=vq.write_packet(model,tmp_path/'warm.h5',initial_bits=[1,0],num_rep=3)
    with h5py.File(p,'r') as f:
        assert np.array_equal(f['Spectrum/states'][()],[[1,-1]]*3)
        assert f['Spectrum/num_rep'][()]==3
        assert np.array_equal(f['Spectrum/energies'][()],[vq.spin_energy(model,[1,-1])]*3)
    result=vq.solve_qubo(vq.SMOKE_BUNDLE,{},dict(initial_bits=[1,0],num_rep=3),tmp_path/'offline')
    assert result['status']=='not_run' and result['veloxq_calls']==0
    assert result['configuration']['initial_literal_energy']=='-4'
    assert result['configuration']['initializer_packet_roundtrip'] is True


@pytest.mark.parametrize('bits', [[0], [0,2], [True,0]])
def test_reject_bad_initializer(tmp_path,bits):
    model=vq.qubo_to_spin(vq.load_qubo(vq.SMOKE_BUNDLE))
    with pytest.raises(ValueError):vq.write_packet(model,tmp_path/'bad.h5',initial_bits=bits)


def test_reject_physically_invalid_catering_warm_start(tmp_path):
    from catering.contracts import load_bundle
    b=load_bundle('output/catering-complete-cell-v3/quantum-qubo.json')
    with pytest.raises(ValueError,match='independently feasible'):
        vq.solve_qubo(b,{},dict(initial_bits=[1]*35),tmp_path/'invalid')


def test_storage_download_uses_clean_client_and_atomic_file(tmp_path,monkeypatch):
    import httpx
    calls=[]
    class Response:
        text='"https://storage.example.test/result?signature=private"'
        def raise_for_status(self):pass
        def iter_bytes(self):yield b'checked';yield b'-result'
        def __enter__(self):return self
        def __exit__(self,*args):pass
    class API:
        def get(self,path):calls.append(('api',path));return Response()
    class Storage:
        def __init__(self,**kwargs):
            assert 'headers' not in kwargs and 'auth' not in kwargs
            calls.append(('clean',kwargs))
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def stream(self,method,url):
            assert method=='GET' and url.startswith('https://storage.example.test/')
            return Response()
    monkeypatch.setattr(httpx,'Client',Storage)
    vq.download_result(type('Job',(),dict(id='saved-job',http=API()))(),tmp_path/'result.h5')
    assert (tmp_path/'result.h5').read_bytes()==b'checked-result'
    assert not (tmp_path/'result.partial').exists()
    assert calls[0]==('api','jobs/saved-job/result')


@pytest.mark.parametrize('limit',[0,-1,float('nan'),float('inf')])
def test_refuse_unbounded_or_invalid_wall_budget(tmp_path,limit):
    with pytest.raises(ValueError,match='finite wall'):
        vq.solve_qubo(vq.SMOKE_BUNDLE,dict(wall_time_limit_s=limit),{},tmp_path/'run')
