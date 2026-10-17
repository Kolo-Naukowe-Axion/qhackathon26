"""Scope-guarded worker/prefix union bound for the held automatic fixture.

No optimization, factory execution, CP search, or saved source modification.
"""
from collections import defaultdict
import hashlib
import heapq
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SOURCE_HASHES={
    'stage2/reference.py':'ffd604b8e5da58bd789cdc24cdf7bdc69f18ea984a28b4d843c718326d8c5732',
    'stage2/reference_multi.py':'226dced1939ee824a0e661d4112efc488be4de3286e6280e9da4e58163700efe',
    'stage2/check.py':'40c96bf26f19aa10e33566332d55133f8bd73c32878753668202b4690ce4bf5b',
    'stage2/engine.py':'ec97bf3c1e57110cc0ddef02e54fafc2626b3aab079718a8ab0f04a5ba26244f'}
ROUTES={
    'housing':(('T',60),('F',90),('WASH',30),('HEAT',120),('QA',45)),
    'rotor':(('T',60),('HEAT',120),('F',75),('WASH',30),('QA',45)),
    'flange':(('F',60),('S',60),('WASH',30),('QA',45)),
    'pump':(('ASSEMBLY',60),('QA',45))}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def require(condition,message):
    if not condition:raise ValueError('Outside union-bound scope: '+message)


def loaded_distance(instance,a,b):
    graph=defaultdict(list)
    for edge in instance['graph_edges']:
        graph[edge['a']].append((edge['b'],edge['ticks']));graph[edge['b']].append((edge['a'],edge['ticks']))
    queue=[(0,a)];seen=set()
    while queue:
        distance,node=heapq.heappop(queue)
        if node in seen:continue
        if node==b:return distance+instance['transport']['load_ticks']+instance['transport']['unload_ticks']
        seen.add(node)
        for target,ticks in graph[node]:heapq.heappush(queue,(distance+ticks,target))
    raise ValueError('Disconnected required nodes')


def guard(instance):
    for name,expected in SOURCE_HASHES.items():require(sha(ROOT/name)==expected,'held physical/reference source changed: '+name)
    n=len(instance['orders']);require(1<=n<=4,'only1–4 pumps')
    if n==1:
        from stage2.reference import validate_scope
    else:
        from stage2.reference_multi import validate_scope
    validate_scope(instance)
    require({r:tuple((s['process'],s['base_ticks']) for s in route) for r,route in instance['recipes'].items()}==ROUTES,'exact scale15 mandatory routes')
    stations={m['process']:m for m in instance['machines']}
    require(set(stations)=={'T','F','S','WASH','HEAT','QA','ASSEMBLY'} and len(stations)==len(instance['machines']),'one station per process')
    require(all(stations[p]['hall']=='A' for p in ('T','F','WASH','HEAT','QA')) and all(stations[p]['hall']=='B' for p in ('S','ASSEMBLY')),'declared A/B placement')
    require(instance['workers'][0]['initial_hall']=='A' and instance['worker_travel_ticks']==2,'worker initiallyA, hall walk2')
    require(all(m['input_capacity']==(3 if m['process']=='ASSEMBLY' else 1) for m in stations.values()),'exact input capacities')
    require(instance.get('output_blocking',True) is True,'blocking outputs')
    require(all(m.get('output_capacity',1)==m.get('output_buffer_capacity',1)==1 for m in stations.values()),'one blocked output per machine')
    require(all(instance['attendance'][p]['kind']=='full' for p in ('S','QA','ASSEMBLY')),'S/QA/assembly fully attended')
    require(all(instance['attendance'][p]['kind']=='start' and instance['attendance'][p]['ticks']==5 for p in ('T','F','WASH','HEAT')),'five-minute automatic start attendance')
    require(all(set(u)=={'id','order_id','recipe','family','release_tick','initial_location'} and u['initial_location']=='RAW_A' and u['release_tick']==0 for u in instance['units']),'unmodified original RAW demand only')
    require(not any(k in instance for k in ('initial_wip','initial_accepted_units','accepted_components','initial_state')),'no accepted/WIP inventory')
    require(loaded_distance(instance,'RAW_A',stations['T']['id'])==loaded_distance(instance,'RAW_A',stations['F']['id'])==4,'initial loaded delivery4')
    require(loaded_distance(instance,stations['F']['id'],stations['S']['id'])==8,'flange F-to-S loaded transfer8')
    require(loaded_distance(instance,stations['QA']['id'],'SHIP_B')==8,'final loaded shipping8')
    return n


def overlap_compensation(outward_start,prefix_end=64,walk=2,first_B_earliest=72):
    """Algebra for the only selected walk that can intersect the prefix."""
    require(outward_start>=0,'nonnegative time')
    overlap=max(0,min(prefix_end,outward_start+walk)-outward_start)
    gap=max(0,first_B_earliest-max(prefix_end,outward_start+walk)) if overlap else 0
    require(gap>=overlap,'required post-prefix compensation unavailable')
    return dict(overlap=overlap,post_prefix_gap_lower_bound=gap)


def certificate(instance):
    n=guard(instance)
    per_pump=sum(step['base_ticks'] if instance['attendance'][step['process']]['kind']=='full' else 5
                 for route in instance['recipes'].values() for step in route)
    require(per_pump==350,'mandatory attendance350 per pump')
    components=dict(mandatory_attendance=350*n,prefix_nonattendance=54,
                    selected_required_hall_walks=4*(n+1),last_pump_QA_shipping=8)
    return dict(schema='tiny-automatic-prefix-walk-union-bound.v1',pumps=n,
                instance_sha256=digest(instance),lower_bound_ticks=sum(components.values()),
                previous_buffer_bound_ticks=350*n+54+2*(2*n+1)+8,
                improvement_ticks=2,components=components,
                first_possible_process_completion=64,maximum_mandatory_attendance_before64=10,
                first_possible_mandatory_B_start=72,productive_B_visits_at_least=n+1,
                selected_walks_at_least=2*(n+1),source_hashes=SOURCE_HASHES,
                proof='Let P=[0,64) minus required attendance, measure>=54. Reserved ASM capacity3 plus one QA output allow atmost4 accepted unconsumed components; no QA can complete while sole worker is inB. Each productive B excursion starts atmostone assembly, and the first must weld before any assembly, giving n+1 excursions and2(n+1) selected2-minute walks. Only the first selected outward walk can overlap P, by o<=2. If it does, arrival b<=66, while first required B work starts>=72, so G=[max(64,b),72) has measure>=o and is disjoint from P, selected walks and required attendance. Therefore union(P,selectedwalks,G) has measure>=54+4(n+1). Add350n disjoint required attendance and8 final shipping after the last full pumpQA. Extra unproductive early walks do not invalidate the union argument; no claim that all nonwalking idle alone is>=54 is needed.',
                proof_scope='Exact guarded deterministic automatic-attendance1–4-pump reference; no global flagship gap, no saved CP-bound modification',
                deliberately_excluded=['Per-pump join or transport gaps that can overlap other attendance','Additional productive/unproductive walks','Extra empty AGV travel','Any secondary cost optimum'],
                source_sha256=sha(__file__),factory_simulations=0,cp_solver_calls=0)
