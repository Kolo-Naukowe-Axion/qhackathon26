"""Independent finite-domain TRAIN audit; no factory runs or policy selection."""
from collections import defaultdict
from copy import deepcopy
import gzip
import hashlib
import json
import math
from pathlib import Path
import time

from stage2.check import check_trace
from stage2.identity_audit import audit_trace
from stage2.quality_material_bound import certificate
from stage2.spec import build

ROOT=Path(__file__).resolve().parent
DATA=ROOT.parent/'axion-oracle-audit-v21p1-submission'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def metric(r):
    m=r['metrics'];return (m['orders']-m['shipped'],m['total_tardiness_ticks'],m['total_cost'])
def near(a,b):assert math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-7),(a,b)
def domain(original,radius):
    def visit(prefix,used):
        if len(prefix)==8:
            yield tuple(prefix);return
        for a in range(6):
            changed=int(a!=original[len(prefix)])
            if used+changed<=radius:yield from visit(prefix+[a],used+changed)
    return list(visit([],0))


def audit():
    began=time.perf_counter();r=read(DATA/'results/report.json');protocol=read(DATA/'results/protocol.json')
    retention=read(DATA/'retention-analysis.json');bounds=read(DATA/'necessary-bound-supplement.json')
    assert retention['report_sha256']==bounds['report_sha256']==sha(DATA/'results/report.json')
    assert r['source_stable'] and r['complete_checked_grid'] and r['witnesses_complete_valid']
    assert r['seeds']==list(range(8)) and r['actor_seed']==900000 and r['actual_grid_execution_count']==12184 and r['actual_oracle_replay_count']==24
    for name,value in r['source_hashes'].items():assert sha(DATA/'results/source_snapshot'/name)==value==sha(name)
    assert sha(DATA/'results/selected-checkpoint.json')==r['checkpoint_sha256']
    rows=r['rows'];witnesses=r['oracle_witnesses'];raw=[json.loads(x) for x in (DATA/'results/rows.jsonl').read_text().splitlines()]
    expected={(x['phase'],x['task_id']):x for x in rows+witnesses}
    assert len(expected)==len(raw)==12208
    assert {(x['phase'],x['task_id']):x for x in raw}==expected
    assert all(x['valid'] and x['identity_audit']['valid'] and not x['issues'] and x['decode_mismatches']==0 for x in raw)
    assert all(x['config']['seed'] in range(8) and x['actor_seed']==900000 for x in raw)
    for x in rows:assert digest(x['metrics'])==x['metrics_sha256']
    summaries=[];anchors={};offset=0;bestrows={}
    for c,s in zip(r['contexts'],r['summary']):
        variants=domain(c['original_schedule'],c['radius']);assert len(variants)==(41 if c['context_id']==0 else 741)
        assert [(v['variant_id'],tuple(v['schedule'])) for v in c['variants']]==list(enumerate(variants))
        group=[x for x in rows if x['context_id']==c['context_id']]
        assert len(group)==len(variants)*8 and len({(x['variant_id'],x['config']['seed']) for x in group})==len(group)
        aggregate=defaultdict(lambda:[0,0,0.]);per_tape=[];originals=[];oracle=[];equivalent=[]
        for seed in range(8):
            instance=build(**c['config'],seed=seed);anchors[c['context_id'],seed]=instance;anchor=digest(instance)
            batch=sorted((x for x in group if x['config']['seed']==seed),key=lambda x:x['variant_id'])
            assert [x['variant_id'] for x in batch]==list(range(len(variants)))
            for x in batch:
                assert x['task_id']==offset+x['variant_id']*8+seed and x['schedule']==list(variants[x['variant_id']])
                assert x['physical_instance_sha256']==anchor and x['hamming_distance']==sum(a!=b for a,b in zip(x['schedule'],c['original_schedule']))
                for i,value in enumerate(metric(x)):aggregate[x['variant_id']][i]+=value
            best=min(batch,key=lambda x:(metric(x),x['schedule']));worst=max(batch,key=metric);original=batch[c['original_variant_id']]
            entry=s['per_tape'][seed];assert entry['seed']==seed and entry['lex_min']==list(metric(best)) and entry['lex_max']==list(metric(worst))
            assert entry['first_lexicographic_minimum_variant_id']==best['variant_id'] and entry['witness_task_id']==best['task_id']
            assert entry['original_key']==list(metric(original)) and entry['schedule']==best['schedule']
            counts=(len({x['physical_trace_sha256'] for x in batch}),len({x['metrics_sha256'] for x in batch}),sum(x['physical_trace_sha256']==original['physical_trace_sha256'] for x in batch))
            assert counts==(entry['distinct_physical_trajectories'],entry['distinct_metric_outcomes'],entry['original_physical_equivalent_variants'])
            per_tape.append(list(metric(best)));originals.append(list(metric(original)));equivalent.append(counts[2]);bestrows[c['context_id'],seed]=best
        ranked=sorted(aggregate,key=lambda v:(aggregate[v],list(variants[v])))
        assert s['best_common_fixed_variant']['variant_id']==ranked[0]
        assert s['best_common_fixed_variant']['schedule']==list(variants[ranked[0]])
        for a,b in zip(aggregate[ranked[0]],s['best_common_fixed_variant']['aggregate_key']):near(a,b)
        oracle=[sum(x[i] for x in per_tape) for i in range(3)];original=[sum(x[i] for x in originals) for i in range(3)]
        for a,b in zip(oracle,s['offline_per_tape_oracle_aggregate_key']):near(a,b)
        for a,b in zip(original,s['original_common_fixed_variant']['aggregate_key']):near(a,b)
        summaries.append(dict(orders=c['config']['orders'],variants=len(variants),original_key=original,
                              best_common_fixed_key=aggregate[ranked[0]],finite_per_tape_oracle_key=oracle,
                              original_equivalent_variant_counts=equivalent))
        offset+=len(variants)*8
    assert offset==12184 and len(protocol['tasks'])==12184
    for task in protocol['tasks']:
        row=rows[task['task_id']]
        for field in ('context_id','variant_id','schedule','config','actor_seed','phase','hamming_distance','retain_trace'):assert task[field]==row[field]
    for witness in witnesses:
        best=bestrows[witness['context_id'],witness['config']['seed']]
        assert witness['task_id']==best['task_id'] and witness['metrics']==best['metrics']
        assert witness['physical_trace_sha256']==best['physical_trace_sha256']
    trace_checks=[]
    for row in raw:
        if 'trace_path' not in row:continue
        path=DATA/'results'/Path(row['trace_path']).name;payload=gzip.decompress(path.read_bytes())
        assert hashlib.sha256(payload).hexdigest()==row['trace_sha256'];trace=json.loads(payload)
        instance=anchors[row['context_id'],row['config']['seed']]
        assert trace['instance']==instance and digest(instance)==row['physical_instance_sha256']
        checked=check_trace(trace,deepcopy(instance));identity=audit_trace(trace,instance)
        assert checked['valid'] and checked['terminal_requirements_met'] and identity['valid']
        assert trace['metrics']==row['metrics'] and digest({k:trace[k] for k in ('operations','moves','worker_moves','events','energy','metrics')})==row['physical_trace_sha256']
        assert checked['metrics']['unfulfilled_orders']==metric(row)[0] and checked['metrics']['terminal_deadline_debt_ticks']==metric(row)[1]
        near(checked['metrics']['total_cost'],metric(row)[2])
        for d in trace['decisions']:
            action=row['schedule'][min(d['tick']//720,7)]
            assert d['action_id']=='adaptive-recovery-schedule-'+str(action)
        trace_checks.append(dict(phase=row['phase'],task_id=row['task_id'],trace_sha256=row['trace_sha256'],valid=True))
    assert len(trace_checks)==27
    primary_attained=0
    for entry in bounds['rows']:
        fresh=certificate(anchors[entry['context_id'],entry['config']['seed']])
        assert json.loads(json.dumps(fresh))==entry['certificate'] and fresh['unfulfilled_lower_bound']==entry['necessary_missing_lower_bound']==0
        best=bestrows[entry['context_id'],entry['config']['seed']];upper=metric(best)[0]
        assert upper==entry['finite_neighborhood_witness_missing_upper_bound']==entry['primary_interval_width']
        assert entry['primary_optimum_certified']==(upper==0);primary_attained+=int(upper==0)
    assert len(bounds['rows'])==24 and primary_attained==9
    return dict(schema='stage2-independent-train-finite-headroom-audit.v1',valid=True,grid_rows=12184,
                separate_oracle_replays=24,retained_physical_identity_replays=27,contexts=summaries,
                recomputed_necessary_bounds=24,primary_optimum_attained_instances=9,all_necessary_lower_bounds_zero=True,
                report_sha256=sha(DATA/'results/report.json'),protocol_sha256=sha(DATA/'results/protocol.json'),
                retention_analysis_sha256=sha(DATA/'retention-analysis.json'),bound_supplement_sha256=sha(DATA/'necessary-bound-supplement.json'),
                trace_checks=trace_checks,source_sha256=sha(__file__),factory_simulations=0,
                wall_seconds=time.perf_counter()-began,
                scope='TRAIN0–7 only, complete radius1/radius2 schedule neighborhoods, no held-out result or full6^8 optimum. Each fixed schedule is causal time-only; per-tape hindsight choice is not deployable. Improved checked witnesses demonstrate limited controller headroom on these tapes, not factory capacity or positive global optimality-gap lower bounds. Final policies/evidence remain unchanged.')


if __name__=='__main__':
    result=audit()
    with (ROOT/'train-headroom-audit.json').open('x') as stream:stream.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='trace_checks'},indent=2))
