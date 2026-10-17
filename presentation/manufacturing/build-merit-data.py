"""Export checked merit artifacts and whole-plan previews; no optimization."""
import hashlib
import json
from pathlib import Path
import statistics
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from stage2.window_qubo import check_plan,digest

sources={}
def read(name):
    path=ROOT/name
    sources[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    return json.loads(path.read_text())

def method_summary(row, method):
    """An invalid decoded state cannot count as an optimal returned schedule."""
    runs=[r for r in row['runs'] if r['method']==method]
    probabilities=[r['exact_hit_probability'] for r in runs if r['exact_hit_probability'] is not None]
    return dict(runs=len(runs), valid=sum(bool(r['decoded']['valid']) for r in runs),
        pool_optimal=sum(bool(r['decoded']['valid']) and
                         r['decoded'].get('objective')==row['reference']['objective'] and
                         r['energy']==row['reference']['objective'] for r in runs),
        median_exact_single_shot=statistics.median(probabilities) if probabilities else None,
        total_solver_seconds=sum(r['wall_seconds'] for r in runs))


def build():
    frontier=read('output/capacity-frontier-review-v1/report.json')
    deadline=read('output/deadline-decision-review-v1/report.json')
    bridge=read('output/recipe-bridge-review-v2/report.json')
    circuit=read('output/recipe-bridge-circuit-audit-v1/report.json')
    economics=read('output/capacity-economics-v2/report.json')
    controls=read('output/deadline-anneal-report-audit-v2/report.json')
    new_plans=[]
    points=[]
    for row in frontier['rows']:
        if row['case']!='heat-lease-32':continue
        ref=row['reference'];checked=ref['check']
        points.append(dict(cap=row['cap'],variables=row['model']['variables'],couplers=row['model']['couplers'],
                           tardiness=checked['weighted_terminal_tardiness'],makespan=checked['makespan']))
        if row['cap']==64:
            new_plans.append(dict(case=row['case'],id='enriched_reference',name='Enriched operation pool · native reference',
                                  plan=ref['plan'],quality_label='Certified enriched-pool optimum; matches the complete-model reference.',
                                  source='output/capacity-frontier-review-v1/heat-lease-32/cap-64/report.json'))
    for row in deadline['rows']:
        if row['case']=='heat-lease-32' and row['cap']==900:
            ref=row['reference']
            new_plans.append(dict(case=row['case'],id='deadline_reference',name='Hard-deadline query · native witness',
                                  plan=ref['plan'],quality_label='Native hard-deadline witness. Feasibility query; no secondary makespan optimization.',
                                  source='output/deadline-decision-review-v1/heat-lease-32-cap-900/reference.json'))
    quantum=[]
    for row in bridge['rows']:
        methods={}
        for method in ['qaoa_xy','uniform_onehot','sa_onehot']:
            methods[method]=method_summary(row,method)
        quantum.append(dict(case=row['case'],cap=row['cap'],variables=row['model']['variables'],couplers=row['model']['couplers'],
                            sector_states=row['sector_states'],reference_objective=row['reference']['objective'],
                            best_constructive=row['best_constructive'],first_constructive=row['first_constructive'],methods=methods))
        if row['cap']==3:
            r=next(r for r in row['runs'] if r['method']=='qaoa_xy' and r['seed']==7)
            if r['decoded']['valid']:
                new_plans.append(dict(case=row['case'],id='recipe_qaoa',name='QAOA simulation · complete component recombination',
                    plan=r['decoded']['plan'],quality_label='Actual QAOA sample on a restricted whole-recipe domain; classical candidates already contain the best plan.',
                    source=f'output/recipe-bridge-review-v2/{row["case"]}/cap-3/qaoa_xy-7.json'))
    for row in new_plans:
        problem=read('output/manufacturing-recovery-v2/'+row['case']+'/problem.json')
        row['check']=check_plan(problem,row['plan'])
        assert row['check']['valid']
        row['problem_sha256']=digest(problem)
        row['optimal']=False
    realism_path='output/realism-frontier-v1/report.json'
    realism=read(realism_path) if (ROOT/realism_path).exists() else None
    if realism is not None:
        supplement=read('output/realism-continuous-counts-v2/report.json')
        for row in realism['feature_ablations']:
            if row['variant']=='continuous_worker_calendars':
                row['unary_complete']=supplement['unary_complete']
                row['support_complete']=supplement['support_complete']
                row['count_only_supplement']=True
    result=dict(schema='qfactoria-manufacturing-merit-view.v1',source_sha256=sources,
        plans=new_plans,frontier=points,deadline=[dict(case=r['case'],cap=r['cap'],variables=r['model'].get('variables'),
            couplers=r['model'].get('couplers'),target_feasible=r['reference']['target_feasible']) for r in deadline['rows']],
        quantum=quantum,circuit_audit=circuit,economics=economics,controls=controls,realism=realism,
        scope='Saved checked evidence; interactive cost sensitivity is conditional on explicit synthetic assumptions.',
        baseline=dict(naive_bits=72,unary_pruned_bits=39,selected_sequence_bits=3,
                      qualification='Selected baseline3x3 encoding evaluates six common orders classically; not a general factory compression'),
        veloxq_calls=0,physical_qpu_calls=0)
    (Path(__file__).parent/'merit-data.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(sources=len(sources),new_plans=len(new_plans),quantum_rows=len(quantum),realism_available=realism is not None)))


if __name__=='__main__':
    build()
