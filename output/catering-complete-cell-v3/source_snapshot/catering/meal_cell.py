"""Complete small paired-meal cell: no option cap, native/exhaustive references.

The calendars and recipes are explicit physical input, not a crop of the
six-customer study. Classical tractability is intentional for correctness.
"""
import argparse
from pathlib import Path

import numpy as np

from .audit import audit_bundle
from .build_meal_release import save, seal
from .contracts import method_result
from .domain import snapshot, validate_instance, digest
from .meal_blocks import meal_fixture, compile_meal_blocks, sector_data, sector_bits
from .meal_search import warm_state, train, sample_result, distribution_stats
from .meal_reference import solve_bundle
from .native_slots import solve_native
from .options import enumerate_options
from .decode import decode
from .qubo import ising


def cell_fixture():
    instance = meal_fixture(1)
    instance["instance_id"] = "paired-meal-complete-cell-v3"
    instance["calendars"]["P1"] = [[0,10],[20,30],[40,50]]
    instance["calendars"]["W3"] = [[0,20],[50,60],[70,80]]
    # This main-course recipe has fixed yield. The side retains one/two-lot
    # yields and sharing, while the committed main still needs its side.
    instance["menus"]["B"]["yields"] = [1]
    instance["menus"]["B"]["cooking"] = {"1":20}
    return validate_instance(instance)


def run(output):
    output = Path(output)
    if output.exists():
        raise ValueError("Fresh complete-cell directory required")
    output.mkdir(parents=True)
    plan = dict(seeds=[2026,2027,2028],depths=[1,2],evaluations=64,shots=4096,
                scenario="S0",scope="Complete small calendar-limited cell; not the six-customer study",
                selection="All legal programs, no pruning by global reference; all predeclared seeds/depths retained")
    save(output/"experiment-plan.json",plan)
    instance = cell_fixture()
    state = snapshot(instance,"S0")
    programs = enumerate_options(instance,state)
    bundle = compile_meal_blocks(instance,state,programs,parent_domain_sha256=digest([p["id"] for p in programs]),complete_domain=True)
    save(output/"instance.json",instance);save(output/"snapshot.json",state)
    save(output/"quantum-qubo.json",bundle);save(output/"quantum-ising.json",ising(bundle))
    sector = sector_data(bundle)
    initial = warm_state(bundle,sector,set())
    rows=[]
    for depth in plan["depths"]:
        for seed in plan["seeds"]:
            rng=np.random.default_rng(seed)
            best,control,trace=train(bundle,sector,initial,rng,evaluations=plan["evaluations"],depth=depth)
            samples,winner=sample_result(bundle,sector,best[2],rng,plan["shots"])
            controls={}
            for name,vector in (("initializer",initial),("mixer-only",control[2])):
                measured,chosen=sample_result(bundle,sector,vector,rng,plan["shots"])
                controls[name]=dict(**measured,best_metrics=None if chosen is None else chosen[1]["check"]["metrics"],
                                    distribution=distribution_stats(vector,sector))
            directory=output/f"p{depth}-seed-{seed}"
            save(directory/"qubo.json",bundle)
            save(directory/"warm-start.json",dict(incumbent_program_ids=[],exploration=0.15))
            save(directory/"training.json",dict(evaluations=plan["evaluations"],depth=depth,loss="Exact simulator CVaR alpha=0.1",
                 parameters=best[1],control_parameters=control[1],trace=trace))
            result=method_result(bundle,"complete_cell_xy_qaoa",samples["samples"])
            result.update(execution_kind="quantum_simulator",configuration=dict(seed=seed,depth=depth,repair=False),
                          valid_shots=samples["valid_shots"],shots=samples["shots"])
            save(directory/"samples.json",result);save(directory/"controls.json",controls)
            best_metrics=None if winner is None else winner[1]["check"]["metrics"]
            row=dict(seed=seed,depth=depth,best_metrics=best_metrics,valid_shots=samples["valid_shots"],shots=plan["shots"],
                     distribution=distribution_stats(best[2],sector),
                     control_best_metrics={name:r["best_metrics"] for name,r in controls.items()})
            rows.append(row)
            save(directory/"summary.json",row)
    # References come after quantum training/sampling, and never seed the search.
    audit = audit_bundle(bundle)
    encoded = solve_bundle(bundle,seconds=3)
    raw = solve_native(instance,state,dict(wall_time_limit_s=3),dict(workers=1,seed=2026))
    exact = decode(bundle,sector_bits(bundle,sector,int(sector["energy"].argmin())))
    if not audit["valid"] or not exact["valid"] or raw["reference_status"]!="OPTIMAL" or encoded["reference"]["status"]!="OPTIMAL":
        raise AssertionError("Complete-cell reference gate failed")
    if exact["check"]["metrics"]!=raw["check"]["metrics"] or exact["check"]["metrics"]!=encoded["check"]["metrics"]:
        raise AssertionError("Complete-cell raw/encoded minima disagree")
    save(output/"audit.json",audit);save(output/"reference-encoded.json",encoded);save(output/"reference-raw.json",raw)
    save(output/"reference-sector.json",exact)
    report=dict(profile_id=instance["profile_id"],size=bundle["size"],sector_states=sector["states"],
                physically_feasible_sector_states=int(sector["valid"].sum()),reference=raw["check"]["metrics"],
                exact_raw_encoded_agreement=True,rows=rows,physical_qpu_calls=0,veloxq_calls=0,
                limitations=["Complete on this small declared recipe/calendar grid; not the larger kitchen",
                             "Classically easy correctness/method experiment, not a hardness or advantage claim",
                             "Controls use separate samples; no quantum superiority follows from tied best schedules",
                             "Exact-CVaR sector simulator training, not shot-noisy hardware optimization"])
    save(output/"report.json",report);seal(output)
    return report


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();print(run(args.output))
