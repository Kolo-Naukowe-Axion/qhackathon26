"""Audit retained campaign aggregation and export labeled viewer-only evidence."""
from collections import defaultdict
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'output/stage2-search/axion-download-2305'
def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def campaign(name):
    root=BASE/name;paths=[root/file for file in ('summary.json','protocol.json','measurements.jsonl')]
    summary=read(paths[0]);protocol=read(paths[1]);measurements=[json.loads(line)for line in paths[2].read_text().splitlines()if line]
    tasks={task['task_id']:task for task in protocol['tasks']}
    assert len(tasks)==len(protocol['tasks'])==summary['requested']==summary['completed']==len(measurements)
    assert {row['task_id']for row in measurements}==set(tasks)
    assert all(row['valid']for row in measurements),'Suppress performance export if any invalid outcome exists'
    grouped=defaultdict(list)
    for row in measurements:
        task=tasks[row['task_id']]
        assert row['policy_id']==task['policy_id']and row['config']==task['config']and row['weights']==task['weights']
        assert task['seed_role']in ('TRAIN','VALIDATION')and task['config']['seed']<10000
        grouped[row['policy_id'],row['config']['orders']].append((row,task))
    groups=[]
    for group in summary['rows']:
        rows=grouped[group['policy_id'],group['orders']];n=len(rows)
        assert n==group['runs']==group['valid']
        metrics=[row['metrics']for row,_ in rows]
        checks={'mean_shipped':sum(m['shipped']for m in metrics)/n,
            'mean_unfulfilled':sum(m['orders']-m['shipped']for m in metrics)/n,
            'mean_tardiness_minutes':sum(m['total_tardiness_ticks']for m in metrics)/n,
            'mean_total_cost':sum(m['total_cost']for m in metrics)/n,
            'complete_runs':sum(m['all_orders_fulfilled']for m in metrics)}
        for key,value in checks.items():assert abs(group[key]-value)<1e-7,(name,key,group[key],value)
        roles={task['seed_role']for _,task in rows};horizons={task['config']['horizon']for _,task in rows}
        assert len(roles)==len(horizons)==1
        seeds=sorted(task['config']['seed']for _,task in rows);assert len(set(seeds))==n
        assert all(task['solver_options']==rows[0][1]['solver_options']for _,task in rows)
        groups.append(dict(group,seed_role=roles.pop(),horizon_ticks=horizons.pop(),seeds=seeds,
            max_unfulfilled=max(m['orders']-m['shipped']for m in metrics),
            solver_variant=rows[0][1]['solver_variant'],solver_options=rows[0][1]['solver_options'],selection=rows[0][1].get('selection',{})))
    assert len(groups)==len(grouped)
    return dict(campaign=name,completed=summary['completed'],requested=summary['requested'],all_valid=True,
        groups=groups,job_wall_seconds=summary['wall_seconds'],workers=protocol['workers'],
        source_snapshot=protocol['source_snapshot'],source_sha256={str(path.relative_to(ROOT)):sha(path)for path in paths})

def horizon_scope_audit(groups):
    source=ROOT/'output/stage2-search/snapshots/v7-kitting/stage2/spec.py'
    spec=importlib.util.spec_from_file_location('frozen_horizon_scope',source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    configs={(group['orders'],seed,group['horizon_ticks'])for group in groups for seed in group['seeds']}
    references={};checked=0
    for orders,seed,horizon in sorted(configs):
        instance=module.build(orders=orders,seed=seed,horizon=horizon,profile='full')
        normalized=deepcopy(instance);normalized.pop('horizon_ticks')
        key=orders,seed
        if key not in references:references[key]=normalized
        else:assert normalized==references[key],(key,horizon);checked+=1
    return dict(numerical_instance_comparisons=checked,unique_order_seed_cases=len(references),
        tick_minutes=instance['tick_minutes'],
        only_changed_instance_field='horizon_ticks',initial_due_dates_unchanged=True,physical_resources_unchanged=True,
        independent_rebuild_source=str(source.relative_to(ROOT)),source_sha256=sha(source),
        interpretation='Additional calendar time supplies more resource-hours; this is not an algorithmic speedup or96-hour success')

def main():
    recovery=campaign('physical-recovery-6117261');horizon=campaign('strong-horizon-6117258')
    audit=horizon_scope_audit(horizon['groups'])
    horizon['tick_minutes']=audit['tick_minutes']
    out=dict(schema='stage2-later-frontier-evidence.v1',recovery=recovery,horizon=horizon,horizon_scope_audit=audit,
        final_evaluation_tapes_used=0,score_definition='mean_tardiness_minutes is cutoff-censored deadline debt; incomplete eventual lateness is unknown',
        selection_scope='TRAIN and VALIDATION are development cohorts; no untouched final-evaluation inference')
    path=Path(__file__).resolve().parent/'report.json';path.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(dict(recovery_runs=recovery['completed'],horizon_runs=horizon['completed'],horizon_scope_audit=audit)))

if __name__=='__main__':main()
