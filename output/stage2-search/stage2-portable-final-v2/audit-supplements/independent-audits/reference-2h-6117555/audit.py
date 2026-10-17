"""Independent frozen-reference return audit; no factory/solver calls."""
from copy import deepcopy
from fractions import Fraction as Q
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import tarfile
import time

from stage2.check import check_trace
from stage2.identity_audit import audit_trace
from stage2.reference_multi import make_multi,validate_scope,activities,to_trace,schedule_from_trace

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]
REMOTE=BASE/'multi-reference-2h-axion/completed/multi-reference-2h-20261017T0116'
ORIGINAL=BASE/'multi-reference-2h-axion/payload'
RSPEC=importlib.util.spec_from_file_location('scoped_reference_identity',HERE/'reference_identity.py')
R=importlib.util.module_from_spec(RSPEC);RSPEC.loader.exec_module(R)
NSPEC=importlib.util.spec_from_file_location('normalized_reference_witness',HERE/'normalize_witness.py')
N=importlib.util.module_from_spec(NSPEC);NSPEC.loader.exec_module(N)
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def close(a,b):
    if isinstance(a,dict):return isinstance(b,dict) and set(a)==set(b) and all(close(a[k],b[k]) for k in a)
    if isinstance(a,list):return isinstance(b,list) and len(a)==len(b) and all(close(x,y) for x,y in zip(a,b))
    if type(a) is float:return type(b) in (int,float) and math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-7)
    return a==b


def audit():
    began=time.perf_counter();manifest=read(ORIGINAL/'manifest.json');report=read(REMOTE/'result/report.json');exact=report['exact']
    assert (REMOTE/'manifest.json').read_bytes()==(ORIGINAL/'manifest.json').read_bytes()
    assert len(manifest['payload_hashes'])==9 and report['payload_hashes']==manifest['payload_hashes']
    for name,expected in manifest['payload_hashes'].items():
        assert sha(ORIGINAL/name)==sha(REMOTE/name)==expected
        if name.startswith('stage2/'):
            assert sha(Path(name))==expected
    for name,expected in report['artifact_hashes'].items():assert sha(REMOTE/'result'/name)==expected
    assert report['sources_stable_during_run'] and report['source_report_sha256']==manifest['prior_report_sha256']
    prior=BASE/'multi-reference-parallel-axion/collected/result/report.json';assert sha(prior)==manifest['prior_report_sha256']
    fresh=make_multi(pumps=4,processing_scale=15,horizon=10400,automatic_attendance=True,
                     bridge_ticks=4,input_capacity=1,dispatch_after_ready=False)
    validate_scope(fresh);instance=read(REMOTE/'instance.json');assert instance==fresh
    assert digest(instance)==report['instance_sha256']==manifest['instance_sha256']=='3c6bda8bbf315951447394c68053894ff4a756be1c63f826de7c58739b5c3f7e'
    traces={};checks={};identities={};scoped_identities={}
    sources={'new_cp':REMOTE/'result/cp-trace.json','hint':REMOTE/'hint-trace.json',
             'original_heuristic':BASE/'multi-reference-pilot/n4-scale15/heuristic-trace.json'}
    for label,path in sources.items():
        trace=read(path);assert trace['instance']==fresh and trace['horizon_ticks']==10400 and trace['tick_minutes']==fresh['tick_minutes']
        checked=check_trace(trace,deepcopy(fresh));identity=audit_trace(trace,fresh)
        assert checked['valid'] and checked['terminal_requirements_met'] and checked['all_orders_fulfilled']
        scoped=R.audit(trace,fresh);assert scoped['valid']
        assert checked['metrics']['delivered_orders']==4 and checked['metrics']['unfulfilled_orders']==0
        assert checked['metrics']['terminal_deadline_debt_ticks']==checked['metrics']['tardiness_ticks']==0
        assert checked['metrics']['operations']==64 and checked['metrics']['moves']==76
        traces[label]=trace;checks[label]=checked;identities[label]=identity;scoped_identities[label]=scoped
    assert not identities['new_cp']['valid'] and not identities['hint']['valid'] and identities['original_heuristic']['valid']
    for label,unit,move in (('new_cp','P04/pump/1','move74'),('hint','P03/pump/1','move55')):
        assert identities[label]['issues']==[dict(code='unit_before_identity_birth',message='Part referenced before its canonical birth',unit_id=unit,field='part_move',record_id=move)]
    assert close(checks['new_cp'],exact['validation']) and close(checks['hint'],report['hint_fresh_check'])
    def makespan(label):return max(checks[label]['metrics']['delivery_ticks'].values())
    assert makespan('new_cp')==exact['objective_ticks']==1541
    assert makespan('hint')==report['hint_makespan_ticks']==1567 and makespan('original_heuristic')==2482
    energy=fresh['energy'];tickhours=Q(str(fresh['tick_minutes']))/60
    required_kwh=(Q(energy['base_load_kw'])*fresh['horizon_ticks']+
                  sum(Q(step['base_ticks'])*Q(fresh['modes'][step['process']]['standard']['power_kw'])
                      for route in fresh['recipes'].values() for step in route)*4)*tickhours
    constant_min_cost=required_kwh*Q(str(energy['tariff_low']))
    assert required_kwh==2704 and constant_min_cost==Q(1352,5)
    for label,checked in checks.items():
        assert math.isclose(checked['metrics']['grid_kwh'],float(required_kwh),abs_tol=1e-7)
        assert math.isclose(checked['metrics']['total_cost'],float(constant_min_cost),abs_tol=1e-7)
        assert all(e['battery_action']=='idle' for e in traces[label]['energy'])
        assert not any(m['kind']=='charge' for m in traces[label]['moves'])
    schedule=read(REMOTE/'result/cp-schedule.json')
    for field in ('agv_successors','worker_successors'):schedule[field]={int(a):b for a,b in schedule[field].items()}
    ops,moves=activities(fresh);exported=to_trace(fresh,ops,moves,schedule)
    assert exported==traces['new_cp']
    recovered=schedule_from_trace(fresh,ops,moves,traces['new_cp']);assert recovered==schedule
    normalized,normalization=N.normalize(traces['new_cp'],fresh)
    normalized_checked=check_trace(normalized,deepcopy(fresh));normalized_identity=audit_trace(normalized,fresh)
    assert normalized_checked['valid'] and normalized_checked['terminal_requirements_met'] and normalized_checked['all_orders_fulfilled'] and normalized_identity['valid']
    assert close(normalized_checked['metrics'],checks['new_cp']['metrics'])
    assert normalized['metrics']==traces['new_cp']['metrics']=={}
    assert len(N.structural_diff(traces['new_cp'],normalized))==1
    normalized_bytes=(json.dumps(normalized,indent=2)+'\n').encode()
    assert exact['status']=='FEASIBLE' and exact['optimal'] is False and exact['best_bound_ticks']==1524
    assert not exact['model_infeasibility_proven'] and not exact['global_infeasibility_proven'] and exact['flagship_global_gap'] is None
    assert exact['search_workers']==report['search_workers']==16 and exact['seed']==2027
    assert exact['wall_limit_seconds']==report['cp_wall_cap_seconds']==7170 and report['scheduler_wall_cap_seconds']==7200
    assert report['fresh_search'] and not report['cp_proof_resumed'] and report['final_tapes_used']==0
    assert exact['incumbent']['used'] and exact['incumbent']['makespan']==1567 and exact['incumbent']['complete_operation_move_arc_hint']
    assert 'status: FEASIBLE' in exact['solver_response'] and 'objective: 1541' in exact['solver_response'] and 'best_bound: 1524' in exact['solver_response']
    started=read(REMOTE/'result/started.json');assert started['job_id']=='6117555' and started['payload_hashes']==manifest['payload_hashes']
    receipt_path=BASE/'multi-reference-2h-axion/transfer-receipt.json';receipt=read(receipt_path)
    assert receipt['report_sha256']==sha(REMOTE/'result/report.json') and receipt['source_payload_files_checked']==9 and receipt['original_manifest_unchanged']
    archive=Path(receipt['transport_archive']);assert archive.stat().st_size==receipt['transport_archive_bytes']==244994 and sha(archive)==receipt['transport_archive_sha256']
    with tarfile.open(archive) as stream:
        members={m.name:m for m in stream.getmembers() if m.isfile()}
        prefix=REMOTE.name+'/'
        for path in REMOTE.rglob('*'):
            if path.is_file():assert hashlib.sha256(stream.extractfile(members[prefix+str(path.relative_to(REMOTE))]).read()).hexdigest()==sha(path)
    accounting=BASE/'final-compute-0316-summary.json';cost=read(accounting)
    for path,expected in cost['inputs'].items():assert sha(path)==expected
    assert cost['analysis_source_sha256']==sha(BASE/'final-compute-0316-source.py')
    ledger=read(BASE/'final-compute-0316-ledger.json');job=next(j for j in ledger['jobs'] if j['id']=='6117555')
    raw=next(line.split('|') for line in (BASE/'accounting-20261017-0316.txt').read_text().splitlines() if line.startswith('6117555|'))
    assert raw[3]=='COMPLETED' and raw[8]=='0:0' and int(raw[4])==7174 and int(raw[5])==16
    allocated=int(raw[4])*int(raw[5]);assert allocated==114784==job['allocated_cpu_seconds']
    assert job['state']=='COMPLETED' and report['slurm']['SLURM_JOB_ID']=='6117555' and report['slurm']['SLURM_CPUS_PER_TASK']=='16'
    assert report['runtime']['process_cpu_seconds']<=allocated and report['runtime']['wall_seconds']<=7175
    assert cost['research_running_reported_allocated_cpu_hours']==0 and cost['research_running_job_ids']==[]
    assert cost['recorded_gpu_hours']==cost['physical_qpu_calls']==cost['veloxq_calls']==0
    lower=max(1524,1482);upper=1541;heur=2482
    relative_low=Q(heur-upper,upper);relative_high=Q(heur-lower,lower)
    return dict(schema='stage2-independent-two-hour-reference-audit.v1',valid=True,job_id='6117555',
                instance_sha256=digest(fresh),payload_files_checked=9,payload_hashes=manifest['payload_hashes'],
                report_sha256=sha(REMOTE/'result/report.json'),artifact_hashes=report['artifact_hashes'],
                transfer_receipt_sha256=sha(receipt_path),transfer_archive_sha256=receipt['transport_archive_sha256'],
                source_stability_verified=True,fresh_instance_exact_match=True,physical_checks=checks,
                raw_stock_identity_checks=identities,reference_scoped_physical_encounter_identity=scoped_identities,
                derived_normalized_witness=dict(path='derived-normalized-witness.json',sha256=hashlib.sha256(normalized_bytes).hexdigest(),
                    transformation=normalization,physical_check=normalized_checked,stock_identity_check=normalized_identity,
                    exact_one_field_change=True,all_physical_legs_operations_and_metrics_unchanged=True),
                schedule_to_trace_exact_roundtrip=True,trace_to_schedule_exact_roundtrip=True,
                status='FEASIBLE',proven_optimal=False,solver_reported_lower_bound=1524,arithmetic_lower_bound_preserved=1482,
                combined_scoped_optimum_interval=[lower,upper],absolute_incumbent_gap_upper_bound=upper-lower,
                incumbent_relative_excess_upper_bound_over_optimum=float(Q(upper-lower,lower)),
                heuristic_makespan=heur,heuristic_absolute_excess_interval=[heur-upper,heur-lower],
                heuristic_relative_excess_over_optimum_interval=[float(relative_low),float(relative_high)],
                exact_heuristic_relative_excess_rationals=[[relative_low.numerator,relative_low.denominator],[relative_high.numerator,relative_high.denominator]],
                same_earlier_objective_tiers=True,constant_minimum_grid_kwh=float(required_kwh),constant_minimum_cost=float(constant_min_cost),
                runtime=report['runtime'],allocated_cpu_seconds=allocated,allocated_cpu_hours=float(Q(allocated,3600)),
                immutable_accounting_summary_sha256=sha(accounting),raw_accounting_sha256=sha(BASE/'accounting-20261017-0316.txt'),
                original_heuristic_trace_sha256=sha(sources['original_heuristic']),
                audit_source_sha256=sha(__file__),factory_calls=0,solver_calls=0,wall_seconds=time.perf_counter()-began,
                additional_audit_source_hashes={name:sha(HERE/name) for name in ('reference_identity.py','normalize_witness.py','test_reference_identity.py')},
                _derived_trace=normalized,
                limitations=['Lower1524 is the solver-reported bound for the unchanged audited exact CP domain, not a new independent arithmetic proof or external formal solver certificate',
                    'Raw newCP and old1567hint retain their literal frozen stock identity rejection for early future reservation. A separate reference-scoped physical-encounter audit passes; the one-field derived1541witness also passes the unchanged stock identity auditor',
                    'The broader CP dispatch domain supplies a relaxation lower bound for the stricter birth-at-dispatch domain; the normalized checked witness supplies its upper bound. No identical-optima theorem is asserted',
                    'The1567 hint upper bound does not exclude a better optimum; the new1541 feasible witness lies within that cutoff',
                    'FEASIBLE is not OPTIMAL; no exact1541-optimum claim',
                    'Reference only:1worker1AGV7stations, deterministic quality and declared nonbinding mechanisms; no flagship global-gap or final-policy change',
                    'Heuristic excess interval uses(2482-optimum)/optimum; it is not an exact known relative gap',
                    'All earlier arithmetic1480/1482, CP1466 and witness1567 archives remain historical evidence',
                    'Zero aggregate parallel solver branch/conflict counters are not evidence no search occurred',
                    'No factory/solver rerun, final-tape execution, publication or deployment by this audit'])


if __name__=='__main__':
    result=audit();normalized=result.pop('_derived_trace')
    with (HERE/'derived-normalized-witness.json').open('x') as stream:stream.write(json.dumps(normalized,indent=2)+'\n')
    assert sha(HERE/'derived-normalized-witness.json')==result['derived_normalized_witness']['sha256']
    for label,identity in result['raw_stock_identity_checks'].items():
        with (HERE/('raw-'+label+'-stock-identity.json')).open('x') as stream:stream.write(json.dumps(identity,indent=2)+'\n')
    with (HERE/'report.json').open('x') as stream:stream.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('physical_checks','raw_stock_identity_checks','reference_scoped_physical_encounter_identity','derived_normalized_witness','payload_hashes')},indent=2))
