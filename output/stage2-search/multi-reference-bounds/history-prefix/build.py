"""Independent arithmetic certificate; does not change frozen CP experiments."""
from collections import defaultdict
from copy import deepcopy
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

def main():
    out=Path(__file__).resolve().parent
    for n in (2,3,4):
        for attendance in ('full','automatic'):
            suffix='-full'if attendance=='full'else''
            source=ROOT/f'output/stage2-search/multi-reference-pilot/n{n}-scale15{suffix}/instance.json'
            instance=json.loads(source.read_text());data=(certificate if attendance=='full'else automatic_certificate)(instance)
            data.update(instance_path=str(source.relative_to(ROOT)),instance_file_sha256=sha(source),
                construction_source_sha256=sha(Path(__file__)),reference_guard_sha256=sha(ROOT/'stage2/reference_multi.py'))
            (out/f'n{n}-{attendance}.json').write_text(json.dumps(data,indent=2)+'\n')
            print(json.dumps(dict(pumps=n,attendance=attendance,lower_bound_ticks=data['lower_bound_ticks'],components=data['components'])))

if __name__=='__main__':main()
