"""Build selection-biased matched recovery diagnostics from retained traces only."""
import hashlib
import json
from copy import deepcopy
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from stage2.check import check_trace
BASE=ROOT/'output/stage2-search/physical-kit-recovery-diagnostic'
def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def canonical(data):return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def main():
    source_report=BASE/'report.json';control_report=BASE/'matched-control/report.json'
    report=read(source_report);controls=read(control_report);pairs=[];sources={str(p.relative_to(ROOT)):sha(p)for p in (source_report,control_report)}
    for control in controls['rows']:
        seed=control['seed'];row=next(row for row in report['rows']if row['version']=='current-default'and row['seed']==seed)
        paths=[ROOT/control['trace_path'],ROOT/row['trace_path']];before,after=[read(p)for p in paths]
        assert sha(paths[0])==control['trace_sha256']and sha(paths[1])==row['trace_sha256']
        assert before['instance']==after['instance'],'Matched physical instances required'
        checks=[check_trace(trace)for trace in (before,after)]
        assert all(check['valid']and check['terminal_requirements_met']for check in checks)
        old_policy=before['provenance']['physical_kit_recovery'];new_policy=after['provenance']['physical_kit_recovery']
        assert old_policy['enabled']is False and new_policy['enabled']is True
        assert {k:v for k,v in old_policy.items()if k!='enabled'}=={k:v for k,v in new_policy.items()if k!='enabled'}
        sources.update({str(p.relative_to(ROOT)):sha(p)for p in paths})
        pair=dict(seed=seed,instance_sha256=canonical(after['instance']),source_sha256=row['source_hashes'],
            before=dict(trace_path=control['trace_path'],trace_sha256=sha(paths[0]),metrics=before['metrics'],fresh_check=checks[0]),
            after=dict(trace_path=row['trace_path'],trace_sha256=sha(paths[1]),metrics=after['metrics'],fresh_check=checks[1]),
            recovery_policy=new_policy,completed_recoveries=row['completed_recoveries'],retargets=row['retargets'],timeouts=row['timeouts'])
        pairs.append(pair)
        if seed==8:
            move_by={move['id']:move for move in after['moves']};events=[]
            for history in after['algorithm_audit']['physical_kit_recovery']['history']:
                for leg in history['executed_legs']:
                    move=move_by[leg['move_id']]
                    assert move['unit_id']==leg['unit_id']and move['from']==leg['source']and move['to']==leg['destination']
                    events.append(dict(kind='transport',tick=move['start'],unit_id=move['unit_id'],origin=move['from'],destination=move['to'],
                        move_id=move['id'],agv_id=move['agv_id'],pickup_tick=move['pickup_tick'],drop_tick=move['drop_tick'],route_legs=move['legs']))
                if history['status']=='assembled':
                    op=next(op for op in after['operations']if op['process']=='ASSEMBLY'and op['order_id']==history['order_id']and op['start']==history['finished_tick'])
                    parents=op['parent_unit_ids'];assert len(set(parents))==3 and all(uid.split('/')[0]==op['order_id']for uid in parents)
                    consumed={event['unit_id']for event in after['events']if event['type']=='consume'and event.get('parent_operation')==op['id']and event['tick']==op['start']}
                    assert consumed==set(parents)
                    events.append(dict(kind='assembly_start',tick=op['start'],end_tick=op['end'],order_id=op['order_id'],
                        machine_id=op['machine_id'],operation_id=op['id'],parent_unit_ids=parents))
                else:
                    events.append(dict(kind='retarget',tick=history['finished_tick'],previous_order_id=history['order_id'],status=history['status'],counts_as_assembled=False))
            pair['actual_recovery_steps']=sorted(events,key=lambda item:(item['tick'],item['kind']!='retarget'))
            pair['viewer_replays']=[]
            for original,checked,path,name in zip((before,after),checks,paths,('recovery-train8-before.json','recovery-train8-after.json')):
                replay=deepcopy(original)
                replay['validation']=dict(checked,status='passed'if checked['valid']else'failed')
                replay['provenance']['viewer_validation']=dict(source_trace_sha256=sha(path),
                    checker_sha256=sha(ROOT/'stage2/check.py'),activity_data_changed=False,
                    annotation='Fresh independent check attached only to viewer copy; original retained trace and metrics preserved')
                destination=ROOT/'presentation/stage2/traces'/name
                destination.write_text(json.dumps(replay,separators=(',',':'))+'\n')
                pair['viewer_replays'].append(dict(path=str(destination.relative_to(ROOT)),sha256=sha(destination),
                    source_trace_sha256=sha(path),validation_annotation_only=True))
    out=dict(schema='matched-recovery-viewer-evidence.v1',selection_role=report['scope'],tick_minutes=after['tick_minutes'],
        validation_tapes=0,final_tapes=0,matched_control_parameters={k:v for k,v in controls.items()if k!='rows'},
        pairs=pairs,sources_sha256=sources,
        score_definition='Engine total_tardiness_ticks is cutoff-censored deadline debt; fresh_check.metrics.tardiness_ticks is delivered-only; incomplete eventual lateness remains unknown',
        scope='Four deliberately selected failed TRAIN tapes, not a random cohort or general deadlock guarantee',
        mechanism='All recovery legs are actual existing-AGV transfers; assembly consumes original matched parents; no extra capacity/resources')
    destination=Path(__file__).resolve().parent/'report.json';destination.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps([dict(seed=p['seed'],before=p['before']['metrics']['shipped'],after=p['after']['metrics']['shipped'],orders=p['after']['metrics']['orders'])for p in pairs]))

if __name__=='__main__':main()
