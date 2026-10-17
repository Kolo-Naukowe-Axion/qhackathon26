"""Necessary worker-capacity certificates, including indivisible attendance.

Ignore contention to derive safe earliest-start bounds. For each skill, every
attendance interval must fit one qualified worker calendar window. An unbounded
integer packing DP gives an optimistic usable-time upper bound in each window.
If even that bound is below required minimum attendance, the cell is infeasible.
Passing this check never certifies feasibility or schedule optimality.
"""
import argparse
import hashlib
import json
from pathlib import Path

from .window_interval_reference import mode_intervals
from .window_qubo import validate,digest
from .window_campaign import save


def capacity_certificate(problem):
    validate(problem)
    ops={op['id']:op for op in problem['operations']}
    grid=problem['grid']
    earliest_start,earliest_end={},{}
    while len(earliest_end)<len(ops):
        for oid,op in ops.items():
            if oid in earliest_end or not set(op['predecessors'])<=earliest_end.keys():continue
            ready=max([op['release']]+[earliest_end[p]+min(problem['transport_lags'][m][n]
                       for m in ops[p]['durations']for n in op['durations'])for p in op['predecessors']])
            possibilities=[]
            for mid,duration in op['durations'].items():
                for wid in problem['workers']:
                    for lo,hi in mode_intervals(problem,op,mid,wid):
                        tick=max(lo,(ready+grid-1)//grid)
                        if tick<=hi:possibilities.append((grid*tick,grid*tick+duration))
            if not possibilities:
                return dict(infeasible=True,reason='Empty relaxed precedence/calendar domain',operation=oid,
                            problem_sha256=digest(problem))
            earliest_start[oid]=min(start for start,end in possibilities)
            earliest_end[oid]=min(end for start,end in possibilities)
    skills=[]
    for skill in sorted({op['skill']for op in ops.values()}):
        tasks=[op for op in ops.values()if op['skill']==skill]
        first=min(earliest_start[op['id']]for op in tasks)
        def lengths(op):
            return [d if op['attendance']=='full'else min(d,op['start_attendance'])for d in op['durations'].values()]
        durations=sorted({d for op in tasks for d in lengths(op)})
        required=sum(min(lengths(op))for op in tasks)
        windows=[]
        for wid,worker in problem['workers'].items():
            if skill not in worker['skills']:continue
            for lo,hi in worker['available']:
                start=max(lo,first,worker.get('ready',0))
                end=min(hi,problem['horizon'])
                if end<=start:continue
                capacity=end-start
                reachable=[False]*(capacity+1)
                reachable[0]=True
                for time in range(1,capacity+1):
                    reachable[time]=any(time>=d and reachable[time-d]for d in durations)
                packed=max(time for time,value in enumerate(reachable)if value)
                windows.append(dict(worker=wid,start=start,end=end,raw_capacity=capacity,
                                    optimistic_packed_capacity=packed))
        total=sum(w['optimistic_packed_capacity']for w in windows)
        skills.append(dict(skill=skill,operations=len(tasks),earliest_start_lower_bound=first,
                           allowed_attendance_lengths=durations,minimum_required_attendance=required,
                           raw_capacity_upper_bound=sum(w['raw_capacity']for w in windows),
                           packed_capacity_upper_bound=total,deficit=max(0,required-total),windows=windows))
    return dict(infeasible=any(s['deficit']>0 for s in skills),problem_sha256=digest(problem),skills=skills,
                earliest_start_lower_bounds=earliest_start,earliest_end_lower_bounds=earliest_end,
                scope='Necessary bound on mandatory complete deterministic cell. Allows unlimited occurrences of any legal attendance length in each qualified calendar window, ignoring task counts, contention, walk time and machine setups. Those relaxations can only overestimate capacity. Positive deficit certifies infeasibility; no deficit is inconclusive.')


def run(problem_path,output):
    problem_path,output=Path(problem_path),Path(output)
    output.mkdir(parents=True,exist_ok=False)
    root=Path(__file__).resolve().parents[1]
    hashes={}
    for name in('stage2/window_capacity.py','stage2/window_interval_reference.py','stage2/window_qubo.py'):
        data=(root/name).read_bytes()
        target=output/'sources'/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(data)
        hashes[name]=hashlib.sha256(data).hexdigest()
    problem=json.loads(problem_path.read_text())
    certificate=capacity_certificate(problem)
    save(output/'problem.json',problem)
    save(output/'report.json',dict(certificate=certificate,source_hashes=hashes,
                                  source_problem_path=str(problem_path),source_problem_file_sha256=hashlib.sha256(problem_path.read_bytes()).hexdigest()))
    save(output/'manifest.json',{str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(output.rglob('*'))if p.is_file()})
    return dict(infeasible=certificate['infeasible'],deficits=[{k:s[k]for k in('skill','minimum_required_attendance','raw_capacity_upper_bound','packed_capacity_upper_bound','deficit')}for s in certificate.get('skills',[])if s['deficit']])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--problem',required=True)
    p.add_argument('--output',required=True)
    a=p.parse_args()
    print(json.dumps(run(a.problem,a.output),indent=2))
