"""A predeclared, local-only paired-meal QAOA pilot; retain every run."""
import argparse
from pathlib import Path

from .build_meal_release import save, seal
from .meal_search import run


def campaign(output,customers=6,steps=8,evaluations=16,shots=2048,max_qubits=35):
    output = Path(output)
    if output.exists():
        raise ValueError("Fresh campaign directory required")
    output.mkdir(parents=True)
    plan = dict(customers=customers,steps=steps,evaluations_per_step=evaluations,shots_per_step=shots,
                max_qubits=max_qubits,extra_choices=7,reference_seconds=3,
                cases=[dict(scenario=s,seed=seed) for s in ("S0","S1","S2","S3") for seed in (2026,2027)],
                selection="All four paired event cases, two predeclared algorithm seeds; no seed selection after outcomes",
                scope="Development pilot; same four inputs, not independent customer-week replicates",
                physical_qpu_calls=0,veloxq_calls=0)
    save(output/"experiment-plan.json",plan)
    rows=[]
    for case in plan["cases"]:
        name=f"{case['scenario']}-seed-{case['seed']}"
        result=run(output/name,customers=customers,scenario=case["scenario"],steps=steps,
                   evaluations=evaluations,shots=shots,seed=case["seed"],extra_choices=7,
                   reference_seconds=3,max_qubits=max_qubits)
        rows.append(dict(case=name,initial=result["initial_metrics"],final=result["final_metrics"],
                         reference=result["reference_metrics"],reference_status=result["reference_status"],
                         max_qubits=max(r["resources"]["data_qubits"] for r in result["steps"]),total_s=result["total_s"]))
        save(output/"progress.json",dict(completed=rows,planned_cases=len(plan["cases"])))
    save(output/"report.json",dict(plan=plan,rows=rows,complete=True,
         limitations=["Exact sector simulation and exact-CVaR training, not a hardware result",
                      "Per-step controls share quantum incumbents; full-controller advantage is untested",
                      "Two seeds on four paired inputs do not establish broad statistical generalization"]))
    seal(output)
    return rows


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--customers",type=int,default=6)
    parser.add_argument("--steps",type=int,default=8)
    args=parser.parse_args()
    campaign(args.output,customers=args.customers,steps=args.steps)
