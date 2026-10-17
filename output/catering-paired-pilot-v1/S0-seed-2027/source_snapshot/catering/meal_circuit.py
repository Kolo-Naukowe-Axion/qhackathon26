"""Qiskit circuit export/audit for the exact meal-block sector simulator.

Local only: this module never creates a service/client or submits a QPU job.
"""
import argparse
import json
import math
from pathlib import Path


def circuit(bundle,params,incumbent_ids=(),exploration=0.15):
    from qiskit import QuantumCircuit
    qc=QuantumCircuit(bundle["size"]["binary_variables"])
    incumbent_ids=set(incumbent_ids)
    for group in bundle["onehot_groups"]:
        preferred=group["idle_index"]
        for i in group["program_indices"]:
            if bundle["options"][i]["id"] in incumbent_ids:preferred=i
        qc.x(preferred)
        remaining=1.;target=exploration/(len(group["indices"])-1)
        for other in group["indices"]:
            if other==preferred:continue
            angle=math.asin(math.sqrt(target/remaining))
            qc.rxx(angle,preferred,other);qc.ryy(angle,preferred,other)
            qc.s(other);remaining-=target
    scale=max(1,bundle["objective"]["weights"]["U"])
    for gamma_cost,gamma_conflict,beta in params:
        qc.global_phase-=gamma_cost*int(bundle["objective"]["constant"])/scale
        linear=[gamma_cost*int(c)/scale for c in bundle["objective"]["linear"]]
        pairs={}
        for t in bundle["objective"]["quadratic"]:
            pairs[(t["i"],t["j"])]=gamma_cost*int(t["value"])/scale
        for i,j in bundle["conflicts"]:pairs[(i,j)]=pairs.get((i,j),0)+gamma_conflict
        for i,a in enumerate(linear):
            if a:qc.rz(-a,i);qc.global_phase-=a/2
        for (i,j),a in sorted(pairs.items()):
            if a:
                qc.rz(-a/2,i);qc.rz(-a/2,j);qc.rzz(a/2,i,j);qc.global_phase-=a/4
        for group in bundle["onehot_groups"]:
            q=group["indices"]
            edges=list(zip(q[:-1],q[1:]))+([(q[-1],q[0])] if len(q)>2 else [])
            for i,j in edges:qc.rxx(beta,i,j);qc.ryy(beta,i,j)
    return qc


def audit(directory,output):
    from qiskit import transpile,qasm3
    from qiskit.transpiler import CouplingMap
    import qiskit
    directory,output=Path(directory),Path(output)
    if output.exists():raise ValueError("Fresh circuit audit output required")
    bundle=json.loads((directory/"qubo.json").read_text())
    training=json.loads((directory/"training.json").read_text())
    # Steps beyond zero need the exact warm-start identities. They are stored
    # separately by the search runner, not inferred from an optimal reference.
    warm=json.loads((directory/"warm-start.json").read_text())
    logical=circuit(bundle,training["parameters"],warm["incumbent_program_ids"])
    native=transpile(logical,basis_gates=["rz","sx","x","cx"],optimization_level=2,seed_transpiler=2026)
    coupling=CouplingMap.from_heavy_hex(5,bidirectional=True)
    routed=transpile(logical,basis_gates=["rz","sx","x","cx"],coupling_map=coupling,
                     optimization_level=2,seed_transpiler=2026)
    output.mkdir(parents=True)
    def info(qc):
        return dict(qubits=qc.num_qubits,depth=qc.depth(),cx=int(qc.count_ops().get("cx",0)),
                    two_qubit_depth=qc.depth(lambda instruction:len(instruction.qubits)==2),
                    operation_counts={str(k):int(v) for k,v in qc.count_ops().items()})
    report=dict(kind="Offline circuit compilation; synthetic topology, not a live IBM backend",
                bundle_sha256=bundle["bundle_sha256"],qiskit=qiskit.__version__,logical=info(logical),
                all_to_all_native=info(native),synthetic_heavy_hex=info(routed),
                topology=dict(kind="heavy_hex_distance_5",qubits=coupling.size()),
                physical_qpu_calls=0,veloxq_calls=0,
                limitation="No calibrated device/noise/runtime estimate; gate/depth counts are not a hardware success prediction")
    for name,qc in (("logical",logical),("all-to-all-native",native),("synthetic-heavy-hex",routed)):
        (output/(name+".qasm")).write_text(qasm3.dumps(qc))
    (output/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--step",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();print(json.dumps(audit(a.step,a.output)))
