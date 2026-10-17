"""Causal queue/energy threshold control, tuned by paired-tape classical search.

This searches interpretable policies, never relaxes factory physics, and records
every simulated episode. Training, validation selection and test are distinct.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
import hashlib
import json
import math
import multiprocessing
from pathlib import Path
import random
import statistics
import time

ROOT = Path(__file__).resolve().parents[1]
TRAIN = tuple(range(32))
VALIDATION = tuple(range(100, 116))
OPTIONS = dict(wip_low=(1,2,3,4,6,8), wip_high=(1,2,3,4,6,8),
    downstream_limit=(1,2,4,8,99), heat_limit=(2,4,8,12,99),
    family=(0,8,24,48), remaining=(-16,-12,-8,-4,0,8), due=(.25,.5,1.),
    congested_mode=("eco","standard","turbo"), free_mode=("eco","standard","turbo"),
    late_mode=("eco","standard","turbo"), late_fraction=(.5,.7,.85,1.1),
    lease_fraction=(0.,.125,.25,1.1), grid_eco=(False,True))
DEFAULT = dict(wip_low=3,wip_high=6,downstream_limit=4,heat_limit=8,
    family=24,remaining=-4,due=.25,congested_mode="eco",free_mode="standard",
    late_mode="turbo",late_fraction=.85,lease_fraction=0.,grid_eco=True)


def config(orders=8, horizon=5760, profile="full"):
    return dict(orders=orders,horizon=horizon,profile=profile)


def hashes():
    files = ("stage2/engine.py","stage2/spec.py","stage2/check.py","stage2/dispatch.py",
        "stage2/qubo.py","stage2/quantum.py","stage2/threshold.py",
        "instances/stage2/metaltech_pressure.json")
    return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in files}


def assert_sources(expected):
    current=hashes()
    if current!=expected:
        raise RuntimeError("Source changed during experiment: "+str([k for k in current if current[k]!=expected.get(k)]))


def canonical(params):
    result=dict(params)
    if set(result)!=set(OPTIONS):
        raise ValueError("Threshold parameters must specify the complete declared domain")
    for key, choices in OPTIONS.items():
        if result[key] not in choices:
            raise ValueError(f"Unsupported {key}: {result[key]}")
    result["wip_low"],result["wip_high"]=sorted((result["wip_low"],result["wip_high"]))
    return result


def policy_id(params):
    return hashlib.sha256(json.dumps(canonical(params),sort_keys=True).encode()).hexdigest()


def static_params(weights):
    """Embed a supported static policy exactly; no loss hidden in teacher mapping."""
    wip=int(weights.get("wip_limit",6)); mode=weights.get("mode","standard")
    if weights.get("setup",10 if weights.get("family",0) else 3)!=(10 if weights.get("family",0) else 3):
        raise ValueError("Teacher setup coefficient is outside this controller's exact embedding")
    if weights.get("noise",0):raise ValueError("Seeded-noise teachers are outside this exact embedding")
    return canonical(dict(wip_low=wip,wip_high=wip,downstream_limit=99,heat_limit=99,
        family=weights.get("family",0),remaining=weights.get("remaining",-4),
        due=weights.get("due",1.),congested_mode=mode,free_mode=mode,late_mode=mode,
        late_fraction=1.1,lease_fraction=0. if weights.get("lease_calibration",False) else 1.1,
        grid_eco=False))


class Controller:
    def __init__(self, params, base_weights=None):
        self.params=canonical(params)
        self.base=dict(base_weights or {})
        self.base.setdefault("selector","priority");self.base.setdefault("policy_seed",0)
        self.congested=False
        self.count=0;self.changes=0;self.previous=None;self.reasons={}

    def __call__(self, obs):
        p=self.params
        # All terms are current public counts; no lineage, future event or seed is read.
        downstream=(obs.get("queue_QA",0)+obs.get("queue_ASSEMBLY",0)
                    +max(0,obs.get("accepted_components",0)-3)/3)
        heat=obs.get("queue_HEAT",0)
        if self.congested:
            self.congested=not(downstream<.5*p["downstream_limit"] and heat<.5*p["heat_limit"])
        else:
            self.congested=downstream>=p["downstream_limit"] or heat>=p["heat_limit"]
        fraction=obs["tick"]/max(1,obs["horizon_ticks"])
        wip=p["wip_low"] if self.congested else p["wip_high"]
        mode=p["congested_mode"] if self.congested else p["free_mode"]
        reason="congested" if self.congested else "free"
        if fraction>=p["late_fraction"] and obs.get("overdue_orders",0)>0 and not self.congested:
            mode=p["late_mode"];reason="late"
        if p["grid_eco"] and obs["grid_cap_kw"]<.75*obs["normal_grid_cap_kw"]:
            mode="eco";reason="grid_derated"
        weights=dict(self.base,wip_limit=wip,mode=mode,due=p["due"],remaining=p["remaining"],
            family=p["family"],setup=10 if p["family"] else 3,
            lease_calibration=fraction>=p["lease_fraction"])
        action=f"threshold-{reason}-w{wip}-{mode}-lease{int(weights['lease_calibration'])}"
        self.changes+=self.previous is not None and self.previous!=action
        self.previous=action;self.count+=1;self.reasons[reason]=self.reasons.get(reason,0)+1
        return dict(weights=weights,action_id=action)


def simulate(task):
    from .engine import run
    from .spec import build
    from .check import check_trace
    started=time.perf_counter()
    controller=Controller(task["params"],task.get("base_weights"))
    trace=run(build(**task["config"],seed=task["seed"]),controller=controller)
    checked=check_trace(trace)
    result=dict(config=task["config"],seed=task["seed"],policy_id=policy_id(task["params"]),
        params=task["params"],base_weights=controller.base,valid=checked["valid"],
        issues=checked["issues"][:10],metrics=trace["metrics"],decisions=controller.count,
        action_changes=controller.changes,reasons=controller.reasons,
        wall_seconds=time.perf_counter()-started)
    if task.get("trace_path"):
        path=Path(task["trace_path"]);path.parent.mkdir(parents=True,exist_ok=True)
        trace["validation"]=checked
        path.write_text(json.dumps(trace)+"\n")
    return result


def empirical_cvar90(values):
    if not values:raise ValueError("CVaR needs at least one observation")
    ordered=sorted(values,reverse=True);mass=.1*len(ordered)
    whole=math.floor(mass);fraction=mass-whole
    return (sum(ordered[:whole])+(fraction*ordered[whole] if fraction else 0))/mass


def summarize(rows, risk_weight=.25):
    if not rows:return {}
    tardy=sorted((r["metrics"]["total_tardiness_ticks"] for r in rows),reverse=True)
    tail=empirical_cvar90(tardy)
    average=statistics.mean(tardy)
    return dict(episodes=len(rows),invalid=sum(not r["valid"] for r in rows),
        complete=sum(r["valid"] and r["metrics"]["all_orders_fulfilled"] for r in rows),
        mean_unfulfilled=statistics.mean(r["metrics"]["orders"]-r["metrics"]["shipped"] for r in rows),
        mean_tardiness_ticks=average,empirical_cvar90_tardiness=tail,
        risk_weight=risk_weight,risk_adjusted_tardiness=average+risk_weight*tail,
        mean_total_cost=statistics.mean(r["metrics"]["total_cost"] for r in rows),
        mean_action_changes=statistics.mean(r["action_changes"] for r in rows),
        simulation_cpu_seconds=sum(r["wall_seconds"] for r in rows),global_optimality_gap=None)


def rank(summary):
    return (summary["invalid"],summary["mean_unfulfilled"],summary["risk_adjusted_tardiness"],summary["mean_total_cost"])


def load_teachers(path,configs,expected):
    teacher=json.loads(Path(path).read_text())
    role=teacher.get("policy_selection_role","validation_selected_checkpoint" if "selected_validation" in teacher else "training_only_last_update")
    if role!="training_only_last_update" or teacher["policy"]["kind"]!="context_static":
        raise ValueError("Use a training-only static checkpoint, not a validation-selected policy")
    if set(teacher["train_seeds"])-set(TRAIN):raise ValueError("Teacher split is not training-only")
    for name,digest in expected.items():
        if name!="stage2/threshold.py" and teacher["source_hashes"].get(name)!=digest:
            raise ValueError(f"Teacher physical model differs: {name}")
    result=[]
    for c in configs:
        index=teacher["configs"].index(c)
        action=teacher["policy"]["actions"][index]
        result.append(static_params(teacher["actions"][action]["weights"]))
    return result,dict(path=str(path),sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        external_fit_wall_seconds=teacher["actual_wall_seconds"],external_fit_episodes=teacher["fit_episodes"])


class Measurements:
    """Snapshot-local cache. Every actual simulation is written exactly once."""
    def __init__(self, configs, sources, output, executor=None, base=None):
        self.configs=configs;self.sources=sources;self.output=Path(output);self.executor=executor
        self.base=dict(base or {},policy_seed=0);self.cache={};self.measured=0;self.hits=0
        self.cpu_seconds=0.

    def collect(self, context, candidates, seeds, role):
        assert_sources(self.sources)
        allowed={"training":set(TRAIN),"validation":set(VALIDATION)}
        if role not in allowed or set(seeds)-allowed[role]:
            raise ValueError("Seed role/split violation")
        tasks=[];keys=[];requested=[]
        for p in candidates:
            for seed in seeds:
                key=(context,policy_id(p),seed,role)
                requested.append(key)
                if key in self.cache:
                    self.hits+=1;continue
                if key in keys:continue
                keys.append(key)
                tasks.append(dict(config=self.configs[context],params=p,seed=seed,base_weights=self.base))
        rows=(list(self.executor.map(simulate,tasks)) if self.executor else [simulate(t) for t in tasks])
        assert_sources(self.sources)
        with (self.output/"measurements.jsonl").open("a") as stream:
            for key,row in zip(keys,rows):
                row.update(seed_role=role,source_fingerprint=self.sources["stage2/threshold.py"])
                self.cache[key]=row;stream.write(json.dumps(row)+"\n")
        self.measured+=len(rows);self.cpu_seconds+=sum(r["wall_seconds"] for r in rows)
        return [self.cache[key] for key in requested]


def atomic_json(path,value):
    temporary=Path(str(path)+".tmp")
    temporary.write_text(json.dumps(value,indent=2)+"\n");temporary.replace(path)


def search(configs,output,method="cem",seconds=600,workers=4,candidates=16,
           generations=40,paired_tapes=4,validation_every=5,rerank_pool=8,
           rerank_seeds=tuple(range(8)),seed=2026,risk_weight=.25,teacher=None,
           selector="priority"):
    if method not in ("cem","random","fixed"):raise ValueError("Unsupported search method")
    if min(seconds,workers,candidates,generations,paired_tapes,rerank_pool,validation_every)<1:
        raise ValueError("Positive resource/search settings required")
    if paired_tapes>len(TRAIN) or not rerank_seeds or set(rerank_seeds)-set(TRAIN):
        raise ValueError("Paired/reranking tapes must stay within the training split")
    if not math.isfinite(risk_weight) or risk_weight<0:raise ValueError("Nonnegative finite risk weight required")
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if (output/"measurements.jsonl").exists():raise ValueError("Choose a fresh output directory")
    started=time.perf_counter();sources=hashes();rng=random.Random(seed)
    priors,teacher_provenance=([canonical(DEFAULT) for _ in configs],None)
    if teacher:priors,teacher_provenance=load_teachers(teacher,configs,sources)
    probabilities=[{key:[.7/len(options)+(.3 if value==priors[k][key] else 0) for value in options]
        for key,options in OPTIONS.items()} for k in range(len(configs))]
    pool=[{policy_id(priors[k]):dict(params=priors[k],scores={})} for k in range(len(configs))]
    selected=deepcopy(priors);training_incumbent=deepcopy(priors)
    selected_validation=[None]*len(configs);curves=[]
    executor=(ProcessPoolExecutor(max_workers=workers,mp_context=multiprocessing.get_context("spawn")) if workers>1 else None)
    measurements=Measurements(configs,sources,output,executor,dict(selector=selector))
    protocol=dict(schema="stage2-threshold-search.v1",method=method,configs=configs,
        source_hashes=sources,options=OPTIONS,train_seeds=list(TRAIN),validation_seeds=list(VALIDATION),
        final_test_seeds="untouched; supplied explicitly by evaluator",seed=seed,
        requested_fit_seconds=seconds,workers=workers,candidates_per_generation=candidates,
        maximum_generations=generations,paired_tapes=paired_tapes,validation_every=validation_every,
        rerank_pool=rerank_pool,rerank_seeds=list(rerank_seeds),risk_weight=risk_weight,
        teacher=teacher_provenance,selector=selector,
        objective="lex physical-validity, mean-unfulfilled, mean-tardy+risk-weight*empirical-CVaR90, mean-total-cost",
        budget="all actual simulation, cache lookup, ranking, validation and setup charged; reused external teacher cost separate")
    atomic_json(output/"protocol.json",protocol)

    def validate_context(context,candidate_list):
        # A finite shortlist is first compared on the SAME training tapes.
        rows=measurements.collect(context,candidate_list,rerank_seeds,"training")
        train_summaries=[]
        for p in candidate_list:
            rs=[r for r in rows if r["policy_id"]==policy_id(p)]
            info=summarize(rs,risk_weight);train_summaries.append((info,p))
            pool[context].setdefault(policy_id(p),dict(params=p,scores={}))
            pool[context][policy_id(p)]["scores"].update({r["seed"]:r for r in rs})
        _,candidate=min(train_summaries,key=lambda pair:rank(pair[0]))
        training_incumbent[context]=deepcopy(candidate)
        validation_rows=measurements.collect(context,[candidate],VALIDATION,"validation")
        score=summarize(validation_rows,risk_weight)
        if selected_validation[context] is None or rank(score)<rank(selected_validation[context]):
            selected[context]=deepcopy(candidate);selected_validation[context]=score
        return dict(candidate=candidate,validation=score,selected_validation=selected_validation[context])

    try:
        # Strong static teacher/fixed physics prior is an eligible fallback.
        for context in range(len(configs)):validate_context(context,[priors[context]])
        for generation in range(generations):
            if time.perf_counter()-started>=seconds:break
            context=generation%len(configs)
            iteration=generation//len(configs)
            seeds=tuple(TRAIN[(iteration*paired_tapes+j)%len(TRAIN)] for j in range(paired_tapes))
            proposals=[training_incumbent[context]]
            if method=="fixed":proposals=[priors[context]]
            else:
                attempts=0
                while len(proposals)<candidates and attempts<candidates*20:
                    attempts+=1
                    params={key:rng.choices(options,weights=probabilities[context][key] if method=="cem" else None)[0]
                            for key,options in OPTIONS.items()}
                    params=canonical(params)
                    if params not in proposals:proposals.append(params)
            rows=measurements.collect(context,proposals,seeds,"training")
            scored=[]
            for params in proposals:
                rs=[r for r in rows if r["policy_id"]==policy_id(params)]
                score=summarize(rs,risk_weight);scored.append((score,params))
                entry=pool[context].setdefault(policy_id(params),dict(params=params,scores={}))
                entry["scores"].update({r["seed"]:r for r in rs})
            scored.sort(key=lambda pair:rank(pair[0]))
            if method=="cem":
                elite=scored[:max(1,math.ceil(len(scored)*.25))]
                for key,options in OPTIONS.items():
                    target=[.05/len(options)+.95*sum(p[key]==value for _,p in elite)/len(elite) for value in options]
                    probabilities[context][key]=[.7*a+.3*b for a,b in zip(probabilities[context][key],target)]
            event=dict(generation=generation,context=context,training_tapes=list(seeds),
                best_paired_training=scored[0][0],best_params=scored[0][1],
                candidate_paired_summaries=[dict(policy_id=policy_id(p),summary=s) for s,p in scored])
            if (iteration+1)%validation_every==0 or generation+len(configs)>=generations or method=="fixed":
                ordered=sorted(pool[context].values(),key=lambda e:rank(summarize(list(e["scores"].values()),risk_weight)))
                shortlist=[e["params"] for e in ordered[:rerank_pool]]
                if training_incumbent[context] not in shortlist:shortlist.append(training_incumbent[context])
                event["checkpoint_selection"]=validate_context(context,shortlist)
            event.update(elapsed_seconds=time.perf_counter()-started,actual_simulations=measurements.measured,
                         cache_hits=measurements.hits,simulation_cpu_seconds=measurements.cpu_seconds)
            curves.append(event)
            artifact=dict(schema="stage2-threshold-policy.v1",method=method,configs=configs,
                params=deepcopy(selected),selected_validation=deepcopy(selected_validation),
                training_incumbent_params=deepcopy(training_incumbent),
                source_hashes=sources,base_weights=measurements.base,policy_selection_role="validation_selected",
                train_seeds=list(TRAIN),validation_seeds=list(VALIDATION),teacher=teacher_provenance,
                actual_fit_wall_seconds=time.perf_counter()-started,requested_fit_seconds=seconds,
                actual_simulations=measurements.measured,cache_hits=measurements.hits,
                simulation_cpu_seconds=measurements.cpu_seconds,risk_weight=risk_weight,curves=curves)
            atomic_json(output/"checkpoint.json",artifact)
            print(json.dumps(event),flush=True)
            if method=="fixed" and generation+1>=len(configs):break
    finally:
        if executor:executor.shutdown()
    if not curves:
        artifact=dict(schema="stage2-threshold-policy.v1",method=method,configs=configs,params=selected,
            selected_validation=selected_validation,source_hashes=sources,base_weights=measurements.base,
            policy_selection_role="validation_selected",risk_weight=risk_weight,
            actual_fit_wall_seconds=time.perf_counter()-started,actual_simulations=measurements.measured,
            teacher=teacher_provenance,curves=[])
        atomic_json(output/"checkpoint.json",artifact)
    return artifact


def evaluate(artifact,output,seeds,workers=4,traces=False):
    assert_sources(artifact["source_hashes"])
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    tasks=[]
    for context,c in enumerate(artifact["configs"]):
        for seed in seeds:
            task=dict(config=c,params=artifact["params"][context],seed=seed,base_weights=artifact["base_weights"])
            if traces:task["trace_path"]=str(output/f"trace-load{c['orders']}-seed{seed}.json")
            tasks.append(task)
    started=time.perf_counter()
    if workers>1:
        with ProcessPoolExecutor(max_workers=workers,mp_context=multiprocessing.get_context("spawn")) as executor:
            rows=list(executor.map(simulate,tasks))
    else:rows=[simulate(task) for task in tasks]
    assert_sources(artifact["source_hashes"])
    report=dict(schema="stage2-threshold-evaluation.v1",seeds=list(seeds),configs=artifact["configs"],
        source_hashes=artifact["source_hashes"],params=artifact["params"],
        selection_role=artifact["policy_selection_role"],rows=rows,
        summaries=[dict(config=c,**summarize([r for r in rows if r["config"]==c],artifact["risk_weight"])) for c in artifact["configs"]],
        wall_seconds=time.perf_counter()-started)
    atomic_json(output/"evaluation.json",report)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--method",choices=("cem","random","fixed"),default="cem")
    p.add_argument("--orders",default="8,12,16,24")
    p.add_argument("--horizon",type=int,default=5760)
    p.add_argument("--seconds",type=float,default=600)
    p.add_argument("--workers",type=int,default=4)
    p.add_argument("--candidates",type=int,default=16)
    p.add_argument("--generations",type=int,default=40,help="Total generations, cycling over requested workloads")
    p.add_argument("--paired-tapes",type=int,default=4)
    p.add_argument("--validation-every",type=int,default=5,help="Generations per workload before validation selection")
    p.add_argument("--rerank-pool",type=int,default=8)
    p.add_argument("--rerank-seeds",default="0,1,2,3,4,5,6,7")
    p.add_argument("--risk-weight",type=float,default=.25)
    p.add_argument("--seed",type=int,default=2026)
    p.add_argument("--teacher",type=Path,help="Training-only static checkpoint used as strong prior/fallback")
    p.add_argument("--selector",default="priority")
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--checkpoint",type=Path,help="Evaluation-only mode; explicit --evaluation-seeds required")
    p.add_argument("--evaluation-seeds",help="Explicit evaluation tape list; no final holdout is used automatically")
    p.add_argument("--save-traces",action="store_true")
    a=p.parse_args()
    if a.checkpoint:
        if not a.evaluation_seeds:p.error("Evaluation requires explicit seed roles/list")
        artifact=json.loads(a.checkpoint.read_text())
    else:
        artifact=search([config(int(n),a.horizon) for n in a.orders.split(",")],a.output,a.method,
            a.seconds,a.workers,a.candidates,a.generations,a.paired_tapes,a.validation_every,
            a.rerank_pool,tuple(map(int,a.rerank_seeds.split(","))),a.seed,a.risk_weight,a.teacher,a.selector)
    if a.evaluation_seeds:
        report=evaluate(artifact,a.output/"evaluation",tuple(map(int,a.evaluation_seeds.split(","))),a.workers,a.save_traces)
        print(json.dumps(report["summaries"],indent=2))


if __name__=="__main__":main()
