"""Resource-connected conditional column QUBOs with an invariant mixer.

The global finite-pool energy is substituted exactly. Two choices per selected
component become one binary variable; the complete local makespan register uses
a single-excitation XY mixer. Full schedules remain independently checked.
"""
from dataclasses import dataclass
import itertools
import random
from types import SimpleNamespace

from .planning_compressed import compress, expand
from .trajectory_mixer import sample


@dataclass
class ConditionalMaster:
    parent: object
    reduction: dict
    fixed: dict
    free: list
    columns: list
    makespans: list
    linear: list
    quadratic: dict
    offset: int
    penalty: int

    def energy(self, bits):
        return self.offset + sum(c*x for c,x in zip(self.linear,bits)) + sum(
            c*bits[i]*bits[j] for (i,j),c in self.quadratic.items())

    def full_bits(self, bits):
        values = expand(self.reduction,bits)
        full = [self.fixed.get(i,0) for i in range(len(self.parent.linear))]
        for i,value in zip(self.free,values):
            full[i] = value
        if self.energy(bits) != self.parent.energy(full):
            raise AssertionError('Conditional mapped energy differs from full master')
        return full

    def decode(self, bits):
        return self.parent.decode(self.full_bits(bits))


def conditional_master(q, incumbent, alternatives):
    """Exactly retain the supplied two choices per group and all local Cmaxes."""
    if not q.decode(incumbent)['valid']:
        raise ValueError('Valid incumbent required')
    free = []
    choice_ends = []
    selected = set(alternatives)
    for name, alternative in alternatives.items():
        old = next(i for i in q.groups[name] if incumbent[i])
        if alternative not in q.groups[name] or alternative == old:
            raise ValueError('Different alternative in each selected component required')
        free.extend(sorted((old,alternative)))
        choice_ends.append((q.variables[old]['end'],q.variables[alternative]['end']))
    fixed_end = max((q.variables[i]['end'] for name in q.columns if name not in selected
                     for i in q.groups[name] if incumbent[i]),default=0)
    # Include every maximum that can result from a local combination, including
    # invalid resource combinations; no feasible-state oracle is used here.
    ends = {max((fixed_end,*times)) for times in itertools.product(*choice_ends)}
    available = {q.variables[i]['end']:i for i in q.groups['@makespan']}
    # A globally feasible DAG makespan ends at a terminal. Nonterminal maxima
    # absent from the original register cannot describe a feasible full plan.
    cmax = [available[end] for end in sorted(ends) if end in available]
    if not cmax:
        raise AssertionError('Incumbent makespan absent')
    free.extend(cmax)
    fixed = {i:(0 if i in q.groups['@makespan'] else incumbent[i])
             for i in range(len(q.linear)) if i not in free}
    # Compress component one-hot pairs only, leaving the makespan invariant
    # register explicit even when its size is one or two.
    proxy = SimpleNamespace(linear=q.linear,quadratic=q.quadratic,offset=q.offset,
                            groups={name:group for name,group in q.groups.items() if name!='@makespan'})
    reduction = compress(proxy,free,fixed)
    block = reduction['block']
    if len(block['linear']) > 16:
        raise ValueError('Local statevector limit16 qubits')
    return ConditionalMaster(q,reduction,fixed,free,list(alternatives),
                             [q.variables[i]['end'] for i in cmax],
                             block['linear'],block['quadratic'],block['offset'],q.penalty)


def conflict_graph(q):
    graph = [set() for _ in q.linear]
    for i,j in q.pair_conflicts:
        graph[i].add(j)
        graph[j].add(i)
    return graph


def propose(q, incumbent, rng, graph, width=5):
    """Close a proposed column's conflicts with the current selected columns.

    Selection reads only columns and the global QUBO conflict graph. Native CP
    solutions and bounds never enter proposal construction or sampling.
    """
    current = {name:next(i for i in q.groups[name] if incumbent[i]) for name in q.columns}
    owner = {i:name for name,group in q.groups.items() if name!='@makespan' for i in group}
    names = list(current)
    rng.shuffle(names)
    for root in names:
        candidates = [i for i in q.groups[root] if i!=current[root]]
        rng.shuffle(candidates)
        candidates.sort(key=lambda i:(q.variables[i]['end']>q.variables[current[root]]['end']))
        for target in candidates[:24]:
            blockers = {owner[i] for i in graph[target] if incumbent[i]}
            selected = {root,*blockers}
            if len(selected)>width:
                continue
            order = root.split('/')[0]
            extras = [name for name in names if name not in selected and name.split('/')[0]==order]
            selected.update(extras[:max(0,width-len(selected))])
            outside = {current[name] for name in names if name not in selected}
            if graph[target]&outside:
                continue
            alternatives = {root:target}
            failed = False
            for name in sorted(selected-{root}):
                options = [i for i in q.groups[name] if i!=current[name]
                           and not graph[i]&outside and target not in graph[i]]
                if not options:
                    if name in blockers:
                        failed = True
                        break
                    continue
                # Earliest candidate among a randomized short list gives timing
                # pressure without a global optimum or CP reference as teacher.
                rng.shuffle(options)
                options.sort(key=lambda i:q.variables[i]['end'])
                alternatives[name] = rng.choice(options[:min(3,len(options))])
            if not failed:
                return alternatives
    return None


def search(q, initial, method='qaoa_xy', seed=7, iterations=64, shots=32, evaluations=64, layers=2):
    import time
    import numpy as np
    from .planning_quantum import energy_table
    began, cpu = time.perf_counter(), time.process_time()
    incumbent = list(initial)
    rng = random.Random(seed)
    graph = conflict_graph(q)
    history = []
    best = q.energy(incumbent)
    for iteration in range(iterations):
        alternatives = propose(q,incumbent,rng,graph)
        if not alternatives:
            history.append(dict(iteration=iteration,skipped='no bounded resource-connected proposal'))
            break
        local = conditional_master(q,incumbent,alternatives)
        if method=='exact':
            energies = energy_table(dict(linear=local.linear,quadratic=local.quadratic,offset=local.offset))
            index = int(np.argmin(energies))
            bits = [(index>>i)&1 for i in range(len(local.linear))]
            result = dict(method='exact',bits=bits,energy=int(energies[index]),decoded=local.decode(bits),
                          qubits=len(local.linear),physical_qpu_calls=0)
        else:
            result = sample(local,seed+iteration*1009,layers,evaluations,shots,method)
        candidate = local.full_bits(result['bits'])
        accepted = result['decoded']['valid'] and result['energy']<=q.energy(incumbent)
        if accepted:
            incumbent = candidate
        best = min(best,q.energy(incumbent))
        history.append(dict(iteration=iteration,alternatives=alternatives,
             previous_best=best,accepted=accepted,incumbent_energy=q.energy(incumbent),
             free=local.free,fixed=[[i,v] for i,v in sorted(local.fixed.items())],
             reduction=local.reduction['eliminated'],sample=result))
    final = q.decode(incumbent)
    if not final['valid']:
        raise AssertionError('Conditional column search lost raw feasible incumbent')
    return dict(method=method,seed=seed,iterations=iterations,shots=shots,layers=layers,
                angle_evaluations_per_block=evaluations,initial_energy=q.energy(initial),
                energy=q.energy(incumbent),bits=incumbent,decoded=final,history=history,
                physical_qpu_calls=0,wall_seconds=time.perf_counter()-began,
                process_cpu_seconds=time.process_time()-cpu,
                scope='Heuristic resource-connected conditional search of a restricted component pool. Exact affine energies; no CP teacher. Runtime budgets differ by method; quantum angles use classical exact expectations.')
