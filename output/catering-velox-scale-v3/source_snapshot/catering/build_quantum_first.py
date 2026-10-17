"""Offline release of the quantum-first encoding and logical mixer audit.

Fixed-angle probes check circuit semantics. They are not trained QAOA results.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from .audit import audit_bundle
from .domain import fixture,snapshot
from .options import enumerate_options,restricted_pool
from .quantum_first import compile_unit_qubo,neighbor_masks,apply_conflict_mixer,compatibility_pool
from .native_slots import solve_native
from .decode import decode
from .qubo import ising
from .methods.classical import energy_chunks


def quantum_fixture():
    p = fixture()
    p["instance_id"] = "quantum-kitchen-four-lots-v2"
    p["previous_unstarted"] = [];p["urgent_groups"] = []
    p["menus"]["C"] = dict(yields=[1,2],prepare=10,cooking={"1":10,"2":20},
                          cook_attendance=10,pack_per_lot=10,clean=10,max_age=40)
    p["demand_groups"] = p["demand_groups"][:1]+[
        dict(id=f"{m}/{j}",menu=m,lots=1,departure=d,revealed=20,priority=1)
        for m,j,d in (("B",0,90),("B",1,110),("C",0,100),("C",1,110))]
    return p


def mixer_probe(bundle):
    n = bundle["size"]["binary_variables"]
    if n>20:
        raise ValueError("Logical probe limited to 20 data qubits")
    energies = np.empty(1<<n,dtype=np.int64)
    valid = np.empty(1<<n,dtype=bool)
    linear = np.array(list(map(int,bundle["objective"]["linear"])),dtype=np.int64)
    for masks,bits,e in energy_chunks(bundle):
        energies[masks] = e
        valid[masks] = e == bits@linear+int(bundle["objective"]["constant"])
    neighbors = neighbor_masks(bundle)
    scale = max(1,max(abs(int(c)) for c in bundle["linear"]),int(bundle["penalty"]))
    states = {name:np.zeros(1<<n,dtype=complex) for name in ("conflict-aware","ordinary-X")}
    for state in states.values():state[0] = 1
    layers = []
    for gamma,beta in ((0.29,0.37),(0.41,0.23)):
        phase = np.exp(-1j*gamma*(energies/scale))
        layer = dict(gamma=gamma,beta=beta,probabilities={})
        for name,state in states.items():
            states[name] = apply_conflict_mixer(state*phase,neighbors if name=="conflict-aware" else [0]*n,beta)
            probabilities = abs(states[name])**2
            layer["probabilities"][name] = dict(norm=float(probabilities.sum()),valid=float(probabilities[valid].sum()))
            if not np.isclose(probabilities.sum(),1,atol=1e-10):
                raise AssertionError("Nonunitary logical evolution")
            if name=="conflict-aware" and not np.isclose(probabilities[valid].sum(),1,atol=1e-10):
                raise AssertionError("Mixer leaked out of the certified feasible subspace")
        layers.append(layer)
    return dict(kind="Fixed-angle full-statevector invariant audit; not trained optimization",data_qubits=n,
                energy_scale=scale,layers=layers,valid_basis_states=int(valid.sum()),
                uniform_valid_probability=float(valid.mean()),
                max_neighbor_controls=max((m.bit_count() for m in neighbors),default=0),
                logical_controlled_rotations_per_layer=n,
                hardware_compilation="Not performed; controls, routing and ancillas must be costed separately",
                initial_state="All zero: no new batches, all residual demand explicitly missed")


def run(output):
    start = time.monotonic()
    output = Path(output)
    if output.exists():raise ValueError("Fresh output directory required")
    output.mkdir(parents=True)
    def save(name,value):
        (output/name).write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+"\n")
    p = quantum_fixture();s = snapshot(p,"S0")
    save("instance.json",p);save("snapshot.json",s)
    programs = enumerate_options(p,s)
    full = compile_unit_qubo(p,s,programs)
    save("complete-qubo.json",full)
    reference = solve_native(p,s,dict(wall_time_limit_s=10),dict(workers=1))
    save("raw-reference.json",reference)
    rows = []
    for cap in (8,12,16,20):
        b = compile_unit_qubo(p,s,compatibility_pool(p,programs,cap),
                             representation=f"unit-demand-cap{cap}",parent_sha256=full["bundle_sha256"])
        save(f"cap{cap}-qubo.json",b);save(f"cap{cap}-ising.json",ising(b))
        audit = audit_bundle(b)
        save(f"cap{cap}-audit.json",audit)
        selected = decode(b,audit["raw_enumeration"]["best_bits"])
        save(f"cap{cap}-exact-plan.json",selected)
        probe = mixer_probe(b)
        save(f"cap{cap}-mixer-probe.json",probe)
        row = dict(cap=cap,size=b["size"],restricted_optimum=selected["check"]["metrics"],
                   raw_reference_status=reference["reference_status"],
                   raw_reference_metrics=(reference["check"] or {}).get("metrics"),
                   retains_raw_optimum=reference["reference_status"]=="OPTIMAL" and selected["check"]["metrics"]==reference["check"]["metrics"],
                   mixer_probe=probe)
        rows.append(row)
        print(json.dumps(dict(cap=cap,metrics=row["restricted_optimum"],retains_raw_optimum=row["retains_raw_optimum"],
                              valid_states=probe["valid_basis_states"],max_controls=probe["max_neighbor_controls"])),flush=True)
    save("report.json",dict(schema_version="catering-quantum-first-design.v1",cases=rows,complete_size=full["size"],
                            pool_policy="Nested compatibility-count heuristic; no reference/optimum teacher",
                            total_s=time.monotonic()-start,physical_qpu_calls=0,veloxq_calls=0,
                            trained_quantum_results=False,main_workload_acceptance="Pending: train/test and routed circuit cost"))
    root = Path(__file__).resolve().parents[1]
    paths = ["catering/quantum_first.py","catering/build_quantum_first.py","catering/native_slots.py",
             "catering/domain.py","catering/check.py","catering/options.py","catering/qubo.py",
             "catering/audit.py","catering/decode.py","catering/contracts.py","catering/native.py",
             "catering/methods/classical.py","tests/catering/test_quantum_first.py"]
    save("manifest.json",dict(files={str(f.relative_to(output)):hashlib.sha256(f.read_bytes()).hexdigest()
                                      for f in sorted(output.glob("*.json"))},
                              sources={f:hashlib.sha256((root/f).read_bytes()).hexdigest() for f in paths}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    run(parser.parse_args().output)
