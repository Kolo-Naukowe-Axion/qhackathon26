"""Ground-equivalent penalty conditioning for paired-course anchor QUBOs.

Frozen bundles are never changed. See docs/CATERING_VELOXQ_TUNING.md for the
strict-deletion proof, assumptions and the distinction from same-matrix runs.
"""
from collections import defaultdict
from copy import deepcopy

from .domain import digest
from .qubo import validate_bundle, energy

POLICY = 'deletion-bound.v1'


def polynomial(bundle, penalty):
    """Expand the declared objective plus one-hot and cross-conflict penalties."""
    obj = bundle['objective']
    constant = int(obj['constant'])
    linear = list(map(int, obj['linear']))
    pairs = defaultdict(int)
    for t in obj.get('quadratic', []):
        pairs[t['i'], t['j']] += int(t['value'])
    for group in bundle['onehot_groups']:
        constant += penalty
        indices = group['indices']
        for k, i in enumerate(indices):
            linear[i] -= penalty
            for j in indices[k+1:]:
                pairs[min(i,j), max(i,j)] += 2*penalty
    for i, j in bundle['conflicts']:
        pairs[min(i,j), max(i,j)] += penalty
    return dict(constant=str(constant), linear=list(map(str, linear)), quadratic=[
        dict(i=i,j=j,value=str(v)) for (i,j),v in sorted(pairs.items()) if v])


def condition_bundle(source):
    """Return a new hashed bundle with unchanged feasible costs and optima.

    D_i=max(0,-a_i)+sum_j max(0,-b_ij) bounds objective increase on deletion.
    P=1+max_i D_i makes every invalid assignment strictly improvable by deleting
    a program/filling an idle. Thus every global ground state is feasible.
    """
    validate_bundle(source)
    if source.get('encoding') != 'paired-course-anchor-onehot.v1' or source.get('registers'):
        raise ValueError('Paired anchor encoding without other registers required')
    n = len(source['linear'])
    obj = source['objective']
    if len(obj['linear']) != n:
        raise ValueError('Objective variable count mismatch')
    owner, idle = {}, set()
    for block, group in enumerate(source['onehot_groups']):
        indices = group['indices']
        if sorted(indices) != sorted(group['program_indices']+[group['idle_index']]):
            raise ValueError('Each block needs exactly its programs and one idle')
        idle.add(group['idle_index'])
        for i in indices:
            if type(i) is not int or i < 0 or i >= n or i in owner:
                raise ValueError('Blocks must partition variables')
            owner[i] = block
    if set(owner) != set(range(n)):
        raise ValueError('Blocks must partition variables')
    if idle != set(range(len(source['options']), n)):
        raise ValueError('Only idle variables may follow option variables')
    if any(int(obj['linear'][i]) for i in idle):
        raise ValueError('Idle choices must have zero objective cost')
    seen = set()
    drops = [max(0,-int(v)) for v in obj['linear']]
    for t in obj.get('quadratic', []):
        i,j,v = t['i'],t['j'],int(t['value'])
        if not 0 <= i < j < n or (i,j) in seen or i in idle or j in idle:
            raise ValueError('Canonical objective pairs must not involve idle choices')
        seen.add((i,j))
        drops[i] += max(0,-v)
        drops[j] += max(0,-v)
    seen = set()
    for i,j in source['conflicts']:
        if not 0 <= i < j < n or (i,j) in seen or i in idle or j in idle or owner[i] == owner[j]:
            raise ValueError('Canonical cross-block program conflicts required')
        seen.add((i,j))
    original = polynomial(source, int(source['penalty']))
    if any(source[k] != original[k] for k in original):
        raise ValueError('Frozen polynomial has undeclared penalties or terms')
    penalty = max(drops,default=0)+1
    bundle = deepcopy(source)
    bundle.update(polynomial(source,penalty))
    bundle['bundle_id'] += '/'+POLICY
    bundle['representation_id'] += '/'+POLICY
    bundle['penalty'] = str(penalty)
    bundle['penalty_proof'] = 'P > every single-program objective deletion-loss bound; idle-neutral deletion strictly improves every infeasible assignment'
    bundle['conditioning'] = dict(policy=POLICY,source_bundle_sha256=source['bundle_sha256'],
        source_penalty=source['penalty'],max_deletion_loss=str(penalty-1),
        feasible_objective_unchanged=True,variable_order_unchanged=True,
        invalid_state_energies_unchanged=False,existing_frozen_runs_remain_valid=True)
    bundle['size']['couplers'] = len(bundle['quadratic'])
    if 'coefficients' in bundle:
        bundle['coefficients']['max_abs'] = max([abs(int(bundle['constant']))]+list(map(lambda x:abs(int(x)),bundle['linear']))+[abs(int(t['value'])) for t in bundle['quadratic']])
    bundle['bundle_sha256'] = digest({k:v for k,v in bundle.items() if k != 'bundle_sha256'})
    return validate_bundle(bundle)


def rescore_result(source, sampling_bundle, result):
    """Map all raw returns to frozen energies without repairing or dropping rows."""
    validate_bundle(source); validate_bundle(sampling_bundle)
    if sampling_bundle.get('conditioning',{}).get('source_bundle_sha256') != source['bundle_sha256']:
        raise ValueError('Conditioned input does not refer to frozen source')
    if result['bundle_sha256'] != sampling_bundle['bundle_sha256']:
        raise ValueError('Result/variable mapping mismatch')
    mapped = deepcopy(result)
    mapped['bundle_sha256'] = source['bundle_sha256']
    mapped['representation_id'] = source['representation_id']
    mapped['sampling_bundle_sha256'] = sampling_bundle['bundle_sha256']
    mapped['configuration']['conditioning'] = sampling_bundle['conditioning']
    # Preserve any adapter-specific identity under an explicitly different name.
    if 'bundle' in mapped:
        mapped['sampling_bundle'] = mapped.pop('bundle')
    for sample in mapped['samples']:
        actual = energy(sampling_bundle,sample['bits'])
        if int(sample['reported_energy']) != actual:
            raise ValueError('Sampling energy mismatch')
        sample['sampling_energy'] = str(actual)
        sample['bits'] = lift_bits(source,sampling_bundle,sample['bits'])
        sample['reported_energy'] = str(energy(source,sample['bits']))
    mapped['samples'].sort(key=lambda s:(int(s['reported_energy']),s['bits']))
    mapped['reference'] = None
    return mapped


def eliminate_idle(source):
    """Replace exactly-one(programs,idle) by at-most-one(programs).

    Each feasible assignment has a unique idle completion. Pair exclusions and
    the same deletion bound guarantee feasible global ground states without the
    large negative -P bias on every program. Invalid states are not equivalent.
    """
    checked=condition_bundle(source)  # Verify every assumption and source term.
    n=len(source['options']);penalty=int(checked['penalty'])
    bundle=deepcopy(source)
    edges={tuple(edge) for edge in source['conflicts']}
    for g in source['onehot_groups']:
        for k,i in enumerate(g['program_indices']):
            for j in g['program_indices'][k+1:]:edges.add((min(i,j),max(i,j)))
    obj=deepcopy(source['objective']);obj['linear']=obj['linear'][:n]
    pairs=defaultdict(int)
    for t in obj.get('quadratic',[]):pairs[t['i'],t['j']]+=int(t['value'])
    for edge in edges:pairs[edge]+=penalty
    bundle.update(encoding='paired-course-atmostone-noidle.v1',onehot_groups=[],
        constant=obj['constant'],linear=obj['linear'].copy(),objective=obj,
        quadratic=[dict(i=i,j=j,value=str(v)) for (i,j),v in sorted(pairs.items()) if v],
        conflicts=[list(edge) for edge in sorted(edges)],variable_order=source['variable_order'][:n],
        penalty=str(penalty),penalty_proof='P exceeds every program deletion-loss bound; delete an endpoint of any selected exclusion edge')
    bundle['bundle_id']+='/no-idle-deletion.v1'
    bundle['representation_id']+='/no-idle-deletion.v1'
    bundle['conditioning']=dict(policy='no-idle-deletion.v1',source_bundle_sha256=source['bundle_sha256'],
        source_penalty=source['penalty'],max_deletion_loss=str(penalty-1),
        feasible_objective_unchanged=True,variable_order_unchanged=False,
        program_variable_order_unchanged=True,removed_idle_bits=len(source['onehot_groups']),
        invalid_state_energies_unchanged=False,existing_frozen_runs_remain_valid=True)
    bundle['size'].update(binary_variables=n,idle_data_bits=0,auxiliary_bits=0,couplers=len(bundle['quadratic']))
    bundle.pop('mixer',None)
    bundle['bundle_sha256']=digest({k:v for k,v in bundle.items() if k!='bundle_sha256'})
    return validate_bundle(bundle)


def lift_bits(source,sampling_bundle,bits):
    """Restore only redundant idle choices; preserve all program bits, even invalid."""
    from .qubo import checked_bits
    checked_bits(sampling_bundle,bits)
    policy=sampling_bundle.get('conditioning',{}).get('policy')
    if policy==POLICY:
        if sampling_bundle['variable_order']!=source['variable_order']:
            raise ValueError('Variable mapping mismatch')
        return bits.copy()
    if policy!='no-idle-deletion.v1' or sampling_bundle['variable_order']!=source['variable_order'][:len(source['options'])]:
        raise ValueError('Unsupported source variable mapping')
    out=bits.copy()+[0]*len(source['onehot_groups'])
    for g in source['onehot_groups']:
        out[g['idle_index']]=int(not any(out[i] for i in g['program_indices']))
    return out
