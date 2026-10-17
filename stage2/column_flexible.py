"""Machine/crew/time-flexible suffix columns, without a global CP teacher."""
import time

from .column_qubo import subproblem
from .window_qubo import assignments,check_plan,digest


def enrich_flexible(problem,columns,max_columns=48,radius=120):
    if max_columns<max(map(len,columns.values())):raise ValueError('Cap must retain all original columns')
    began=time.perf_counter();cpu=time.process_time();ops={o['id']:o for o in problem['operations']}
    domains={name:sorted(assignments(problem,op),key=lambda r:(r['end'],r['start'],r['machine'],r['worker']))for name,op in ops.items()}
    output={};stats={}
    for name,original in columns.items():
        ids={r['operation']for r in original[0]};raw=subproblem(problem,ids);pool={digest(sorted(p,key=lambda r:r['operation'])):p for p in original};attempts=0
        def variants(plan,suffix,late):
            nonlocal attempts
            ordered=sorted(plan,key=lambda r:r['start']);targets=ordered[-min(suffix,len(ordered)):];states=[{r['operation']:r for r in plan}]
            for old in targets:
                nextstates=[];seen=set()
                options=[r for r in domains[old['operation']]if abs(r['start']-old['start'])<=radius and(r['start']>old['start']if late else r['end']<=old['end'])]
                if late:options.sort(key=lambda r:(r['start']-old['start'],r['end'],r['machine'],r['worker']))
                for state in states:
                    for row in options:
                        signature=(row['machine'],row['worker'])
                        # Up to three structurally distinct choices at each stage;
                        # never select by the global objective or CP reference.
                        if (tuple((k,v['start'],v['machine'],v['worker'])for k,v in state.items()),signature)in seen:continue
                        candidate=dict(state);candidate[row['operation']]=row;attempts+=1
                        # While constructing a two-event suffix, validate only
                        # already assigned prefix/suffix events. The final full
                        # component check below restores every omitted event.
                        processed={r['operation']for r in targets[:targets.index(old)+1]};pending={r['operation']for r in targets}-processed
                        partial=[v for oid,v in candidate.items()if oid not in pending];partial_ids={r['operation']for r in partial}
                        if check_plan(subproblem(problem,partial_ids),partial)['valid']:
                            seen.add((tuple((k,v['start'],v['machine'],v['worker'])for k,v in state.items()),signature));nextstates.append(candidate)
                            if sum(1 for key in seen if key[0]==tuple((k,v['start'],v['machine'],v['worker'])for k,v in state.items()))>=3:break
                states=nextstates[:9]
                if not states:break
            result=[]
            for state in states:
                candidate=sorted(state.values(),key=lambda r:r['operation'])
                if check_plan(raw,candidate)['valid']:
                    key=digest(candidate)
                    if key not in pool:result.append((key,candidate))
            return result
        # Longer suffixes allow earlier machining changes to propagate through
        # downstream calendar cliffs. Each strategy gets one variant per parent
        # before the next strategy, preserving diversity under the pool cap.
        for suffix,late,per_parent in((5,False,1),(3,False,1),(2,False,1),(1,False,1),
                                     (5,True,1),(3,True,1),(2,True,1),(1,True,1)):
            for plan in original:
                if len(pool)>=max_columns:break
                added=0
                for key,candidate in variants(plan,suffix,late):
                    if key not in pool:pool[key]=candidate;added+=1
                    if added>=per_parent or len(pool)>=max_columns:break
            if len(pool)>=max_columns:break
        output[name]=list(pool.values());stats[name]=dict(original=len(original),retained=len(pool),raw_checks=attempts)
    return output,dict(method='qualified crew/machine/time-flexible suffix list generation',suffix_lengths=[5,3,2,1],radius=radius,max_columns=max_columns,groups=stats,
        cp_teacher_used=False,wall_seconds=time.perf_counter()-began,process_cpu_seconds=time.process_time()-cpu,
        scope='Raw unary domains and partial/full component checks only. Complete parent schedules retained. Global BOM/resource interactions and global objective left to master optimization.')
