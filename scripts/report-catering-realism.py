"""Count representation costs on the complete cell, without changing or solving it."""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def report():
    from catering.contracts import load_bundle
    from catering.domain import residual_demand
    path=ROOT/'output/catering-complete-cell-v3/quantum-qubo.json'
    b=load_bundle(path);i,s=b['instance'],b['snapshot']
    assert not s['previous_unstarted']
    remaining=residual_demand(s)
    starts=len(range(s['current_time'],i['horizon_minutes'],i['grid_minutes']))
    crew=math.prod(sum(role in skills for skills in i['workers'].values()) for role in ['prepare','cook','pack','clean'])
    def naive(cookers=None,unit_yields=False,no_sharing=False):
        rows=[]
        for menu,recipe in sorted(i['menus'].items()):
            n=sum(remaining.get(d['id'],0) for d in s['demand_groups'] if d['menu']==menu)
            if not n:continue
            # Current cell has distinct unit-demand groups; allocations are ordered.
            assert all(remaining.get(d['id'],0)<=1 for d in s['demand_groups'] if d['menu']==menu)
            yields=[q for q in recipe['yields'] if not unit_yields or q==1]
            orders=sum(math.perm(n,r) for y in yields for r in range(1,min(y,n,1 if no_sharing else n)+1))
            configs=len(i['equipment']['prepare'])*(cookers or len(i['equipment']['cook']))*crew*orders
            activations=n*configs
            rows.append(dict(menu=menu,slots=n,configurations_per_slot=configs,activation_bits=activations,
                             start_bits=activations*3*starts))
        return dict(menus=rows,total_bits=sum(r['activation_bits']+r['start_bits'] for r in rows))
    rows=[]
    for name,keep,kwargs in [
        ('full',lambda p:True,{}),
        ('only-C1',lambda p:p['cooker']=='C1',dict(cookers=1)),
        ('unit-yields',lambda p:p['yield_lots']==1,dict(unit_yields=True)),
        ('no-sharing',lambda p:len(p['allocation_order'])==1,dict(no_sharing=True)),
    ]:
        programs=[p for p in b['options'] if keep(p)]
        anchors={min(p['allocation_order']) for p in programs}
        rows.append(dict(case=name,program_bits=len(programs),idle_bits=len(anchors),
                         chosen_bits=len(programs)+len(anchors),analytic_time_indexed=naive(**kwargs)))
    expected=[(35,1118),(10,559),(20,430),(33,774)]
    assert [(r['chosen_bits'],r['analytic_time_indexed']['total_bits']) for r in rows]==expected
    hot={tuple(sorted(e)) for g in b['onehot_groups'] for e in itertools.combinations(g['indices'],2)}
    conflicts={tuple(e) for e in b['conflicts']}
    objective={(t['i'],t['j']) for t in b['objective']['quadratic'] if int(t['value'])}
    hard=hot|conflicts
    ledger=dict(onehot_pairs=len(hot),cross_conflict_pairs=len(conflicts),
                objective_pairs=len(objective),new_objective_edges=len(objective-hard),
                reused_objective_edges=len(objective&hard),union_couplers=len(hard|objective))
    assert ledger==dict(onehot_pairs=236,cross_conflict_pairs=266,objective_pairs=200,
                       new_objective_edges=18,reused_objective_edges=182,union_couplers=520)
    return dict(schema='catering-realism-cost.v1',bundle_sha256=b['bundle_sha256'],
        source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),grid_starts=starts,rows=rows,couplers=ledger,
        comparator='Analytically specified unpruned optional-slot/configuration/three-phase-start construction; not an implemented or benchmarked reference QUBO.',
        limitations=['Independent feature restrictions from the full cell, not additive steps.',
                     'Counts do not measure solver speed, minimality or classical hardness.',
                     'Comparator covers this empty-prior-plan unit-demand cell; nonempty-prior exact-match registers need separate accounting.'],
        optimization_runs=0,training_runs=0,service_calls=0)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise ValueError('Fresh output required')
    r=report();args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
    print([(x['case'],x['chosen_bits'],x['analytic_time_indexed']['total_bits']) for x in r['rows']])
