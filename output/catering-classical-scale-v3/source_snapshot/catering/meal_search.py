"""Quantum-led bounded-width search over the full local-program domain.

Classical code enumerates legal *local* programs, changes a portfolio, tunes
angles and checks quantum samples. It never solves/repairs a kitchen plan.
CP and exact sector minima are evaluation references, not plan teachers.
"""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import platform
import shutil
import time

import numpy as np

from .domain import snapshot,make_plan,digest
from .check import check_plan
from .options import enumerate_options
from .meal_blocks import meal_fixture,compile_meal_blocks,sector_data,sector_bits,xy_mix
from .decode import decode
from .qubo import energy,objective_energy,ising
from .native_slots import solve_native
from .paired_meals import active_meals
from .options import claims,conflict


def portfolio(programs,incumbent,extra_choices,rng,instance=None,state=None):
    by_anchor=defaultdict(list)
    for p in programs:by_anchor[min(p["allocation_order"])].append(p)
    selected={p["id"]:p for p in incumbent}
    if instance is not None and extra_choices>=2:
        # Local two-course support, not a whole-kitchen teacher: propose up to
        # extra_choices/2 compatible main/side pairs. They may conflict with
        # every other proposal or incumbent; quantum chooses the combination.
        cover=defaultdict(list)
        retimings=defaultdict(list)
        for p in programs:
            for g in p["allocation_order"]:cover[g].append(p)
            retimings[(p["menu"],p["yield_lots"],tuple(p["allocation_order"]))].append(p)
        committed={g for p in state["fixed_batches"] for g in p["allocation_order"]}
        meals=list(active_meals(instance,state));rng.shuffle(meals)
        already=committed|{g for p in incumbent for g in p["allocation_order"]}
        meals.sort(key=lambda m:m["main"] in already and m["side"] in already)
        proposed=0
        for meal in meals:
            left=[None] if meal["main"] in committed else cover[meal["main"]]
            right=[None] if meal["side"] in committed else cover[meal["side"]]
            if not left or not right:continue
            for _ in range(32):
                p=left[int(rng.integers(len(left)))];q=right[int(rng.integers(len(right)))]
                if p is not None and q is not None and conflict(claims(instance,p),claims(instance,q)):continue
                proposed_values=[v for v in (p,q) if v is not None]
                # Supply local retiming support for old batches that clash
                # with this proposal. Each replacement is tested only against
                # the proposed pair, never against all other replacements.
                # Their global compatibility remains the quantum decision.
                for old in incumbent:
                    if not any(conflict(claims(instance,old),claims(instance,v)) for v in proposed_values[:2]):continue
                    candidates=[v for v in retimings[(old["menu"],old["yield_lots"],tuple(old["allocation_order"]))]
                                if all(not conflict(claims(instance,v),claims(instance,target)) for target in (p,q) if target is not None)]
                    # If no retiming exists, the proposal can still be useful:
                    # the quantum choice may drop the old batch using idle.
                    if not candidates:continue
                    proposed_values.append(candidates[int(rng.integers(len(candidates)))])
                prospective=dict(selected)
                for value in proposed_values:prospective[value["id"]]=value
                multiplicities=defaultdict(int)
                for value in prospective.values():multiplicities[min(value["allocation_order"])]+=1
                if sum(max(0,n-1) for n in multiplicities.values())>extra_choices:continue
                for value in proposed_values:
                    if value is not None:selected[value["id"]]=value
                proposed+=1;break
            if proposed>=extra_choices//2:break
    counts=defaultdict(int)
    for p in selected.values():counts[min(p["allocation_order"])]+=1
    # At least one alternative at every nonempty anchor, then diversify a
    # seeded subset of anchors. Incumbent batch choices are never dropped.
    for anchor,values in sorted(by_anchor.items()):
        if counts[anchor]==0:
            p=values[int(rng.integers(len(values)))];selected[p["id"]]=p;counts[anchor]+=1
    anchors=list(sorted(by_anchor));rng.shuffle(anchors)
    target=len(by_anchor)+extra_choices
    for anchor in anchors:
        if len(selected)>=target:break
        candidates=[p for p in by_anchor[anchor] if p["id"] not in selected]
        if candidates:
            p=candidates[int(rng.integers(len(candidates)))];selected[p["id"]]=p
    return sorted(selected.values(),key=lambda p:p["id"])


def warm_state(bundle,sector,incumbent_ids,exploration=0.15):
    state=np.ones(sector["states"],dtype=complex)
    for axis,g in enumerate(bundle["onehot_groups"]):
        preferred=len(g["indices"])-1
        for j,i in enumerate(g["program_indices"]):
            if bundle["options"][i]["id"] in incumbent_ids:preferred=j
        amplitudes=np.full(len(g["indices"]),math.sqrt(exploration/(len(g["indices"])-1)))
        amplitudes[preferred]=math.sqrt(1-exploration)
        state*=amplitudes[sector["choices"][:,axis]]
    return state


def evolve(initial,sector,params,scale):
    state=initial.copy()
    for gamma_cost,gamma_conflict,beta in params:
        # One-hot penalties vanish in this invariant sector. Independent phase
        # angles are an explicitly multi-angle QAOA ansatz, not a changed QUBO.
        phase=gamma_cost*(sector["objective"]/scale)+gamma_conflict*sector["violations"]
        state=xy_mix(state*np.exp(-1j*phase),sector["dims"],beta)
    return state


def cvar(probabilities,energies,order,alpha=0.1):
    mass=probabilities[order];before=np.cumsum(mass)-mass
    taken=np.minimum(mass,np.maximum(0,alpha-before))
    return float(taken@energies[order]/alpha)


def train(bundle,sector,initial,rng,evaluations=16,depth=1):
    order=np.argsort(sector["energy"],kind="stable")
    scale=max(1,bundle["objective"]["weights"]["U"])
    best=None;best_control=None;trace=[]
    for j in range(evaluations):
        params=[(float(rng.uniform(0,2*np.pi)),float(rng.uniform(0,2*np.pi)),float(rng.uniform(-0.65,0.65)))
                for _ in range(depth)]
        state=evolve(initial,sector,params,scale);prob=abs(state)**2
        control_params=[(0.,0.,b) for _,_,b in params]
        control=evolve(initial,sector,control_params,scale);control_prob=abs(control)**2
        loss=cvar(prob,sector["energy"],order)
        control_loss=cvar(control_prob,sector["energy"],order)
        trace.append(dict(evaluation=j,params=params,cvar=loss,mixer_only_cvar=control_loss))
        if best is None or loss<best[0]:best=(loss,params,state)
        if best_control is None or control_loss<best_control[0]:best_control=(control_loss,control_params,control)
    return best,best_control,trace


def distribution_stats(state,sector):
    p=abs(state)**2
    target=(sector["energy"]==sector["energy"].min())
    return dict(norm=float(p.sum()),physical_valid_probability=float(p[sector["valid"]].sum()),
                encoded_ground_probability=float(p[target].sum()),expected_literal_energy=float(p@sector["energy"]))


def sample_result(bundle,sector,state,rng,shots):
    p=abs(state)**2;p/=p.sum()
    indices,counts=np.unique(rng.choice(sector["states"],size=shots,p=p),return_counts=True)
    samples=[];winner=None;valid_shots=0
    for index,count in zip(indices,counts):
        bits=sector_bits(bundle,sector,int(index));checked=decode(bundle,bits)
        literal=energy(bundle,bits)
        if literal!=int(sector["energy"][index]):raise AssertionError("Literal/sector mismatch")
        samples.append(dict(bits=bits,count=int(count),reported_energy=str(literal)))
        if checked["valid"]:
            valid_shots+=int(count)
            score=tuple(checked["check"]["metrics"][k] for k in ("U","W","B","R"))
            if winner is None or score<winner[0]:winner=(score,checked)
    return dict(samples=samples,valid_shots=valid_shots,shots=shots),winner


def circuit_resources(bundle):
    groups=bundle["onehot_groups"]
    xy=sum(len(g["indices"]) if len(g["indices"])>2 else 1 for g in groups)
    # A term may contain both objective and conflict contributions; combine it
    # for a tied-angle circuit, or use two rotations for independent phase angles.
    return dict(data_qubits=bundle["size"]["binary_variables"],ancilla_qubits=0,
                idle_data_qubits=len(groups),xy_two_qubit_rotations_per_mixer_layer=xy,
                controlled_neighbor_rotations=0,
                linear_cost_phase_terms=sum(int(x)!=0 for x in bundle["objective"]["linear"]),
                quadratic_cost_phase_terms=len(bundle["objective"]["quadratic"]),
                conflict_phase_terms=len(bundle["conflicts"]),
                state_preparation=dict(x_gates=len(groups),xy_rotations=sum(len(g["indices"])-1 for g in groups),
                                       single_qubit_phase_corrections=sum(len(g["indices"])-1 for g in groups)),
                hardware_status="Logical operations only; native decomposition/routing/noise not yet measured")


def run(output,customers=4,scenario="S3",steps=6,evaluations=16,shots=2048,seed=2026,extra_choices=6,reference_seconds=5,max_qubits=35):
    if min(customers,steps,evaluations,shots)<1 or extra_choices<0:
        raise ValueError("Positive customers/steps/evaluations/shots and nonnegative extra choices required")
    output=Path(output)
    if output.exists():raise ValueError("Fresh output directory required")
    output.mkdir(parents=True);started=time.monotonic()
    def save(path,value):
        target=output/path;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+"\n")
    instance=meal_fixture(customers);state=snapshot(instance,scenario)
    save("instance.json",instance);save("snapshot.json",state)
    before=time.monotonic();programs=enumerate_options(instance,state);generation_s=time.monotonic()-before
    anchor_count=len({min(p["allocation_order"]) for p in programs})
    if 2*anchor_count>max_qubits:
        raise ValueError("All-anchor portfolio exceeds the declared qubit cap; use a smaller case or implement an explicitly conditional neighborhood")
    extra_choices=min(extra_choices,max_qubits-2*anchor_count)
    domain_sha=digest([p["id"] for p in programs]);incumbent=[];rows=[]
    fixed=state["fixed_batches"]
    current=check_plan(instance,state,make_plan(instance,fixed,state.get("recovery_operations",[])))
    incumbent_score=tuple(current["metrics"][k] for k in ("U","W","B","R"))
    save("initial-plan.json",dict(plan=make_plan(instance,fixed,state.get("recovery_operations",[])),check=current))
    rng=np.random.default_rng(seed)
    for step in range(steps):
        begin=time.monotonic();pool=portfolio(programs,incumbent,extra_choices,rng,instance,state)
        bundle=compile_meal_blocks(instance,state,pool,parent_domain_sha256=domain_sha)
        if bundle["size"]["binary_variables"]>max_qubits:raise AssertionError("Circuit qubit cap exceeded")
        sector=sector_data(bundle)
        before_score=incumbent_score
        warm_ids=sorted(p["id"] for p in incumbent)
        initial=warm_state(bundle,sector,set(warm_ids))
        best,control,trace=train(bundle,sector,initial,rng,evaluations=evaluations)
        selected_state=best[2]
        measured,winner=sample_result(bundle,sector,selected_state,rng,shots)
        controls={}
        for name,vector in (("initializer",initial),("best-mixer-only",control[2])):
            control_samples,control_winner=sample_result(bundle,sector,vector,rng,shots)
            controls[name]=dict(distribution=distribution_stats(vector,sector),
                                best_metrics=None if control_winner is None else control_winner[1]["check"]["metrics"],
                                **control_samples)
        accepted=winner is not None and winner[0]<incumbent_score
        if accepted:
            incumbent_score=winner[0]
            fixed_ids={p["id"] for p in fixed}
            incumbent=[p for p in winner[1]["plan"]["batches"] if p["id"] not in fixed_ids]
        # Exact sector minimum is evaluated only after training/sampling. It is
        # never used as an initializer, candidate, optimizer parameter or update.
        exact=decode(bundle,sector_bits(bundle,sector,int(sector["energy"].argmin())))
        if not exact["valid"]:raise AssertionError("Encoded ground state is not physically valid")
        incumbent_bits=[0]*bundle["size"]["binary_variables"]
        for g in bundle["onehot_groups"]:
            selected=[i for i in g["program_indices"] if bundle["options"][i]["id"] in {p["id"] for p in incumbent}]
            incumbent_bits[selected[0] if selected else g["idle_index"]]=1
        if not decode(bundle,incumbent_bits)["valid"]:raise AssertionError("Incumbent was lost from its own portfolio")
        directory=Path(f"step-{step:02d}")
        save(directory/"qubo.json",bundle);save(directory/"ising.json",ising(bundle))
        save(directory/"warm-start.json",dict(incumbent_program_ids=warm_ids,exploration=0.15))
        save(directory/"training.json",dict(evaluations=evaluations,depth=1,loss="CVaR alpha=0.1 of literal QUBO energy",trace=trace,
                                           parameters=best[1],control_parameters=control[1],scale=bundle["objective"]["weights"]["U"]))
        save(directory/"samples.json",dict(schema_version="catering-method-result.v1",method_id="block_xy_multiangle_qaoa_pilot",
             case_id=bundle["case_id"],bundle_sha256=bundle["bundle_sha256"],representation_id=bundle["representation_id"],
             execution_kind="quantum_simulator",configuration=dict(seed=seed,step=step,depth=1,repair=False),**measured))
        save(directory/"controls.json",controls)
        save(directory/"exact-sector-reference.json",exact)
        row=dict(step=step,before_metrics=dict(zip(("U","W","B","R"),before_score)),
                 after_metrics=dict(zip(("U","W","B","R"),incumbent_score)),accepted=accepted,
                 best_quantum_sample_metrics=None if winner is None else winner[1]["check"]["metrics"],
                 exact_portfolio_metrics=exact["check"]["metrics"],sector_states=sector["states"],
                 physically_feasible_sector_states=int(sector["valid"].sum()),resources=circuit_resources(bundle),
                 distribution=distribution_stats(selected_state,sector),
                 controls={name:{k:v for k,v in value.items() if k!="samples"} for name,value in controls.items()},
                 total_s=time.monotonic()-begin)
        rows.append(row);save(directory/"summary.json",row)
        print(json.dumps({k:row[k] for k in ("step","before_metrics","after_metrics","accepted","sector_states","physically_feasible_sector_states","total_s")}),flush=True)
    plan=make_plan(instance,fixed+incumbent,state.get("recovery_operations",[]));checked=check_plan(instance,state,plan)
    save("quantum-plan.json",dict(plan=plan,check=checked))
    # Evaluation oracle comes last. It cannot guide the quantum trajectory.
    reference=solve_native(instance,state,dict(wall_time_limit_s=reference_seconds),dict(workers=4,seed=seed))
    save("raw-reference.json",reference)
    report=dict(schema_version="catering-quantum-meals-pilot.v1",profile_id=instance["profile_id"],scenario=scenario,
                customers=customers,initial_metrics=current["metrics"],final_metrics=checked["metrics"],steps=rows,
                full_local_program_count=len(programs),full_local_domain_sha256=domain_sha,generation_s=generation_s,
                reference_status=reference["reference_status"],reference_metrics=(reference["check"] or {}).get("metrics"),
                reference_timing=reference["timings"],seed=seed,total_s=time.monotonic()-started,
                qubit_cap=max_qubits,extra_choices=extra_choices,
                preprocessing="Local main/side compatibility proposals and independent retiming support; no complete-plan optimizer",
                physical_qpu_calls=0,veloxq_calls=0,
                limitations=["Exact invariant one-hot sector simulation; physical qubit counts are not compressed to log sector dimension",
                             "Multi-angle block-QAOA pilot, not a hardware result or a quantum/classical advantage claim",
                             "Per-portfolio controls share the quantum incumbent/input; they are not independent full-search controllers",
                             "Single training/sample seed is exploratory; held-out cases and repeats remain required",
                             "Portfolio restrictions vary each step; incumbent preservation does not prove global convergence",
                             "Fixed recovery-clean policy; no interrupted-batch/aggregate-capacity/monetary extension"])
    save("report.json",report)
    root=Path(__file__).resolve().parents[1]
    sources=[str(p.relative_to(root)) for p in sorted((root/"catering").rglob("*.py"))]
    for name in sources:
        target=output/"source_snapshot"/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(root/name,target)
    save("environment.json",dict(python=platform.python_version(),numpy=np.__version__,machine=platform.machine(),
                                 kind="Local CPU exact one-hot-sector simulator; no QPU or GPU used"))
    save("manifest.json",dict(files={str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.rglob("*")) if p.is_file()},
                              sources={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in sources}))
    return report


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True);parser.add_argument("--customers",type=int,default=4)
    parser.add_argument("--scenario",choices=("S0","S1","S2","S3"),default="S3")
    parser.add_argument("--steps",type=int,default=6);parser.add_argument("--evaluations",type=int,default=16)
    parser.add_argument("--shots",type=int,default=2048);parser.add_argument("--seed",type=int,default=2026)
    parser.add_argument("--extra-choices",type=int,default=6);parser.add_argument("--reference-seconds",type=float,default=5)
    parser.add_argument("--max-qubits",type=int,default=35)
    args=parser.parse_args();run(args.output,args.customers,args.scenario,args.steps,args.evaluations,args.shots,args.seed,args.extra_choices,args.reference_seconds,args.max_qubits)
