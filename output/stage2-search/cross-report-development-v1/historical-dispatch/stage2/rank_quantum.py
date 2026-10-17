"""Isolated QAOA simulation of the certified four-bit baseline-B deadline QUBO.

No Stage 1 selected artifact is changed. No physical quantum job is submitted.
The action-selection feasibility API is intentionally not reused: rank bits
are decoded as machine orders, and deadline success is independently checked.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import random
from statistics import mean
import time

from .quantum import _optimize, circuit_metadata, statevector
from .rank_probe import earliest_schedule
from solver.stage1 import exact_reference, validate


ROOT=Path(__file__).resolve().parents[1]


@dataclass
class RankEnergy:
    """Energy-only adapter; it never inherits action-core feasibility semantics."""
    linear:list
    quadratic:dict
    offset:int

    @property
    def size(self):return len(self.linear)

    def energy(self,bits):
        if len(bits)!=self.size or any(bit not in (0,1) for bit in bits):
            raise ValueError("One binary value per rank variable required")
        return self.offset+sum(a*b for a,b in zip(self.linear,bits))+sum(value*bits[i]*bits[j] for (i,j),value in self.quadratic.items())


def sha256(data):return hashlib.sha256(data).hexdigest()


def canonical_digest(data):return sha256(json.dumps(data,sort_keys=True,separators=(",",":")).encode())


def expand_bits(model,bits):
    groups=model["decoder"]["equal_variable_groups"]
    constants={int(i):int(value) for i,value in model["decoder"].get("forced_constants",{}).items()}
    if len(bits)!=len(groups) or any(bit not in (0,1) for bit in bits):raise ValueError("Wrong reduced rank sample")
    full=[None]*9
    for bit,value in constants.items():full[bit]=value
    for reduced,group in enumerate(groups):
        for old in group:
            if full[old] is not None:raise ValueError("Decoder assigns an original bit twice")
            full[old]=bits[reduced]
    if any(value is None for value in full):raise ValueError("Decoder does not cover all original order bits")
    return full


def classify_basis(model,instance):
    q=RankEnergy(model["linear"],{(i,j):value for i,j,value in model["quadratic"]},model["offset"])
    if q.size!=4 or len(model["variables"])!=4:raise ValueError("This candidate experiment expects four rank variables")
    if canonical_digest(instance)!=model["instance_sha256"]:raise ValueError("Instance digest does not match the certified rank model")
    rows=[]
    for state in range(1<<q.size):
        bits=[(state>>i)&1 for i in range(q.size)]
        full=expand_bits(model,bits)
        decoded=earliest_schedule(instance,full)
        errors=None if decoded is None else validate(instance,decoded["schedule"],decoded["makespan"])
        physical=decoded is not None and not errors
        deadline=physical and decoded["makespan"]<=model["horizon"]
        energy=q.energy(bits)
        if (energy==0)!=deadline or energy<0:raise AssertionError("Rank model fails independently decoded deadline equivalence")
        rows.append(dict(state=state,bitstring=format(state,f"0{q.size}b"),bits=bits,expanded_order_bits=full,
            energy=energy,physical_schedule_valid=physical,deadline_success=deadline,
            makespan=None if decoded is None else decoded["makespan"],
            schedule=None if decoded is None else decoded["schedule"],official_validator_errors=errors))
    if sum(row["deadline_success"] for row in rows)!=5:raise AssertionError("Not all five certified schedules retained")
    return q,rows


def run_candidate(model,instance,*,layers,seed,shots=1024,max_evaluations=512,restarts=4):
    from qiskit import QuantumCircuit,transpile
    from qiskit.quantum_info import Statevector
    from qiskit_aer import AerSimulator
    started=time.perf_counter()
    q,rows=classify_basis(model,instance)
    probabilities,optimization=_optimize(q,layers,seed,max_evaluations,restarts,"coordinate")
    metadata=circuit_metadata(q,optimization["gamma"],optimization["beta"],optimization["cost_scale"])
    circuit=QuantumCircuit.from_qasm_str(metadata["openqasm2"])
    unmeasured=circuit.remove_final_measurements(inplace=False)
    independent=Statevector.from_instruction(unmeasured).probabilities()
    pure=statevector(q,optimization["gamma"],optimization["beta"],optimization["cost_scale"])
    difference=max(abs(abs(amplitude)**2-prob) for amplitude,prob in zip(pure,independent))
    if difference>1e-12 or max(abs(a-b) for a,b in zip(probabilities,independent))>1e-12:
        raise AssertionError("Independent Qiskit circuit probabilities disagree with exact simulator")
    simulator=AerSimulator(method="statevector",seed_simulator=seed)
    compiled=transpile(circuit,simulator,optimization_level=0,seed_transpiler=seed)
    counts={bitstring.replace(" ",""):int(count) for bitstring,count in simulator.run(compiled,shots=shots).result().get_counts().items()}
    if sum(counts.values())!=shots:raise AssertionError("Incomplete measured shot counts")
    # Every observed bitstring is independently expanded, scheduled and checked.
    samples=[]
    for bitstring,count in sorted(counts.items()):
        state=int(bitstring,2);row=rows[state]
        if [int(value) for value in bitstring[::-1]]!=row["bits"]:raise AssertionError("Bit-order mismatch")
        samples.append(dict(count=count,**row))
    best=min(samples,key=lambda row:(row["energy"],-row["count"],row["state"]))
    uniform_rng=random.Random(seed^0x51D3)
    uniform_counts=Counter(uniform_rng.randrange(1<<q.size) for _ in range(shots))
    uniform_best=min(uniform_counts,key=lambda state:(rows[state]["energy"],-uniform_counts[state],state))
    ground=[row["state"] for row in rows if row["deadline_success"]]
    ideal=sum(probabilities[state] for state in ground)
    uniform=len(ground)/(1<<q.size)
    histogram=Counter()
    for row in samples:histogram[str(row["makespan"]) if row["makespan"] is not None else "cyclic_order"]+=row["count"]
    metadata.update(qiskit_unmeasured_depth=unmeasured.depth(),
        qiskit_unmeasured_gate_counts=dict(unmeasured.count_ops()),
        aer_compiled_depth=compiled.depth(),aer_compiled_gate_counts=dict(compiled.count_ops()))
    return dict(schema="stage2-rank-qaoa-candidate.v1",model_encoding=model["encoding"],
        logical_qubits=q.size,layers=layers,seed=seed,shots=shots,
        simulation_backend="Qiskit Aer statevector + measurement shots",
        quantum_algorithm_simulated=True,physical_quantum_executed=False,
        circuit=metadata,optimization=optimization,
        independent_qiskit_crosscheck=dict(maximum_probability_error=difference,tolerance=1e-12,passed=True),
        exact_basis_audit=rows,raw_counts=counts,samples=samples,
        ideal_basis_probabilities=probabilities,
        ideal_deadline_ground_probability=ideal,
        ideal_physical_schedule_probability=sum(probabilities[row["state"]] for row in rows if row["physical_schedule_valid"]),
        sampled_deadline_success_fraction=sum(row["count"] for row in samples if row["deadline_success"])/shots,
        sampled_makespan_histogram=dict(histogram),
        selected_sample=dict(best,selection_rule="minimum observed QUBO energy; ties by count then basis index"),
        uniform_reference=dict(ideal_deadline_ground_probability=uniform,
            probability_at_least_one_ground_in_equal_shots=1-(1-uniform)**shots,
            log10_probability_no_ground_in_equal_shots=shots*math.log10(1-uniform),
            raw_counts={format(state,"04b"):count for state,count in sorted(uniform_counts.items())},
            sampled_ground_fraction=sum(count for state,count in uniform_counts.items() if rows[state]["deadline_success"])/shots,
            selected_basis_state=uniform_best,selected_energy=rows[uniform_best]["energy"],
            selected_makespan=rows[uniform_best]["makespan"]),
        preprocessing=model["construction"],elapsed_seconds=time.perf_counter()-started,
        limitations=["This is classical simulation of a genuine QAOA gate circuit; no physical ODRA5 execution occurred.",
            "Exact classical structural/SAT preprocessing is required and disclosed; it can itself find satisfying assignments.",
            "All sixteen basis energies are classically evaluated for simulation and validation.",
            "Equal-shot uniform sampling also almost certainly finds a ground state at 1024 shots; best observed makespan is not speedup evidence.",
            "Qubit-count fit does not certify native hardware connectivity, routed depth, calibration or noise tolerance."])


def experiment(output,seeds=(2026,17,83),shots=1024,max_evaluations=512,restarts=4):
    import qiskit,qiskit_aer
    output=Path(output)
    if output.exists() and any(output.iterdir()):raise ValueError("Use a new empty candidate output directory")
    output.mkdir(parents=True,exist_ok=True)
    source_paths={"sat_only":ROOT/"output/stage2-search/rank-probe/sat-only-final/structural-four-bit-model.json",
                  "sparse_optional_lp":ROOT/"output/stage2-search/rank-probe/structural-final/structural-four-bit-model.json"}
    instance_path=ROOT/"instances/instance_3x3.json"
    instance=json.loads(instance_path.read_text())
    reference_started=time.perf_counter();reference=exact_reference(instance)
    reference_seconds=time.perf_counter()-reference_started
    if reference["makespan"]!=8 or validate(instance,reference["schedule"],8):raise AssertionError("Official instance reference failed")
    source_files=["stage2/rank_quantum.py","stage2/rank_probe.py","stage2/quantum.py","solver/stage1.py"]
    provenance=dict(created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
        source_sha256={name:sha256((ROOT/name).read_bytes()) for name in source_files},
        instance_sha256=canonical_digest(instance),qiskit_version=qiskit.__version__,qiskit_aer_version=qiskit_aer.__version__,
        instance_reference_enumeration_seconds=reference_seconds,
        disclosure="Isolated research candidate; no official Stage1 selected artifact or QPU job changed")
    (output/"instance.json").write_text(json.dumps(instance,indent=2)+"\n")
    (output/"provenance.json").write_text(json.dumps(provenance,indent=2)+"\n")
    (output/"exact-classical-reference.json").write_text(json.dumps(reference,indent=2)+"\n")
    summaries=[]
    for variant,model_path in source_paths.items():
        model=json.loads(model_path.read_text());variant_dir=output/variant;variant_dir.mkdir()
        (variant_dir/"source-model.json").write_bytes(model_path.read_bytes())
        certificate=model_path.parent/"report.json"
        (variant_dir/"source-certificate.json").write_bytes(certificate.read_bytes())
        model_provenance=dict(source_path=str(model_path),source_sha256=sha256(model_path.read_bytes()),
            certificate_path=str(certificate),certificate_sha256=sha256(certificate.read_bytes()))
        (variant_dir/"model-provenance.json").write_text(json.dumps(model_provenance,indent=2)+"\n")
        for layers in (1,2):
            for seed in seeds:
                result=run_candidate(model,instance,layers=layers,seed=seed,shots=shots,
                                     max_evaluations=max_evaluations,restarts=restarts)
                result["provenance"]={**provenance,**model_provenance}
                run_dir=variant_dir/f"p{layers}-seed{seed}";run_dir.mkdir()
                (run_dir/"result.json").write_text(json.dumps(result,indent=2)+"\n")
                (run_dir/"raw-counts.json").write_text(json.dumps(result["raw_counts"],indent=2)+"\n")
                (run_dir/"circuit.qasm").write_text(result["circuit"]["openqasm2"])
                (run_dir/"selected-schedule.json").write_text(json.dumps(dict(problem="erp_scheduling",makespan=result["selected_sample"]["makespan"],schedule=result["selected_sample"]["schedule"]),indent=2)+"\n")
                summaries.append(dict(variant=variant,layers=layers,seed=seed,
                    ideal_ground_probability=result["ideal_deadline_ground_probability"],
                    sampled_ground_fraction=result["sampled_deadline_success_fraction"],
                    uniform_ideal_ground_probability=result["uniform_reference"]["ideal_deadline_ground_probability"],
                    uniform_sampled_ground_fraction=result["uniform_reference"]["sampled_ground_fraction"],
                    selected_energy=result["selected_sample"]["energy"],selected_makespan=result["selected_sample"]["makespan"],
                    official_validator_errors=result["selected_sample"]["official_validator_errors"],
                    qiskit_probability_error=result["independent_qiskit_crosscheck"]["maximum_probability_error"],
                    logical_depth=result["circuit"]["logical_depth_without_measurement"],
                    cx_gates=result["circuit"]["gate_counts"].get("cx",0),
                    optimization_evaluations=result["optimization"]["evaluations"],
                    elapsed_seconds=result["elapsed_seconds"],path=str(run_dir)))
    aggregate=[]
    for variant in source_paths:
        for layers in (1,2):
            rows=[row for row in summaries if row["variant"]==variant and row["layers"]==layers]
            aggregate.append(dict(variant=variant,layers=layers,seeds=list(seeds),
                mean_ideal_ground_probability=mean(row["ideal_ground_probability"] for row in rows),
                min_ideal_ground_probability=min(row["ideal_ground_probability"] for row in rows),
                max_ideal_ground_probability=max(row["ideal_ground_probability"] for row in rows),
                mean_sampled_ground_fraction=mean(row["sampled_ground_fraction"] for row in rows),
                uniform_ground_probability=5/16,all_selected_makespan_eight=all(row["selected_makespan"]==8 and not row["official_validator_errors"] for row in rows)))
    report=dict(schema="stage2-rank-qaoa-experiment.v1",logical_qubits=4,shots_per_run=shots,
        max_angle_evaluations_per_run=max_evaluations,angle_restarts=restarts,
        model_variants=2,layers=[1,2],seeds=list(seeds),runs=summaries,aggregate=aggregate,
        provenance=provenance,physical_quantum_executed=False,no_quantum_speedup_claim=True)
    (output/"summary.json").write_text(json.dumps(report,indent=2)+"\n")
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=ROOT/"output/stage2-search/rank-quantum")
    parser.add_argument("--shots",type=int,default=1024)
    parser.add_argument("--seeds",default="2026,17,83")
    parser.add_argument("--evaluations",type=int,default=512)
    parser.add_argument("--restarts",type=int,default=4)
    args=parser.parse_args()
    if args.shots<1 or args.evaluations<8 or args.restarts<1:parser.error("Positive shots/restarts and >=8 evaluations required")
    report=experiment(args.output,seeds=tuple(int(value) for value in args.seeds.split(",")),
                      shots=args.shots,max_evaluations=args.evaluations,restarts=args.restarts)
    print(json.dumps(report["aggregate"],indent=2))


if __name__=="__main__":main()
