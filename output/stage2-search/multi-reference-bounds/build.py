"""Independent arithmetic certificate; does not change frozen CP experiments."""
from collections import defaultdict
from copy import deepcopy
import argparse
import hashlib
import heapq
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from stage2.reference_multi import validate_scope

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def certificate(instance):
    validate_scope(instance)
    if any(rule['kind']!='full'for rule in instance['attendance'].values()):raise ValueError('Every process must reserve the worker throughout')
    stations={m['process']:m for m in instance['machines']}
    if any(stations[p]['hall']!='A'for p in ('T','F','WASH','HEAT','QA'))or any(stations[p]['hall']!='B'for p in ('S','ASSEMBLY')):
        raise ValueError('Hall proof requires declared A/B station placement')
    if instance['workers'][0]['initial_hall']!='A':raise ValueError('Initial worker must be in A')
    graph=defaultdict(list)
    for edge in instance['graph_edges']:
        graph[edge['a']].append((edge['b'],edge['ticks']));graph[edge['b']].append((edge['a'],edge['ticks']))
    def distance(origin,destination):
        queue=[(0,origin)];visited=set()
        while queue:
            cost,node=heapq.heappop(queue)
            if node in visited:continue
            if node==destination:return cost
            visited.add(node)
            for neighbor,ticks in graph[node]:heapq.heappush(queue,(cost+ticks,neighbor))
        raise ValueError('Disconnected required path')
    handling=instance['transport']['load_ticks']+instance['transport']['unload_ticks']
    n=len(instance['orders'])
    processing=n*sum(step['base_ticks']for route in instance['recipes'].values()for step in route)
    initial=min(distance('RAW_A',stations[instance['recipes'][recipe][0]['process']]['id'])+handling
        for recipe in ('housing','rotor','flange'))
    final=distance(stations['QA']['id'],'SHIP_B')+handling
    walk=4*instance['worker_travel_ticks']
    pieces=dict(all_mandatory_processing=processing,first_loaded_delivery=initial,
        four_forced_worker_hall_walks=walk,last_pump_QA_shipping=final)
    return dict(schema='tiny-multi-full-attendance-bound.v1',pumps=n,components=pieces,lower_bound_ticks=sum(pieces.values()),
        forced_hall_subsequence=['A:first raw operation','B:flange weld','A:flange wash/QA','B:matching assembly','A:final pump QA'],
        proof='Single full-attendance worker makes all process and walk intervals disjoint. Initial delivery precedes every process; last required process is final pump QA, followed by shipping. Witness chain forces four hall transitions inside the processing span.',
        deliberately_excluded=['Per-pump join gaps','Additional walks','Empty repositioning','Buffer blocking'],
        flagship_bound=False,changes_saved_cp_bound=False)

def automatic_certificate(instance):
    """Guarded initial-wait/worker-walk bound for the scale15 automatic fixture."""
    validate_scope(instance)
    stations={m['process']:m for m in instance['machines']}
    if any(stations[p]['hall']!='A'for p in ('T','F','WASH','HEAT','QA'))or any(stations[p]['hall']!='B'for p in ('S','ASSEMBLY')):
        raise ValueError('Automatic proof requires declared A/B station placement')
    if instance['workers'][0]['initial_hall']!='A':raise ValueError('Initial worker must be in A')
    first=[instance['recipes'][recipe][0]for recipe in ('housing','rotor','flange')]
    if any(step['process']not in ('T','F')or step['base_ticks']<60 for step in first):
        raise ValueError('Automatic prefix proof requires every first T/F duration at least60')
    for process in ('T','F'):
        rule=instance['attendance'][process]
        if rule['kind']!='start'or rule['ticks']!=5:raise ValueError('Initial T/F attendance must be five start minutes')
    if any(instance['attendance'][p]['kind']!='full'for p in ('S','QA','ASSEMBLY')):
        raise ValueError('Witness walk/shipping proof requires full S/QA/assembly attendance')
    # Reuse guarded shortest-distance arithmetic, not its full-attendance premise.
    numerical=deepcopy(instance)
    for rule in numerical['attendance'].values():rule['kind']='full'
    full=certificate(numerical)
    initial=full['components']['first_loaded_delivery']
    if initial<4:raise ValueError('Initial loaded delivery must take at least four minutes')
    prefix=4+60
    maximum_prefix_attendance=2*5
    n=len(instance['orders']);attendance=0
    for route in instance['recipes'].values():
        for step in route:
            rule=instance['attendance'][step['process']]
            attendance+=step['base_ticks']if rule['kind']=='full'else min(rule['ticks'],step['base_ticks'])
    pieces=dict(all_mandatory_attendance=n*attendance,
        initial_prefix_without_mandatory_attendance=prefix-maximum_prefix_attendance,
        three_forced_worker_walks_after_first_completion=3*instance['worker_travel_ticks'],
        last_pump_QA_shipping=full['components']['last_pump_QA_shipping'])
    return dict(schema='tiny-multi-automatic-bound.v1',pumps=n,components=pieces,lower_bound_ticks=sum(pieces.values()),
        earliest_process_completion_ticks=prefix,maximum_attendance_before_that_tick=maximum_prefix_attendance,
        proof='Before64 no process completes: raw delivery>=4 and all first T/F durations>=60. Single T and F permit at most two starts, totaling<=10 mandatory attendance. This leaves>=54 non-attendance minutes in that prefix. After flange weld completes, its chain requires B-to-A, A-to-B, B-to-A walks, all after64 and disjoint from mandatory attendance. Last mandatory processing is full pumpQA, followed by shipping.',
        guards=['All components initially RAW_A, release0','One fixed T and one fixed F','Every first T/F processing duration>=60',
            'First T/F start attendance exactly5','Initial loaded delivery>=4','Fixed two-hall layout','Full S/QA/assembly attendance',
            'Zero setups; deterministic recipes; no binding service or hidden events'],
        deliberately_excluded=['The first A-to-B walk, which may overlap prefix non-attendance','Per-pump join gaps',
            'Additional walks','Empty repositioning','Buffer blocking'],
        flagship_bound=False,changes_saved_cp_bound=False)

def buffer_bom_certificate(instance):
    """One full matched kit per productive B visit, conditional on exact storage."""
    validate_scope(instance)
    stations={m['process']:m for m in instance['machines']}
    if stations['ASSEMBLY']['input_capacity']!=3:raise ValueError('Buffer proof requires assembly input capacity exactly3')
    if stations['QA'].get('output_capacity',1)!=1 or stations['QA'].get('output_buffer_capacity',1)!=1:
        raise ValueError('Buffer proof requires exactly one held QA output')
    if any(instance['attendance'][p]['kind']!='full'for p in ('QA','ASSEMBLY')):
        raise ValueError('QA and assembly must fully attend the sole worker')
    unit_fields={'id','order_id','recipe','family','release_tick','initial_location'}
    if any(set(unit)!=unit_fields for unit in instance['units']):raise ValueError('No initial accepted/WIP state extensions allowed')
    if any(key in instance for key in ('initial_wip','initial_accepted_units','accepted_components','initial_state')):
        raise ValueError('No initial accepted/WIP inventory allowed')
    if instance.get('output_blocking',True)is not True:raise ValueError('Held machine output blocking is required')
    full=all(rule['kind']=='full'for rule in instance['attendance'].values())
    prior=(certificate if full else automatic_certificate)(instance)
    n=len(instance['orders']);walk=instance['worker_travel_ticks'];parts=dict(prior['components'])
    if full:
        parts.pop('four_forced_worker_hall_walks');parts['buffer_forced_worker_hall_walks']=2*(n+1)*walk
    else:
        parts.pop('three_forced_worker_walks_after_first_completion');parts['buffer_forced_walks_after_initial_prefix']=(2*n+1)*walk
    return dict(schema='tiny-multi-buffer-bom-bound.v1',pumps=n,attendance='full'if full else'automatic',
        lower_bound_ticks=sum(parts.values()),components=parts,
        productive_B_visits_at_least=n+1,forced_worker_hall_walks_at_least=2*(n+1),
        accepted_unconsumed_components_at_most=4,components_needed_for_two_assemblies=6,
        proof='Before a productive hallB visit, at most three accepted components occupy/reserve ASM input and one occupies QA output. Inbound moves reserve destination capacity. QA fully attends the sole worker in A, so no additional acceptance occurs during that B visit. Two assembly starts require six distinct accepted components, exceeding four; hence at most one assembly starts per B visit. The first productive B visit must weld before any flange can return A for wash/QA, so it cannot assemble a pump. Thus n+1 B visits, each returning A before final QA. Under automatic prefix assumptions, only the first outward walk may overlap the initial prefix.',
        guards=prior.get('guards',[])+['One QA station with one blocked output','One assembly station with input capacity exactly3',
            'Inbound destination reservations count against capacity','Full QA and ASM attendance by one worker',
            'No initial accepted inventory or temporary warehouses','Matched three-distinct-component BOM','Declared A/B station mapping'],
        previous_certificate_bound_ticks=prior['lower_bound_ticks'],
        deliberately_excluded=['Additional welding visits','Extra empty travel','Further blocking/join waits'],
        flagship_bound=False,changes_saved_cp_bound=False)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--buffer-bom',action='store_true',help='Write new strengthened artifacts; preserve earlier prefix/full artifacts')
    args=parser.parse_args()
    out=Path(__file__).resolve().parent
    for n in (2,3,4):
        for attendance in ('full','automatic'):
            suffix='-full'if attendance=='full'else''
            source=ROOT/f'output/stage2-search/multi-reference-pilot/n{n}-scale15{suffix}/instance.json'
            instance=json.loads(source.read_text());data=(buffer_bom_certificate if args.buffer_bom else certificate if attendance=='full'else automatic_certificate)(instance)
            data.update(instance_path=str(source.relative_to(ROOT)),instance_file_sha256=sha(source),
                construction_source_sha256=sha(Path(__file__)),reference_guard_sha256=sha(ROOT/'stage2/reference_multi.py'))
            destination=out/f'n{n}-{attendance}{"-buffer"if args.buffer_bom else""}.json'
            if args.buffer_bom:
                earlier=out/f'n{n}-{attendance}.json';data['previous_certificate_file_sha256']=sha(earlier)
            destination.write_text(json.dumps(data,indent=2)+'\n')
            print(json.dumps(dict(pumps=n,attendance=attendance,lower_bound_ticks=data['lower_bound_ticks'],components=data['components'])))

if __name__=='__main__':main()
