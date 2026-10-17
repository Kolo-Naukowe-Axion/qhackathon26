"""Seal a derived planning-core checkpoint without changing prior experiments."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from .window_campaign import save
from .window_qubo import check_plan,digest


ROOT=Path(__file__).resolve().parents[1]
SEARCH=ROOT/'output/stage2-search'


def run(output):
    output=Path(output)
    output.mkdir(parents=True,exist_ok=False)
    base=json.loads((SEARCH/'planning-core-checkpoint-v1/report.json').read_text())
    entries=list(base['experiments'])
    names=['component-columns-mac-v1','component-column-references-mac-v1',
           'component-columns-enriched-mac-v1','component-raw-reference128-mac-v1',
           'component-columns-flexible-mac-v1','component-columns-flexible-mac-v2',
           'component-compact-reference-mac-v1','component-compact-reference-mac-v2',
           'component-column-blocks-mac-v1','operation-columns-mac-v1',
           'operation-column-blocks128-mac-v1','operation-compiler-audit128-mac-v1',
           'operation-width-probe32-mac-v1','operation-closure-probe32-mac-v1',
           'operation-closure-probe32-mac-v2','operation-closure-probe32-mac-v3',
           'operation-sector-blocks32-mac-v1','operation-sector-circuit-audit-mac-v1',
           'component-reference128-refine-mac-v1','operation-sector-blocks32-long-mac-v1',
           'operation-sector-circuit-audit-long-mac-v1','operation-sector-circuit-audit-long-mac-v2']
    for name in names:
        folder=SEARCH/name
        path=folder/('summary.json'if(folder/'summary.json').exists()else'report.json')
        data=json.loads(path.read_text())
        entries.append(dict(experiment=name,report=str(path.relative_to(ROOT)),
             sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
             wall_seconds=data.get('wall_seconds'),process_cpu_seconds=data.get('process_cpu_seconds'),
             peak_rss_bytes=data.get('peak_rss_bytes'),source_stable=data.get('source_stable')))
    if len({row['report']for row in entries})!=len(entries):
        raise AssertionError('Duplicate top-level process accounting report')
    for row in entries:
        if hashlib.sha256((ROOT/row['report']).read_bytes()).hexdigest()!=row['sha256']:
            raise AssertionError('A retained checkpoint report changed')
        if row['source_stable']is False:
            raise AssertionError('Source instability requires explicit treatment')
    reference_inputs=[('component-raw-reference128-mac-v1',''),
                      ('component-compact-reference-mac-v1','case0'),
                      ('component-compact-reference-mac-v2','case0'),
                      ('component-reference128-refine-mac-v1','')]
    anchors=[]
    problem_hash=None
    best_upper=None
    lower=0
    for name,case in reference_inputs:
        folder=SEARCH/name/case
        problem=json.loads((folder/'problem.json').read_text())
        checksum=digest(problem)
        if problem_hash is not None and problem_hash!=checksum:
            raise AssertionError('Raw reference certificates describe different numerical problems')
        problem_hash=checksum
        path=folder/'report.json'
        report=json.loads(path.read_text())
        result=report['result']
        bound=math.ceil(float(result.get('bound',0))-1e-6)
        lower=max(lower,bound)
        if 'plan'in result:
            checked=check_plan(problem,result['plan'])
            if not checked['valid']or checked['objective']!=result['objective']:
                raise AssertionError('Saved raw reference failed independent schedule/objective check')
            if best_upper is None or checked['objective']<best_upper:
                best_upper=checked['objective']
                best_plan=result['plan']
        anchors.append(dict(report=str(path.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                            status=result['status'],bound=bound,objective=result.get('objective')))
    if lower>best_upper:
        raise AssertionError('Inconsistent same-model bounds')
    certificate=dict(schema='stage2-combined-raw-cell-interval.v1',operations=128,problem_sha256=problem_hash,
           lower_bound=lower,feasible_upper_bound=best_upper,relative_gap_to_upper=(best_upper-lower)/best_upper,
           best_plan=best_plan,anchors=anchors,
           scope='Combined native-CP bounds and independently raw-checked feasible schedules of the SAME deterministic grid15/H4320 cell. Not a physical-factory, stochastic, finer-grid or shipping certificate.')
    save(output/'raw128-certificate.json',certificate)
    audits=[]
    for name in('window-circuit-audit-mac-v1','trajectory-circuit-audit-mac-v1',
                 'operation-sector-circuit-audit-mac-v1','operation-sector-circuit-audit-long-mac-v2'):
        path=SEARCH/name/'report.json'
        data=json.loads(path.read_text())
        audits.append(dict(report=str(path.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                           valid=data['valid'],circuits=data.get('circuits'),audited=data.get('audited',data.get('circuits')),
                           skipped=data.get('skipped',0)))
    frozen=ROOT/'presentation/stage2/research/final-evidence.json'
    frozen_hash=hashlib.sha256(frozen.read_bytes()).hexdigest()
    if frozen_hash!='6a66d36b2ea032b773a2b550d8773c13a0c4ea3f1fab0ef3565894853746fd60':
        raise AssertionError('Frozen final export changed')
    hashes={}
    for name in('stage2/planning_checkpoint.py','stage2/window_qubo.py'):
        data=(ROOT/name).read_bytes()
        target=output/'sources'/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(data)
        hashes[name]=hashlib.sha256(data).hexdigest()
    report=dict(schema='stage2-renewed-planning-core-checkpoint.v2',status='Completed local planning-core research batch; development evidence, not a new final population estimate',
                experiments=entries,metered_process_cpu_seconds=sum(row.get('process_cpu_seconds')or 0 for row in entries),
                metering_scope='Distinct top-level process CPU only, failures included; nested solver/controller CPU not double-counted. Tests, interactive diagnostics and some older audit work are not comprehensively metered: lower bound, not complete billing. Concurrent wall times are not summed as elapsed campaign duration.',
                max_recorded_process_rss_bytes=max(row.get('peak_rss_bytes')or 0 for row in entries),
                gpu_hours=0,physical_qpu_calls=0,new_remote_jobs=0,old_frozen_compute_ledger_unchanged=True,
                tests=dict(targeted_unittests=37,status='passed',original_randomized_exhaustive_instances=30,
                           additional_raw_interval_reference_exhaustive_instances=40),
                independent_qasm_audits=audits,audit_count_scope='Audit cases across campaigns can overlap; counts are not distinct circuits or quantum optimization calls.',
                rejected_compiler_audit=dict(report='output/stage2-search/operation-sector-circuit-audit-long-mac-v1/report.json',
                     reason='All raw QASM circuits match the sector simulator, but three level3 compilations exceed the strict probability tolerance. Failure retained; v2 verifies conservative fallback circuits without relaxing tolerance.'),
                raw128_certificate='raw128-certificate.json',frozen_final_export_sha256=frozen_hash,
                source_hashes=hashes,
                decision='Retain existing strong physical-factory controller. Full bounded grid15 scheduling now has proven32/48/64-operation references and a bounded128-operation reference. Restricted operation QUBOs improve over heuristic parents under native CP; current quantum conditional searches do not establish advantage. No external compute justified by the current bottleneck.')
    save(output/'report.json',report)
    save(output/'manifest.json',{str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(output.rglob('*'))if p.is_file()})
    return dict(experiments=len(entries),metered_process_cpu_seconds=report['metered_process_cpu_seconds'],
                max_recorded_process_rss_bytes=report['max_recorded_process_rss_bytes'],
                raw128_interval=[lower,best_upper],independent_audits_valid=all(row['valid']for row in audits))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',required=True)
    a=p.parse_args()
    print(json.dumps(run(a.output),indent=2))
