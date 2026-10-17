"""Summarize retained scoped reference evidence, including unresolved bounds."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    grid_path=ROOT/'output/stage2-search/multi-reference-heuristic-grid/report.json'
    grid=read(grid_path);sources={str(grid_path.relative_to(ROOT)):sha(grid_path)}
    rows=[]
    for pumps in (2,3,4):
        for attendance in ('automatic','full'):
            candidates=[row for row in grid['candidates']if row['pumps']==pumps and row['attendance']==attendance]
            complete=[row for row in candidates if row['valid']and row['complete']]
            best=min(complete,key=lambda row:row['makespan'])
            result=dict(pumps=pumps,attendance=attendance,operations=16*pumps,moves=19*pumps,
                development_heuristic=dict(makespan_ticks=best['makespan'],weights=best['weights'],trace_sha256=best['trace_sha256'],
                    valid_candidates=sum(row['valid']for row in candidates),incomplete_candidates=sum(not row['complete']for row in candidates),
                    total_candidates=len(candidates)),cp_runs=[])
            suffix='-full'if attendance=='full'else''
            campaigns=[(15,ROOT/f'output/stage2-search/multi-reference-pilot/n{pumps}-scale15{suffix}')]
            campaigns.extend((budget,ROOT/f'output/stage2-search/multi-reference-{budget}/n{pumps}/{attendance}')for budget in (600,3600))
            for budget,directory in campaigns:
                report_path=directory/'report.json'
                if not report_path.exists():
                    if (directory/'hint.json').exists():result['cp_runs'].append(dict(budget_seconds=budget,status='RUNNING',proof_complete=False))
                    continue
                report=read(report_path);exact=report['exact'];sources[str(report_path.relative_to(ROOT))]=sha(report_path)
                result['cp_runs'].append(dict(budget_seconds=budget,status=exact['status'],
                    incumbent_ticks=exact['objective_ticks'],cp_lower_bound_ticks=exact['best_bound_ticks'],
                    optimal=exact['optimal'],valid=exact.get('validation',{}).get('valid'),
                    all_orders_fulfilled=exact.get('validation',{}).get('all_orders_fulfilled'),
                    wall_seconds=exact['solver_wall_seconds'],workers=exact.get('search_workers',1),source_sha256=report['provenance']['source_sha256'],
                    sources_stable=report['provenance']['sources_stable_during_run'],
                    exact_heuristic_gap=(best['makespan']/exact['objective_ticks']-1)if exact['optimal']else None,
                    trace_path=str((directory/'cp-trace.json').relative_to(ROOT))))
            parallel=ROOT/'output/stage2-search/multi-reference-parallel-axion'
            audit_path=parallel/'independent-audit.json'
            if pumps==4 and attendance=='automatic'and audit_path.exists():
                audit=read(audit_path);report_path=parallel/'collected/result/report.json';report=read(report_path)
                trace_path=parallel/'collected/result/cp-trace.json';exact=report['exact']
                original_instance=read(campaigns[0][1]/'instance.json')
                assert report['instance_sha256']==audit['instance_sha256']==hashlib.sha256(json.dumps(original_instance,sort_keys=True,separators=(',',':')).encode()).hexdigest()
                assert audit['valid_complete']and report['sources_stable_during_run']and not audit['conflicts_with_prior_analytic_bound']
                assert audit['trace_sha256']==sha(trace_path)
                assert audit['fresh_independent_check']['valid']and audit['fresh_independent_check']['all_orders_fulfilled']and audit['fresh_independent_check']['terminal_requirements_met']
                for path in (audit_path,report_path,parallel/'collected/collection-status.json'):
                    sources[str(path.relative_to(ROOT))]=sha(path)
                result['cp_runs'].append(dict(budget_seconds=report['cp_wall_cap_seconds'],scheduler_wall_cap_seconds=report['scheduler_wall_cap_seconds'],
                    status=exact['status'],incumbent_ticks=exact['objective_ticks'],cp_lower_bound_ticks=exact['best_bound_ticks'],
                    optimal=exact['optimal'],valid=True,all_orders_fulfilled=True,wall_seconds=exact['solver_wall_seconds'],workers=exact['search_workers'],
                    source_sha256={name:digest for name,digest in report['payload_hashes'].items()if name.startswith('stage2/')and not name.endswith('__init__.py')},
                    sources_stable=True,exact_heuristic_gap=(best['makespan']/exact['objective_ticks']-1)if exact['optimal']else None,
                    trace_path=str(trace_path.relative_to(ROOT)),instance_sha256=audit['instance_sha256'],job_id=audit['job_id'],cost=audit['cost'],
                    fresh_search=True,cp_proof_resumed=False))
            if pumps==4 and attendance=='automatic':
                # Independently sealed closeout. Raw early-reservation identity
                # rejection stays literal; the derived witness supplies the upper.
                directory=ROOT/'output/stage2-search/multi-reference-2h-axion/completed/multi-reference-2h-20261017T0116/result'
                audit_dir=ROOT/'output/stage2-search/final-independent-audit/reference-2h-6117555'
                seal_path=ROOT/'output/stage2-search/reference-2h-methodology-review/final-seal.json'
                assert sha(seal_path)=='96bca6796eff427102dbdc59c14ffb1693b70e04594ecf17baebc08087a54a14'
                seal=read(seal_path);audit_path=audit_dir/'report.json';audit=read(audit_path)
                report_path=directory/'report.json';report=read(report_path);exact=report['exact']
                witness_path=audit_dir/audit['derived_normalized_witness']['path'];derived=audit['derived_normalized_witness']
                assert seal['valid']and seal['audited_report_sha256']==sha(audit_path)
                assert seal['derived_stock_identity_physical_terminal_pass']and seal['raw_stock_identity_rejection_preserved']
                assert audit['valid']and audit['schema']=='stage2-independent-two-hour-reference-audit.v1'
                assert audit['report_sha256']==sha(report_path)
                assert audit['source_stability_verified']and audit['fresh_instance_exact_match']and audit['same_earlier_objective_tiers']
                assert derived['sha256']==seal['derived_witness_sha256']==sha(witness_path)
                assert derived['physical_check']['valid']and derived['physical_check']['all_orders_fulfilled']and derived['physical_check']['terminal_requirements_met']
                assert derived['stock_identity_check']['valid']and derived['exact_one_field_change']and derived['all_physical_legs_operations_and_metrics_unchanged']
                assert not audit['raw_stock_identity_checks']['new_cp']['valid']
                assert report['instance_sha256']==audit['instance_sha256']==result['cp_runs'][-1]['instance_sha256']
                assert report['sources_stable_during_run']and report['payload_hashes']['stage2/reference_multi.py']=='226dced1939ee824a0e661d4112efc488be4de3286e6280e9da4e58163700efe'
                for name,digest in audit['artifact_hashes'].items():assert sha(directory/name)==digest
                accounting_path=ROOT/'output/stage2-search/final-compute-0316-summary.json';accounting=read(accounting_path)
                assert sha(accounting_path)==audit['immutable_accounting_summary_sha256']
                for name,digest in accounting['inputs'].items():assert sha(ROOT/name)==digest
                for path in (audit_path,seal_path,report_path,witness_path,directory/'cp-trace.json',audit_dir/'raw-new_cp-stock-identity.json',accounting_path):
                    sources[str(path.relative_to(ROOT))]=sha(path)
                result['cp_runs'].append(dict(budget_seconds=report['cp_wall_cap_seconds'],scheduler_wall_cap_seconds=report['scheduler_wall_cap_seconds'],
                    status=exact['status'],incumbent_ticks=exact['objective_ticks'],cp_lower_bound_ticks=exact['best_bound_ticks'],
                    optimal=exact['optimal'],valid=True,all_orders_fulfilled=True,wall_seconds=exact['solver_wall_seconds'],workers=exact['search_workers'],
                    source_sha256={name:digest for name,digest in report['payload_hashes'].items()if name.startswith('stage2/')and not name.endswith('__init__.py')},
                    sources_stable=True,exact_heuristic_gap=None,trace_path=str(witness_path.relative_to(ROOT)),raw_cp_trace_path=str((directory/'cp-trace.json').relative_to(ROOT)),
                    instance_sha256=audit['instance_sha256'],job_id=audit['job_id'],fresh_search=True,cp_proof_resumed=False,
                    cost=dict(scheduler_elapsed_seconds=audit['allocated_cpu_seconds']/report['search_workers'],allocated_cpu_hours=audit['allocated_cpu_hours'],
                        process_cpu_seconds=report['runtime']['process_cpu_seconds'],gpu_hours=0),
                    audit_path=str(audit_path.relative_to(ROOT)),audit_sha256=sha(audit_path),methodology_seal_sha256=sha(seal_path),
                    upper_witness_kind='one-field normalized derived copy; all physical timings unchanged',
                    raw_stock_identity_valid=False,derived_stock_identity_valid=True,
                    dispatch_domain_scope='CP lower bound permits earlier future reservations; derived upper witness meets birth-at-dispatch stock identity. Identical domain optima are not asserted.',
                    date_utc='2026-10-17',completed_closeout=True))
            construct_path=ROOT/f'output/stage2-search/multi-reference-constructive/n{pumps}/report.json'
            if attendance=='automatic'and construct_path.exists():
                construct=read(construct_path);sources[str(construct_path.relative_to(ROOT))]=sha(construct_path)
                result['constructive_upper_bound_ticks']=construct['upper_bound_ticks']
            usable=[row for row in result['cp_runs']if row.get('valid')and row.get('all_orders_fulfilled')]
            upper=[row['incumbent_ticks']for row in usable]+[best['makespan']]
            if 'constructive_upper_bound_ticks'in result:upper.append(result['constructive_upper_bound_ticks'])
            lower=[row['cp_lower_bound_ticks']for row in result['cp_runs']if row.get('cp_lower_bound_ticks')is not None]
            result['best_checked_upper_bound_ticks']=min(upper)
            result['best_reported_cp_lower_bound_ticks']=max(lower,default=None)
            result['optimum_proven']=any(row.get('optimal',False)for row in result['cp_runs'])
            # Add only a retained numerical certificate; never overwrite CP bounds.
            result['analytic_certificates']=[]
            for suffix in ('','-buffer'):
                bound_path=ROOT/f'output/stage2-search/multi-reference-bounds/n{pumps}-{attendance}{suffix}.json'
                if not bound_path.exists():continue
                certificate=read(bound_path);sources[str(bound_path.relative_to(ROOT))]=sha(bound_path)
                entry=dict(path=str(bound_path.relative_to(ROOT)),lower_bound_ticks=certificate['lower_bound_ticks'],components=certificate['components'],proof=certificate['proof'])
                result['analytic_certificates'].append(entry)
            if pumps==4 and attendance=='automatic':
                extension_path=ROOT/'output/reference-bound-extension/report.json'
                extension=read(extension_path);certificate=extension['certificate']
                bound_source=ROOT/'output/reference-bound-extension/bound.py';proof_source=ROOT/'output/reference-bound-extension/PROOF.md'
                assert extension['valid']and extension['complete_witnesses_checked']==26 and not extension['invalid_in_scope_traces']
                assert certificate['pumps']==4 and certificate['lower_bound_ticks']==1482 and certificate['previous_buffer_bound_ticks']==1480
                original_instance=read(campaigns[0][1]/'instance.json')
                assert certificate['instance_sha256']==hashlib.sha256(json.dumps(original_instance,sort_keys=True,separators=(',',':')).encode()).hexdigest()
                assert certificate['source_sha256']==sha(bound_source)==extension['source_hashes']['bound_py']
                assert extension['old_certificate_sha256']==sha(ROOT/'output/stage2-search/multi-reference-bounds/n4-automatic-buffer.json')
                assert all(sha(ROOT/name)==expected for name,expected in certificate['source_hashes'].items())
                assert all(w['independently_checked']and w['makespan_ticks']>=w['guarded_lower_bound_ticks']for w in extension['witnesses'])
                for path in (extension_path,bound_source,proof_source):sources[str(path.relative_to(ROOT))]=sha(path)
                entry=dict(path=str(extension_path.relative_to(ROOT)),lower_bound_ticks=certificate['lower_bound_ticks'],components=certificate['components'],proof=certificate['proof'],
                    proof_path=str(proof_source.relative_to(ROOT)),proof_sha256=sha(proof_source),bound_source_sha256=sha(bound_source),instance_sha256=certificate['instance_sha256'],
                    previous_lower_bound_ticks=certificate['previous_buffer_bound_ticks'],complete_witnesses_checked=extension['complete_witnesses_checked'],supplemental=True,
                    scope=certificate['proof_scope'])
                result['analytic_certificates'].append(entry)
                result['supplemental_bound_extension']=entry
            if result['analytic_certificates']:
                best_certificate=max(result['analytic_certificates'],key=lambda item:item['lower_bound_ticks'])
                result['analytic_lower_bound_ticks']=best_certificate['lower_bound_ticks'];result['analytic_certificate']=best_certificate
                result['analytic_full_attendance_lower_bound_ticks'if attendance=='full'else'analytic_automatic_lower_bound_ticks']=best_certificate['lower_bound_ticks']
            rigorous_lower=max([value for value in (result['best_reported_cp_lower_bound_ticks'],
                result.get('analytic_lower_bound_ticks'))if value is not None],default=None)
            result['best_certified_lower_bound_ticks']=rigorous_lower
            result['heuristic_makespan_gap_interval']=dict(
                lower=best['makespan']/result['best_checked_upper_bound_ticks']-1,
                upper=best['makespan']/rigorous_lower-1 if rigorous_lower else None,
                explanation='Optimum lies between rigorous lower bound and best checked complete upper bound; this is an interval, not an exact gap')
            rows.append(result)
    bundle=dict(schema='tiny-multi-reference-evidence.v1',scope='1–4 matched-BOM deterministic pumps; not stochastic flagship',
        role='Same-instance development/reference experiments; zero final held-out tapes',rows=rows,
        grid_valid=sum(row['valid']for row in grid['candidates']),grid_incomplete=sum(not row['complete']for row in grid['candidates']),
        source_sha256=sources,analytic_bound_proof='docs/STAGE2_REFERENCE_MULTI.md#full-attendance-analytic-lower-bound')
    (OUT/'report.json').write_text(json.dumps(bundle,indent=2)+'\n')
    print(json.dumps([dict(pumps=row['pumps'],attendance=row['attendance'],upper=row['best_checked_upper_bound_ticks'],
        cp_lower=row['best_reported_cp_lower_bound_ticks'],optimal=row['optimum_proven'])for row in rows]))

if __name__=='__main__':main()
