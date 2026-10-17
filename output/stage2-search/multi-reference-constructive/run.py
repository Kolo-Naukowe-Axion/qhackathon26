"""Construct checked multi-pump upper bounds by concatenating physical blocks.

No CP proof state or optimum claim is transferred from a smaller instance.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from stage2.reference_multi import activities,to_trace,validate_scope
from stage2.reference import shortest_path
from stage2.check import check_trace

def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n')

def construct(pumps,blocks):
    instance=read(ROOT/f'output/stage2-search/multi-reference-pilot/n{pumps}-scale15/instance.json')
    validate_scope(instance);operations,moves=activities(instance)
    op_lookup={(op['unit_id'],op['recipe_step']):op for op in operations}
    move_lookup={(move['unit_id'],move['from'],move['to']):move for move in moves}
    schedule=dict(operations={},moves={});offset=0;order_cursor=0;previous_location=instance['agvs'][0]['initial_location'];sources=[]
    for path in blocks:
        block=read(path);checked=check_trace(block)
        assert checked['valid']and checked['all_orders_fulfilled']and checked['terminal_requirements_met']
        block_orders=[order['id']for order in block['instance']['orders']]
        mapping={oid:instance['orders'][order_cursor+i]['id']for i,oid in enumerate(block_orders)}
        remap=lambda uid:mapping[uid.split('/')[0]]+'/'+uid.split('/',1)[1]
        transport=sorted((move for move in block['moves']if move['kind']=='transport'and move['entity_type']=='part'),key=lambda move:move['start'])
        assert transport[0]['start']==transport[0]['pickup_tick']==0
        reposition=sum(ticks for _,_,ticks in shortest_path(instance,previous_location,transport[0]['from']))
        shift=offset+reposition
        for row in block['operations']:
            assert row['kind']=='process'
            op=op_lookup[remap(row['unit_id']),row['recipe_step']]
            assert op['duration']==row['end']-row['start']and op['machine_id']==row['machine_id']
            schedule['operations'][op['id']]=row['start']+shift
        for index,row in enumerate(transport):
            move=move_lookup[remap(row['unit_id']),row['from'],row['to']]
            schedule['moves'][move['id']]=dict(start=offset if index==0 else row['start']+shift,
                pickup=row['pickup_tick']+shift,drop=row['drop_tick']+shift)
        block_makespan=max(checked['metrics']['delivery_ticks'].values())
        sources.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path),orders=mapping,shift_ticks=shift,
            block_makespan_ticks=block_makespan,preceding_empty_reposition_ticks=reposition))
        offset=shift+block_makespan;previous_location=transport[-1]['to'];order_cursor+=len(block_orders)
    assert order_cursor==pumps and len(schedule['operations'])==len(operations)and len(schedule['moves'])==len(moves)
    worker_path=[0]+sorted(range(1,len(operations)+1),key=lambda i:schedule['operations'][operations[i-1]['id']])+[0]
    agv_path=[0]+sorted(range(1,len(moves)+1),key=lambda i:schedule['moves'][moves[i-1]['id']]['start'])+[0]
    schedule['worker_successors']=dict(zip(worker_path,worker_path[1:]));schedule['agv_successors']=dict(zip(agv_path,agv_path[1:]))
    trace=to_trace(instance,operations,moves,schedule)
    trace['provenance']=dict(kind='measured',solver='Constructive classical concatenation of retained physically checked blocks',
        full_instance_optimality_claim=False,source_blocks=sources)
    checked=check_trace(trace)
    assert checked['valid']and checked['all_orders_fulfilled']and checked['terminal_requirements_met'],checked
    assert max(checked['metrics']['delivery_ticks'].values())==offset
    return trace,schedule,dict(pumps=pumps,upper_bound_ticks=offset,validation=checked,source_blocks=sources,
        full_instance_optimality_claim=False,cp_proof_state_resumed=False)

def main():
    destination=Path(__file__).resolve().parent
    one=ROOT/'output/stage2-search/tiny-reference-final/automatic/optimal-trace.json'
    two=ROOT/'output/stage2-search/multi-reference-600/n2/automatic/cp-trace.json'
    reports=[]
    for pumps,blocks in ((3,[two,one]),(4,[two,two])):
        trace,schedule,report=construct(pumps,blocks)
        out=destination/f'n{pumps}';out.mkdir(exist_ok=False)
        write(out/'trace.json',trace);write(out/'schedule.json',schedule)
        report.update(trace_sha256=sha(out/'trace.json'),schedule_sha256=sha(out/'schedule.json'),
            sources_sha256={name:sha(ROOT/name)for name in ('stage2/reference_multi.py','stage2/reference.py','stage2/check.py')})
        write(out/'report.json',report);reports.append(report)
        print(json.dumps(dict(pumps=pumps,upper_bound_ticks=report['upper_bound_ticks'],valid=report['validation']['valid'])),flush=True)
    write(destination/'report.json',reports)

if __name__=='__main__':main()
