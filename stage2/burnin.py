"""Reachable mid-production benchmarks over the unchanged physical factory.

A common real execution prefix reaches the decision boundary.  Suffix policies
change through the existing controller interface, retaining every committed
operation, movement, worker appointment and inventory item.  The public snapshot
is a causal inspection artifact, not a standalone simulator checkpoint.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import time

from .advanced import AdvancedFactory
from .check import check_trace
from .spec import build

SCHEMA = "metaltech-stage2-burnin.v1"
RECORD_FIELDS = ("operations", "moves", "worker_moves", "events", "energy", "decisions", "qubo_decisions")
PRE_DECISION_EVENTS = frozenset(("lease_delivery","tool_service_complete","maintenance_complete",
    "ship","process_complete","qa_result","repair","scrap","replacement","new_unit",
    "reveal","outage","grid_derating","delivery_delay","urgent_order","delivery"))
ROOT = Path(__file__).resolve().parents[1]
PREFIX_WEIGHTS = dict(mode="standard",wip_limit=4,lease_calibration=True,selector="priority",
    due=1.,remaining=-4.,family=0.,noise=0.,setup=3.,worker_calendar=True,preposition=True,
    preposition_ticks=10,routing_free_buffers=False,routing_estimate_finish=False,bom_priority=False)
SUFFIX_POLICIES = {
    "retain-standard": {},
    "turbo": dict(mode="turbo"),
    "routing-eta": dict(routing_free_buffers=True,routing_estimate_finish=True),
    "eta-soft-join": dict(routing_free_buffers=True,routing_estimate_finish=True,
        bom_priority="join",bom_join_weight=4,bom_progress_weight=0),
}


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()


def source_hashes():
    names=("stage2/burnin.py","stage2/advanced.py","stage2/engine.py","stage2/spec.py",
           "stage2/check.py","stage2/dispatch.py","instances/stage2/metaltech_pressure.json")
    return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in names}


def reconstruct_boundary(records,instance,boundary):
    """Basic boundary facts derived solely from immutable committed records.

    No simulator caches, engine validity helpers, random seed, future outcomes or
    hidden event queue are used.  Full part/worker/tool cache replay is outside
    this function's coverage and is explicitly not a checkpoint claim.
    """
    machines={m["id"] for m in instance["machines"]}
    active_ops=[deepcopy(op) for op in records["operations"] if op["start"]<boundary<op["end"]]
    active_moves=[deepcopy(move) for move in records["moves"] if move["start"]<boundary<move["end"]]
    active_walks=[deepcopy(move) for move in records["worker_moves"] if move["start"]<boundary<move["end"]]
    reserved={}
    for move in records["moves"]:
        if (move.get("entity_type")=="part" and move["to"] in machines and
            move["start"]<boundary<move["drop_tick"]):
            reserved[move["to"]]=reserved.get(move["to"],0)+1
    shipped={e["order_id"]:e["tick"] for e in records["events"] if e["type"]=="ship" and e["tick"]<=boundary}
    blocked={}
    for op in records["operations"]:
        if op["end"]>boundary:continue
        for uid in op["unit_ids"]:
            picked=any(move.get("entity_type")=="part" and move.get("unit_id")==uid and
                move["from"]==op["machine_id"] and op["end"]<=move["pickup_tick"]<=boundary
                for move in records["moves"])
            if not picked:blocked.setdefault(op["machine_id"],set()).add(uid)
    return dict(active_operations=active_ops,active_moves=active_moves,active_worker_moves=active_walks,
        reserved_inputs=dict(sorted(reserved.items())),shipped_at=dict(sorted(shipped.items())),
        blocked_outputs={mid:sorted(units) for mid,units in sorted(blocked.items())},
        stationary_soc=records["energy"][-1]["soc"] if records["energy"] else instance["energy"]["stationary_soc_initial"])


def _public_events(events):
    # Even observed numerical quality draws are debugging details, not features
    # needed by a causal scheduler.  Pass/fail and its known consequences remain.
    return [{key:deepcopy(value) for key,value in event.items() if key!="keyed_uniform"} for event in events]


def capture(factory,boundary):
    records={name:deepcopy(factory.trace[name]) for name in RECORD_FIELDS}
    prefix=dict(boundary_tick=boundary,phase="after-completions-and-revelation-before-new-decisions",records=records)
    prefix["sha256"]=digest(prefix)
    basics=reconstruct_boundary(records,factory.i,boundary)
    parts_fields=("id","order_id","recipe","family","release_tick","location","step","status",
        "attempt","replacement","accepted","rework","busy","moving")
    parts=[{key:deepcopy(p[key]) for key in parts_fields if key in p} for p in factory.parts.values()]
    snapshot=dict(schema=SCHEMA,tick=boundary,tick_minutes=factory.i["tick_minutes"],
        horizon_ticks=factory.i["horizon_ticks"],remaining_ticks=factory.i["horizon_ticks"]-boundary,
        phase=prefix["phase"],prefix_sha256=prefix["sha256"],
        observation=deepcopy(factory.observation()),orders=deepcopy(list(factory.orders.values())),parts=parts,
        stock=dict(factory.stock),admitted_orders=sorted(factory.admitted),
        machines=[dict(m,output=sorted(m["output"])) for m in factory.machines.values()],
        workers=deepcopy(list(factory.workers.values())),tools=deepcopy(list(factory.tools.values())),
        agv_reservation_cache=[dict(id=a["id"],available_tick=a["busy"],reservation_destination=a["location"],
            reserved_terminal_soc=a["soc"],capacity=a["capacity"]) for a in factory.agvs.values()],
        investment_cost=factory.investment_cost,observed_grid_cap_kw=factory.grid_cap,
        observed_outages=dict(factory.outages),observed_events=_public_events(records["events"]),
        **basics,
        semantics=dict(reachable=True,standalone_restart_checkpoint=False,
            worker_hall="Committed walk destination; active walk records describe physical transit",
            resource_wear_and_tool_use="Committed usage, including whole active operations",
            agv_state="Reservation endpoint/SOC, not instantaneous position; see active_moves",
            quality="Observed pass/fail only; no future draw or actual generation seed"))
    # Validate selected cache facts against the independent record construction
    # now, before a suffix policy can act or modify any state.
    # The engine's power-active cache intentionally omits zero-power tool
    # services. They remain real resource occupations in public active_ops.
    powered_or_processing=[op for op in basics["active_operations"] if op.get("kind")!="tool_service"]
    if powered_or_processing!=factory.active:
        raise RuntimeError("Boundary cache disagrees with committed replay: active_operations")
    expected=dict(reserved_inputs=dict(sorted((mid,n) for mid,n in factory.reserved.items() if n)),
        shipped_at=dict(sorted(factory.shipped.items())),
        blocked_outputs={mid:sorted(m["output"]) for mid,m in sorted(factory.machines.items()) if m["output"]},
        stationary_soc=factory.soc)
    for field,value in expected.items():
        if basics[field]!=value:raise RuntimeError(f"Boundary cache disagrees with committed replay: {field}")
    return prefix,snapshot


def run(instance,weights=None,controller=None,*,boundary_tick=480,prefix_weights=None,method_id="suffix"):
    """Execute a shared prefix, then apply static overrides or a causal controller.

    A supplied controller receives the existing compact public observation only.
    Static weights are overrides to the explicit common prefix policy.  The
    actual instance seed remains inside the factory/witness for post-run audit;
    it is never passed to the controller or public snapshot.
    """
    if type(boundary_tick) is not int or not 0<boundary_tick<instance["horizon_ticks"]:
        raise ValueError("Boundary must be an integer strictly inside the horizon")
    if boundary_tick%instance.get("replan_ticks",4):
        raise ValueError("Boundary must coincide with an existing controller tick")
    prefix_policy=dict(PREFIX_WEIGHTS);prefix_policy.update(prefix_weights or {})
    suffix=dict(weights or {});saved={};factory=None
    def switched(observation):
        if observation["tick"]<boundary_tick:
            return dict(weights=dict(prefix_policy),action_id="common-burnin-prefix")
        first_suffix=not saved
        if first_suffix:
            saved["prefix"],saved["public_snapshot"]=capture(factory,boundary_tick)
            saved["snapshot_sha256"]=digest(saved["public_snapshot"])
        if controller is not None:
            answer=controller(deepcopy(observation))
            if first_suffix:answer=dict(answer,weights=dict(suffix,**answer.get("weights",{})))
            return answer
        return dict(weights=dict(suffix),action_id=method_id)
    factory=AdvancedFactory(instance,prefix_policy,switched)
    trace=factory.run()
    if not saved:raise RuntimeError("Execution did not reach the burn-in boundary")
    trace["provenance"]["reachable_burnin"]=dict(boundary_tick=boundary_tick,method_id=method_id,
        prefix_sha256=saved["prefix"]["sha256"],snapshot_sha256=saved["snapshot_sha256"],
        initialization="Executed common prefix; no state injection or artificial relocation")
    bundle=dict(schema=SCHEMA,boundary_tick=boundary_tick,method_id=method_id,
        prefix_weights=prefix_policy,suffix_overrides=suffix,**saved,trace=trace)
    bundle["verification"]=verify(bundle)
    return bundle


def verify(bundle):
    """Check full witness and basic snapshot facts without trusting cached flags."""
    issues=[];trace=bundle.get("trace",{});physical=check_trace(trace)
    if bundle.get("schema")!=SCHEMA:issues.append(dict(code="burnin_schema"))
    prefix=bundle.get("prefix",{});snapshot=bundle.get("public_snapshot",{});boundary=bundle.get("boundary_tick")
    if (type(boundary) is not int or not 0<boundary<trace.get("horizon_ticks",0) or
        boundary%trace.get("instance",{}).get("replan_ticks",4)):
        return dict(valid=False,issues=issues+[dict(code="burnin_boundary")],physical=physical)
    payload={k:v for k,v in prefix.items() if k!="sha256"}
    if prefix.get("sha256")!=digest(payload):issues.append(dict(code="prefix_digest"))
    if snapshot.get("prefix_sha256")!=prefix.get("sha256"):issues.append(dict(code="snapshot_prefix_digest"))
    if bundle.get("snapshot_sha256")!=digest(snapshot):issues.append(dict(code="snapshot_digest"))
    if prefix.get("boundary_tick")!=boundary or snapshot.get("tick")!=boundary:issues.append(dict(code="snapshot_boundary"))
    if snapshot.get("schema")!=SCHEMA:issues.append(dict(code="snapshot_schema"))
    if snapshot.get("horizon_ticks")!=trace.get("horizon_ticks"):issues.append(dict(code="snapshot_horizon"))
    records=prefix.get("records",{})
    for name in RECORD_FIELDS:
        rows=records.get(name)
        if not isinstance(rows,list):issues.append(dict(code="prefix_records",field=name));continue
        if trace.get(name,[])[:len(rows)]!=rows:issues.append(dict(code="immutable_prefix",field=name))
        clock="start" if name in ("operations","moves","worker_moves") else "tick"
        if any(row[clock]>boundary if name=="events" else row[clock]>=boundary for row in rows):
            issues.append(dict(code="prefix_after_boundary",field=name))
        # The prefix must include every earlier commitment, rather than merely
        # agreeing with an arbitrary shorter initial slice.
        remaining=trace.get(name,[])[len(rows):]
        if name!="events" and any(row[clock]<boundary for row in remaining):
            issues.append(dict(code="prefix_incomplete",field=name))
        if name=="events" and any(row[clock]<boundary for row in remaining):
            issues.append(dict(code="prefix_incomplete",field=name))
        if name=="events":
            expected=[e for e in trace.get(name,[]) if e["tick"]<boundary or
                (e["tick"]==boundary and e["type"] in PRE_DECISION_EVENTS)]
            if rows!=expected:issues.append(dict(code="prefix_boundary_events",field=name))
    if all(isinstance(records.get(name),list) for name in RECORD_FIELDS) and trace.get("instance"):
        basics=reconstruct_boundary(records,trace["instance"],boundary)
        basics["observed_events"]=_public_events(records["events"])
        for field,value in basics.items():
            if snapshot.get(field)!=value:issues.append(dict(code="snapshot_reconstruction",field=field))
    def private_fields(value):
        if isinstance(value,dict):
            for key,item in value.items():
                if key in ("seed","run_id","keyed_uniform","realized_stages"):return True
                if private_fields(item):return True
        if isinstance(value,list):return any(private_fields(v) for v in value)
        return False
    if private_fields(snapshot):issues.append(dict(code="snapshot_private_fields"))
    return dict(valid=physical["valid"] and not issues,issues=issues,physical=physical,
        coverage=["full_trace_independent_physical_replay","immutable_prefix_records_and_digest",
            "active_operations_moves_and_walks","input_reservations","blocked_machine_outputs","shipped_orders","stationary_soc","snapshot_private_field_exclusion"],
        unsupported=["detailed_parts_workers_tools_cache_replay","standalone_snapshot_restart","general_policy_nonanticipativity_proof"])


def common_prefix(bundles):
    """Compare methods on one actual tape; other tapes may differ observably."""
    if not bundles:return dict(valid=False,issues=[dict(code="empty_comparison")])
    first=bundles[0];issues=[]
    for bundle in bundles[1:]:
        if bundle["prefix"]!=first["prefix"]:issues.append(dict(code="different_prefix",method=bundle["method_id"]))
        if bundle["public_snapshot"]!=first["public_snapshot"]:issues.append(dict(code="different_snapshot",method=bundle["method_id"]))
    return dict(valid=not issues,issues=issues,prefix_sha256=first["prefix"]["sha256"])


def _compare_group(task):
    orders,seed,horizon,boundary,outdir=task;bundles=[];rows=[];out=Path(outdir)
    for method,weights in SUFFIX_POLICIES.items():
        started=time.perf_counter();bundle=run(build(orders=orders,horizon=horizon,seed=seed),weights,
            boundary_tick=boundary,method_id=method);bundles.append(bundle)
        name=f"n{orders}-s{seed}-{method}.json.gz"
        data=json.dumps(bundle,separators=(",",":"),allow_nan=False).encode();(out/name).write_bytes(gzip.compress(data,mtime=0))
        trace_name=f"n{orders}-s{seed}-{method}-trace.json.gz"
        trace_data=json.dumps(bundle["trace"],separators=(",",":"),allow_nan=False).encode()
        (out/trace_name).write_bytes(gzip.compress(trace_data,mtime=0))
        metrics=bundle["trace"]["metrics"];snap=bundle["public_snapshot"]
        rows.append(dict(orders=orders,seed=seed,method=method,valid=bundle["verification"]["valid"],
            issues=bundle["verification"]["issues"],physical_issues=bundle["verification"]["physical"]["issues"],
            metrics=metrics,boundary_active_operations=len(snap["active_operations"]),
            boundary_active_moves=len(snap["active_moves"]),boundary_shipped=len(snap["shipped_at"]),
            bundle_file=name,bundle_sha256=hashlib.sha256(data).hexdigest(),
            trace_file=trace_name,trace_sha256=hashlib.sha256(trace_data).hexdigest(),elapsed_seconds=time.perf_counter()-started))
    # One separate public artifact makes clear that a controller need not see the
    # private full witness (which necessarily contains the audit seed).
    (out/f"n{orders}-s{seed}-public-snapshot.json").write_text(json.dumps(bundles[0]["public_snapshot"],indent=2))
    return dict(orders=orders,seed=seed,rows=rows,common_prefix=common_prefix(bundles))


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest="command",required=True)
    compare=sub.add_parser("compare");compare.add_argument("--orders",type=int,nargs="+",default=[8,12,24])
    compare.add_argument("--seeds",type=int,nargs="+",default=[20,21,22,23]);compare.add_argument("--horizon",type=int,default=5760)
    compare.add_argument("--boundary",type=int,default=480);compare.add_argument("--workers",type=int,default=4)
    compare.add_argument("--output",type=Path,required=True)
    check=sub.add_parser("verify");check.add_argument("bundle",type=Path)
    args=parser.parse_args(argv)
    if args.command=="verify":
        raw=args.bundle.read_bytes();bundle=json.loads(gzip.decompress(raw) if args.bundle.suffix==".gz" else raw)
        result=verify(bundle);print(json.dumps(result,indent=2));return 0 if result["valid"] else 1
    args.output.mkdir(parents=True,exist_ok=True);before=source_hashes()
    for name in before:(args.output/Path(name).name).write_bytes((ROOT/name).read_bytes())
    started=time.perf_counter();tasks=[(n,s,args.horizon,args.boundary,str(args.output)) for n in args.orders for s in args.seeds]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:groups=list(pool.map(_compare_group,tasks))
    after=source_hashes();report=dict(schema=SCHEMA,scope="Development comparison; no held-out claim",boundary_tick=args.boundary,
        horizon_ticks=args.horizon,orders=args.orders,seeds=args.seeds,prefix_weights=PREFIX_WEIGHTS,suffix_policies=SUFFIX_POLICIES,
        source_before=before,source_after=after,source_stable=before==after,elapsed_seconds=time.perf_counter()-started,groups=groups)
    report["valid"]=report["source_stable"] and all(g["common_prefix"]["valid"] and all(r["valid"] for r in g["rows"]) for g in groups)
    (args.output/"report.json").write_text(json.dumps(report,indent=2));print(json.dumps(dict(valid=report["valid"],groups=len(groups),output=str(args.output),elapsed_seconds=report["elapsed_seconds"]),indent=2))
    return 0 if report["valid"] else 1


if __name__=="__main__":raise SystemExit(main())
