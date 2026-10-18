"""Read retained investment what-if results into one public page data file. No solver calls.

Source: output/catering-investment-v1 (catering/investment.py, CP 240 s, two seeds).
Output: presentation/catering/investment/data.json. Every number on the investment page
comes from this file; the page computes nothing that needs the solver.
"""
import json
import hashlib
import sys
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
BASE='output/catering-investment-v1/'
SEEDS=[2026,2027]
# What changes in the kitchen, for display. Keys match catering.investment.VARIANTS.
CHANGES={
    'baseline':dict(kind='none',label='Current kitchen',short='Today'),
    'repair-c2':dict(kind='equipment',label='Repair cooker C2 (no outage)',short='Repair C2',resource='C2'),
    'third-cooker':dict(kind='equipment',label='Third cooker C3',short='+ Cooker C3',resource='C3'),
    'second-prep':dict(kind='equipment',label='Second prep station P2',short='+ Prep P2',resource='P2'),
    'second-pack':dict(kind='equipment',label='Second packing line K2',short='+ Packing K2',resource='K2'),
    'second-cook-worker':dict(kind='worker',label='Extra worker who can only cook',short='+ Cook',skills=['cook']),
    'flexible-worker':dict(kind='worker',label='Extra flexible worker: prepare, cook, pack',short='+ Flexible',skills=['prepare','cook','pack']),
    'worker-prepare':dict(kind='worker',label='Extra worker: prepare only',short='+ Prep helper',skills=['prepare']),
    'worker-pack':dict(kind='worker',label='Extra worker: pack only',short='+ Packing helper',skills=['pack']),
    'worker-prepare-pack':dict(kind='worker',label='Extra worker: prepare and pack',short='+ Prep/pack',skills=['prepare','pack']),
    'worker-prepare-cook':dict(kind='worker',label='Extra worker: prepare and cook',short='+ Prep/cook',skills=['prepare','cook']),
    'worker-cook-pack':dict(kind='worker',label='Extra worker: cook and pack',short='+ Cook/pack',skills=['cook','pack']),
}

def file_hash(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()

def load_plan_details(result,meals):
    """Served/missed meals and attended minutes per worker and resource, from the checked plan."""
    plan=result['plan']
    served=sorted({h['meal_id'] for h in plan['meal_handovers']},key=meals.index)
    workers=defaultdict(lambda:defaultdict(int));resources=defaultdict(int)
    for op in plan['operations']+plan.get('recovery_operations',[]):
        attended=op.get('attended_end',op['end'])-op['start']
        if op.get('worker'):workers[op['worker']][op['kind']]+=attended
        resources[op['resource']]+=op['end']-op['start']
    return dict(served_meals=served,missed_meals=[m for m in meals if m not in served],
        handovers=[dict(meal=h['meal_id'],time=h['time']) for h in plan['meal_handovers']],
        worker_minutes={w:dict(sorted(k.items()),total=sum(k.values())) for w,k in sorted(workers.items())},
        resource_minutes=dict(sorted(resources.items())),
        batches=len(plan['batches']),discarded_lots=result['check']['discarded_lots'])

def render(data):return json.dumps(data,indent=1)+'\n'

def export():
    from catering.investment import VARIANTS
    from catering.meal_blocks import meal_fixture
    from catering.domain import snapshot
    instance=meal_fixture(12);state=snapshot(instance,'S3')
    meals=[m['id'] for m in instance['service_model']['meals']]
    sources={}
    def load(path):
        sources[path]=dict(path=path,sha256=file_hash(path))
        return json.loads((ROOT/path).read_text())
    by_seed={}
    for seed in SEEDS:
        for group in ['seed','skills-seed']:
            directory=f'{BASE}{group}-{seed}/'
            plan=load(directory+'experiment-plan.json')
            if (plan['seconds'],plan['workers'],plan['seed'])!=(240,2,seed):raise ValueError(f'Unexpected settings in {directory}')
            for row in load(directory+'report.json')['rows']:
                by_seed[row['variant'],seed]=(row,directory)
    variants=[]
    for name,description,_,scenario in VARIANTS:
        rows={seed:by_seed[name,seed] for seed in SEEDS}
        first,directory=rows[SEEDS[0]]
        entry=dict(id=name,description=description,scenario=scenario,**CHANGES[name])
        if first['status']=='unsupported by profile':
            entry.update(status='unsupported',reason=first['reason'])
            variants.append(entry);continue
        tuples={seed:[r['metrics'][k] for k in 'UWBR'] for seed,(r,_) in rows.items()}
        if not all(r['valid'] for r,_ in rows.values()):raise ValueError(f'Invalid checked plan for {name}')
        if len({tuple(t) for t in tuples.values()})!=1:raise ValueError(f'Seeds disagree for {name}: {tuples}')
        result=load(directory+f'{name}-result.json')
        if result['check']['metrics']!=first['metrics'] or not result['check']['valid']:raise ValueError(f'Report/result mismatch for {name}')
        entry.update(status='checked',solver_status=first['status'],tuple=tuples[SEEDS[0]],seeds_agree=True,
            programs=first['programs'],objective=int(first['objective']),bound=first['bound'],
            instance_sha256=first['instance_sha256'],
            per_seed=[dict(seed=seed,tuple=tuples[seed],objective=int(r['objective']),bound=r['bound'],status=r['status'])
                for seed,(r,_) in rows.items()],
            **load_plan_details(result,meals))
        variants.append(entry)
    base=next(v for v in variants if v['id']=='baseline')
    lot=instance['lot_size']
    for v in variants:
        if v['status']!='checked':continue
        v['meals_served']=(len(meals)-v['tuple'][0])*lot
        v['extra_meals_vs_today']=(base['tuple'][0]-v['tuple'][0])*lot
        v['waste_portions']=v['tuple'][1]*lot
        v['register_multiplier']=round(v['programs']/base['programs'],2)
    checked=[v for v in variants if v['status']=='checked']
    best_u=min(v['tuple'][0] for v in checked)
    # Highlighted option: best observed service, then fewest added skills, then smallest register.
    # A structural tie-break, not a price: wages and equipment prices were not supplied.
    best=[v for v in checked if v['tuple'][0]==best_u]
    cost=lambda v:(len(v.get('skills',[])) if v['kind']=='worker' else 1,v['programs'])
    highlighted=min(best,key=cost)
    tied=[v['id'] for v in best if cost(v)[0]==cost(highlighted)[0]]
    data=dict(schema='catering-investment.v1',
        question='What single change to the kitchen serves the most complete meals?',
        case=dict(scenario='S3',summary='12-customer lunch; cooker C2 is out from 20 to 60 minutes and an urgent order arrives.',
            customers=12,meals=len(meals),meal_ids=meals,lot_size=lot,total_meals=len(meals)*lot,
            horizon_minutes=instance['horizon_minutes'],time_origin=instance['time_origin'],grid_minutes=instance['grid_minutes'],
            workers=instance['workers'],equipment=instance['equipment'],
            available_minutes={k:sum(e-b for b,e in v) for k,v in instance['calendars'].items()},outages=state['outages'],
            urgent=instance['urgent_groups']),
        method=dict(solver='Raw-input CP reference (native slots, not the QUBO), same physical checker as all methods',
            seconds=240,cp_workers=2,seeds=SEEDS,optimality_proved=False,
            quantum_training=0,veloxq_calls=0,physical_qpu_calls=0,
            tuple_order='(U,W,B,R): missed complete meal lots, discarded component lots, new batches, plan changes; lower is better, compared left to right',
            reproduce='.venv/bin/python -m catering.investment --output NEW_DIR --seconds 240 --workers 2 --seed 2026'),
        variants=variants,
        decision=dict(best_missed_lots=best_u,today_missed_lots=base['tuple'][0],
            extra_meals=(base['tuple'][0]-best_u)*lot,fewest_skills_sufficient=highlighted['id'],equally_few_skills=tied,
            equipment_improved_service_in_runs=any(v['kind']=='equipment' and v['tuple'][0]<base['tuple'][0] for v in checked),
            bottleneck='W1 is the only worker who can prepare and the only one who can pack.',
            claims=['The best found third-cooker and repaired-C2 plans serve the same number of meals as today, while wasting one fewer component lot (ten portions).',
                'Adding a worker qualified for prepare or pack produces plans serving two more lots, or 20 more meals per lunch service; a cook-only worker gives no observed service gain.',
                'A single-task packing or prep helper attains the same U=3 as a fully flexible worker: a sufficient skill set, not the cheapest hire, because wages were not supplied.',
                'The observed 20-meal gain breaks even when its contribution margin covers the extra shift cost.',
                'No run proved optimality: this does not certify that equipment can never help or that 20 meals is the maximum gain.'],
            price_of_realism='A flexible worker multiplies the complete program register 8.3x (18,182 to 150,080); a single-task helper 2.0x (36,364).'),
        notes=['Best plans found within 240 s, not certified optima; both seeds return the same tuples.',
            'The core profile requires exactly one packing line, so a second line is reported as unsupported, not approximated.',
            'This is a classical decision study on the same model; the quantum methods solve cut portfolios of this register.'],
        doc='docs/CATERING_INVESTMENT.md',code='catering/investment.py')
    data['source_files']=list(sources.values())
    return data

def main():
    data=export()
    out=ROOT/'presentation/catering/investment/data.json';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(render(data))
    print('Exported',len(data['variants']),'variants; highlighted',data['decision']['fewest_skills_sufficient'])

if __name__=='__main__':main()
