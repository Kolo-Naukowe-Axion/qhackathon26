"""Add internally checked route-suffix retimings without a global optimizer."""
from copy import deepcopy
import time

from .column_qubo import subproblem
from .window_qubo import check_plan,digest


def enrich(problem,columns,max_columns=32,offsets=(-15,-30,-60,15,30,60)):
    if any(delta%problem['grid']for delta in offsets):raise ValueError('Offsets must preserve declared start grid')
    began=time.perf_counter();cpu=time.process_time();result={};details={}
    for name,original in columns.items():
        ids={r['operation']for r in original[0]};raw=subproblem(problem,ids);pool={digest(sorted(p,key=lambda r:r['operation'])):deepcopy(p)for p in original}
        attempts=0;valid=0;longest=max(len(p)for p in original)
        # Terminal suffix first; a whole-route shift alone can be blocked by an
        # early release even when later work has avoidable idle gaps.
        for suffix in range(1,longest+1):
            if len(pool)>=max_columns:break
            for delta in offsets:
                if len(pool)>=max_columns:break
                for plan in original:
                    if len(pool)>=max_columns:break
                    ordered=sorted(plan,key=lambda r:r['start']);shift={r['operation']for r in ordered[-suffix:]};candidate=[]
                    for row in plan:
                        new=dict(row)
                        if row['operation']in shift:
                            for key in('start','end','attended_end'):new[key]+=delta
                        candidate.append(new)
                    attempts+=1
                    if check_plan(raw,candidate)['valid']:
                        valid+=1;pool[digest(sorted(candidate,key=lambda r:r['operation']))]=candidate
        result[name]=list(pool.values());details[name]=dict(original=len(original),retained=len(pool),attempted_retimings=attempts,internally_valid_retimings=valid)
    return result,dict(method='raw-checked fixed-resource suffix retiming',max_columns=max_columns,offsets=list(offsets),groups=details,
        cp_teacher_used=False,wall_seconds=time.perf_counter()-began,process_cpu_seconds=time.process_time()-cpu,
        scope='Future machine/worker identities and durations retained, selected route suffix start/end/attendance times shifted. Cross-component BOM/resource feasibility is left to the QUBO, not silently assumed.')
