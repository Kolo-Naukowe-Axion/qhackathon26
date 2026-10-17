"""Check new bound against every retained reference trace in its scope."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import time

from stage2.check import check_trace

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location('guarded_reference_union_bound',HERE/'bound.py')
B=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(B)


def audit():
    began=time.perf_counter();entries=[];out_of_scope=[];incomplete=[];invalid=[];seen={}
    for path in sorted((B.ROOT/'output/stage2-search').glob('*reference*/**/*trace*.json')):
        trace=json.loads(path.read_text())
        if not isinstance(trace,dict) or 'instance' not in trace:continue
        try:certificate=B.certificate(trace['instance'])
        except ValueError as error:
            out_of_scope.append(dict(path=str(path.relative_to(B.ROOT)),reason=str(error)));continue
        checked=check_trace(trace,deepcopy(trace['instance']))
        if not checked['valid']:
            invalid.append(dict(path=str(path.relative_to(B.ROOT)),issues=checked['issues']));continue
        if not checked['all_orders_fulfilled']:
            incomplete.append(dict(path=str(path.relative_to(B.ROOT)),unfulfilled=checked['metrics']['unfulfilled_orders']));continue
        assert checked['terminal_requirements_met']
        makespan=max(checked['metrics']['delivery_ticks'].values());assert makespan>=certificate['lower_bound_ticks']
        assert sum(i['end']-i['start'] for op in trace['operations'] for i in op['worker_intervals'])==certificate['components']['mandatory_attendance']
        first_B=min(op['start'] for op in trace['operations'] if op['process'] in ('S','ASSEMBLY'))
        assert first_B>=72
        prefix_attendance=sum(max(0,min(64,i['end'])-max(0,i['start'])) for op in trace['operations'] for i in op['worker_intervals'])
        assert prefix_attendance<=10
        # Count maximal B excursions containing mandatory B operations. Extra
        # unproductive excursions are allowed and never subtracted as idle.
        walks=sorted(trace['worker_moves'],key=lambda m:m['start']);visits=[]
        for index,walk in enumerate(walks):
            if walk['from_hall']!='A' or walk['to_hall']!='B':continue
            returning=next(w for w in walks[index+1:] if w['from_hall']=='B' and w['to_hall']=='A')
            operations=[op for op in trace['operations'] if op['process'] in ('S','ASSEMBLY') and walk['end']<=op['start'] and op['end']<=returning['start']]
            if not operations:continue
            assert sum(op['process']=='ASSEMBLY' for op in operations)<=1
            visits.append(dict(outward=walk,returning=returning,operations=[op['id'] for op in operations]))
        assert len(visits)>=certificate['productive_B_visits_at_least']
        first=visits[0]['outward'];compensation=B.overlap_compensation(first['start'])
        assert first_B>=first['end']
        assert max(0,first_B-max(64,first['end']))>=compensation['overlap']
        entries.append(dict(path=str(path.relative_to(B.ROOT)),file_sha256=B.sha(path),instance_sha256=certificate['instance_sha256'],
                            pumps=certificate['pumps'],makespan_ticks=makespan,guarded_lower_bound_ticks=certificate['lower_bound_ticks'],
                            productive_B_excursions=len(visits),prefix_attendance_ticks=prefix_attendance,
                            first_B_start=first_B,first_outward_prefix_overlap=compensation['overlap'],
                            independently_checked=True))
        seen.setdefault(certificate['pumps'],[]).append(makespan)
    assert set(seen)=={1,2,3,4} and not invalid
    specific=B.ROOT/'output/stage2-search/multi-reference-2h-axion/payload/instance.json'
    proof=B.certificate(json.loads(specific.read_text()))
    return dict(schema='tiny-automatic-prefix-walk-bound-witness-audit.v1',valid=True,
                certificate=proof,complete_witnesses_checked=len(entries),witnesses=entries,
                minimum_checked_makespan_by_pumps={str(n):min(values) for n,values in seen.items()},
                excluded_incomplete_traces=incomplete,excluded_out_of_scope=out_of_scope,invalid_in_scope_traces=invalid,
                source_hashes=dict(bound_py=B.sha(HERE/'bound.py'),audit_py=B.sha(__file__),test_py=B.sha(HERE/'test_bound.py')),
                old_certificate_sha256=B.sha(B.ROOT/'output/stage2-search/multi-reference-bounds/n4-automatic-buffer.json'),
                factory_simulations=0,solver_calls=0,wall_seconds=time.perf_counter()-began,
                scope='Every locally retained regular-JSON reference trace matching exact automatic-scale15 guards is inspected; complete valid witnesses for1–4 pumps all exceed bound. Full-attendance/compressed/changed-buffer instances are explicitly out of scope; incomplete valid traces do not supply upper bounds. Saved1480certificate, CPsources and CPbounds remain unchanged.')


if __name__=='__main__':
    result=audit()
    with (HERE/'report.json').open('x') as stream:stream.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('witnesses','excluded_out_of_scope')},indent=2))
