"""No service calls: exhaustive ground-state and strict-descent proof checks."""
from copy import deepcopy
import itertools
import random

import pytest
from catering.conditioning import condition_bundle, polynomial, rescore_result
from catering.domain import digest
from catering.contracts import load_bundle, method_result
from catering.qubo import energy, objective_energy


def toy(seed):
    b = deepcopy(load_bundle('output/catering-complete-cell-v3/quantum-qubo.json'))
    rng = random.Random(seed)
    b['options'] = b['options'][:4]
    b['variable_order'] = [f'option:{i}' for i in range(4)]+['idle:a','idle:b']
    b['onehot_groups'] = [dict(indices=[0,1,4],program_indices=[0,1],idle_index=4),
                          dict(indices=[2,3,5],program_indices=[2,3],idle_index=5)]
    b['conflicts'] = [[0,2],[1,3]]
    b['objective'] = dict(constant=str(rng.randint(-10,10)),
        linear=[str(rng.randint(-10,10)) for _ in range(4)]+['0','0'],
        quadratic=[dict(i=i,j=j,value=str(rng.randint(-10,10))) for i,j in itertools.combinations(range(4),2)])
    b['penalty'] = '1000'
    b.update(polynomial(b,1000))
    b['size']['binary_variables']=6;b['size']['couplers']=len(b['quadratic'])
    b['bundle_sha256']=digest({k:v for k,v in b.items() if k!='bundle_sha256'})
    return b


def feasible(b,bits):
    return (all(sum(bits[i] for i in g['indices'])==1 for g in b['onehot_groups'])
            and all(not(bits[i] and bits[j]) for i,j in b['conflicts']))


def descent(b,bits):
    """Construct the proof's next strict improvement; never used to repair results."""
    out=bits.copy()
    for g in b['onehot_groups']:
        chosen=[i for i in g['indices'] if bits[i]]
        if not chosen:
            out[g['idle_index']]=1;return out
        if len(chosen)>1:
            out[chosen[0]]=0;return out
    for i,j in b['conflicts']:
        if bits[i] and bits[j]:
            out[i]=0
            g=next(g for g in b['onehot_groups'] if i in g['indices'])
            out[g['idle_index']]=1
            return out
    return None


@pytest.mark.parametrize('seed', range(20))
def test_every_invalid_state_has_strict_descent_and_same_ground(seed):
    src=toy(seed);b=condition_bundle(src)
    before=[];after=[]
    for state in itertools.product((0,1),repeat=6):
        bits=list(state);e=energy(b,bits)
        before.append((energy(src,bits),state));after.append((e,state))
        if feasible(b,bits):
            assert e==energy(src,bits)==objective_energy(b,bits)
        else:
            next_bits=descent(b,bits)
            assert next_bits is not None and energy(b,next_bits)<e
    best=min(e for e,_ in before)
    assert {s for e,s in before if e==best}=={s for e,s in after if e==min(v for v,_ in after)}


def test_complete_cell_sector_energies_and_optimum_unchanged():
    from catering.meal_blocks import sector_data, sector_bits
    from catering.decode import decode
    src=load_bundle('output/catering-complete-cell-v3/quantum-qubo.json')
    old=digest(src);b=condition_bundle(src)
    assert digest(src)==old
    a=sector_data(src);c=sector_data(b)
    assert (a['valid']==c['valid']).all()
    assert (a['objective']==c['objective']).all()
    assert (a['energy'][a['valid']]==c['energy'][c['valid']]).all()
    assert int(a['energy'].min())==int(c['energy'].min())==68
    for idx in [int(a['energy'].argmin()),0,100,1044]:
        bits=sector_bits(b,c,idx)
        assert energy(b,bits)==int(c['energy'][idx])
        assert decode(src,bits)['valid']==decode(b,bits)['valid']


@pytest.mark.parametrize('mutation', ['idle_linear','idle_pair','missing_block','conflict_idle','hidden_term'])
def test_refuse_unproven_structure(mutation):
    b=toy(1)
    if mutation=='idle_linear':b['objective']['linear'][4]='1'
    if mutation=='idle_pair':b['objective']['quadratic'].append(dict(i=0,j=4,value='-1'))
    if mutation=='missing_block':b['onehot_groups'][0]['indices'].remove(0)
    if mutation=='conflict_idle':b['conflicts']=[[0,4]]
    if mutation=='hidden_term':b['linear'][0]=str(int(b['linear'][0])+1)
    b['bundle_sha256']=digest({k:v for k,v in b.items() if k!='bundle_sha256'})
    with pytest.raises(ValueError):condition_bundle(b)


def test_rescore_preserves_invalid_rows_counts_and_sampling_energy():
    src=toy(4);b=condition_bundle(src)
    rows=[dict(bits=[1,0,0,1,0,0],count=7,reported_energy=str(energy(b,[1,0,0,1,0,0]))),
          dict(bits=[1]*6,count=3,reported_energy=str(energy(b,[1]*6)))]
    result=method_result(b,'fake',rows)
    mapped=rescore_result(src,b,result)
    assert mapped['bundle_sha256']==src['bundle_sha256']
    assert sum(s['count'] for s in mapped['samples'])==10
    for s in mapped['samples']:
        assert int(s['reported_energy'])==energy(src,s['bits'])
        assert int(s['sampling_energy'])==energy(b,s['bits'])
    assert result['bundle_sha256']==b['bundle_sha256']


@pytest.mark.parametrize('seed',range(20))
def test_noidle_bijection_and_strict_descent(seed):
    from catering.conditioning import eliminate_idle,lift_bits
    src=toy(seed);b=eliminate_idle(src)
    feasible_states=[];grounds=[]
    for state in itertools.product((0,1),repeat=4):
        bits=list(state);lifted=lift_bits(src,b,bits)
        e=energy(b,bits)
        bad=next(((i,j) for i,j in b['conflicts'] if bits[i] and bits[j]),None)
        grounds.append((e,feasible(src,lifted)))
        if bad:
            changed=bits.copy();changed[bad[0]]=0
            assert energy(b,changed)<e
        else:
            assert feasible(src,lifted)
            assert e==energy(src,lifted)==objective_energy(src,lifted)
            feasible_states.append((tuple(lifted),e))
    expected=[(s,energy(src,list(s))) for s in itertools.product((0,1),repeat=6) if feasible(src,s)]
    assert sorted(expected)==sorted(feasible_states)
    minimum=min(e for e,_ in grounds)
    assert all(valid for e,valid in grounds if e==minimum)
    result=method_result(b,'fake',[dict(bits=[1,1,1,1],count=3,reported_energy=str(energy(b,[1,1,1,1])))])
    mapped=rescore_result(src,b,result)
    assert mapped['samples'][0]['bits'][:4]==[1,1,1,1]
    assert len(mapped['samples'][0]['bits'])==6
    assert not feasible(src,mapped['samples'][0]['bits'])
