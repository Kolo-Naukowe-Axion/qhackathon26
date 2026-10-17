"""Exact tiny pair-order QUBO expressiveness probe; never changes Stage 1.

All 216 machine-order combinations are scored before supervised coefficient
construction. This cost is part of the experiment, not a free formulation.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from fractions import Fraction
from functools import reduce
import hashlib
from itertools import combinations, permutations, product
import json
from math import gcd, lcm
from pathlib import Path
import time


PAIRS = tuple(combinations(range(3), 2))
TERMS = [()] + [(i,) for i in range(9)] + list(combinations(range(9), 2))


def features(bits, terms=TERMS):
    return [int(all(bits[i] for i in term)) for term in terms]


def order_from_bits(bits):
    for order in permutations(range(3)):
        if all(bits[k] == int(order.index(a) < order.index(b)) for k, (a,b) in enumerate(PAIRS)):
            return order
    return None


def earliest_schedule(instance, bits):
    """Topological longest paths on job chains and consecutive machine orders."""
    jobs = instance["jobs"]
    if len(jobs) != 3 or any(len(job["operations"]) != 3 for job in jobs):
        raise ValueError("This probe expects exactly three jobs and three common-route machines")
    route = [op["machine"] for op in jobs[0]["operations"]]
    if any([op["machine"] for op in job["operations"]] != route for job in jobs):
        raise ValueError("A common three-machine route is required")
    orders = [order_from_bits(bits[3*m:3*m+3]) for m in range(3)]
    if any(order is None for order in orders):
        return None
    predecessors = defaultdict(set)
    for job in range(3):
        for machine in range(1,3):
            predecessors[job,machine].add((job,machine-1))
    for machine, order in enumerate(orders):
        for a,b in zip(order,order[1:]):
            predecessors[b,machine].add((a,machine))
    ends, schedule = {}, []
    pending = {(j,m) for j in range(3) for m in range(3)}
    while pending:
        ready = sorted(node for node in pending if predecessors[node] <= ends.keys())
        if not ready:
            return None
        for j,m in ready:
            start = max((ends[node] for node in predecessors[j,m]),default=0)
            end = start + jobs[j]["operations"][m]["duration"]
            ends[j,m] = end
            schedule.append(dict(job=jobs[j]["id"],machine=route[m],start=start,end=end))
            pending.remove((j,m))
    return dict(makespan=max(ends.values()),schedule=schedule,
                machine_orders={route[m]:[jobs[j]["id"] for j in order] for m,order in enumerate(orders)})


def independent_grid_score(instance,bits):
    """Second scorer: release jobs in machine-sequence queues at integer ticks.

    It does not reuse the longest-path predecessor graph or computed starts.
    """
    orders = [order_from_bits(bits[3*m:3*m+3]) for m in range(3)]
    if any(order is None for order in orders):
        return None
    cursors = [0]*3
    free_at = [0]*3
    job_end = [[None]*3 for _ in range(3)]
    total_duration = sum(op["duration"] for job in instance["jobs"] for op in job["operations"])
    for tick in range(total_duration+1):
        for machine in range(3):
            if cursors[machine] == 3 or free_at[machine] > tick:
                continue
            job = orders[machine][cursors[machine]]
            if machine and (job_end[job][machine-1] is None or job_end[job][machine-1] > tick):
                continue
            end = tick + instance["jobs"][job]["operations"][machine]["duration"]
            job_end[job][machine] = end
            free_at[machine] = end
            cursors[machine] += 1
        if all(x == 3 for x in cursors):
            return max(free_at)
    raise AssertionError("Common-route machine orders failed to finish")


def rational_integers(values,max_denominator=100000):
    fractions = [Fraction(float(value)).limit_denominator(max_denominator) for value in values]
    multiplier = lcm(*(value.denominator for value in fractions))
    integers = [int(value*multiplier) for value in fractions]
    divisor = reduce(gcd,(abs(value) for value in integers if value),0) or 1
    return [value//divisor for value in integers], multiplier, divisor


def exact_equalities(matrix,targets,track_witness=False):
    """Rational RREF: exact fit or an independently checkable contradiction."""
    rows = [[Fraction(value) for value in row]+[Fraction(target)] for row,target in zip(matrix,targets)]
    weights = [{i:Fraction(1)} for i in range(len(rows))] if track_witness else None
    n = len(matrix[0]);pivot=0;pivots=[]
    for column in range(n):
        chosen = next((r for r in range(pivot,len(rows)) if rows[r][column]),None)
        if chosen is None:
            continue
        rows[pivot],rows[chosen] = rows[chosen],rows[pivot]
        if weights is not None:
            weights[pivot],weights[chosen] = weights[chosen],weights[pivot]
        denominator = rows[pivot][column]
        rows[pivot] = [value/denominator for value in rows[pivot]]
        if weights is not None:
            weights[pivot] = {i:value/denominator for i,value in weights[pivot].items()}
        for r in range(len(rows)):
            if r==pivot or not rows[r][column]:
                continue
            factor=rows[r][column]
            rows[r]=[a-factor*b for a,b in zip(rows[r],rows[pivot])]
            if weights is not None:
                for i,value in weights[pivot].items():
                    weights[r][i]=weights[r].get(i,Fraction(0))-factor*value
                    if not weights[r][i]:
                        del weights[r][i]
        pivots.append(column);pivot+=1
        if pivot==len(rows):
            break
    bad = next((i for i,row in enumerate(rows) if not any(row[:n]) and row[n]),None)
    if bad is not None:
        return dict(feasible=False,rank=len(pivots),contradiction=str(rows[bad][-1]),
                    witness={i:str(value) for i,value in weights[bad].items()} if weights is not None else None)
    solution=[Fraction(0)]*n
    for r,column in enumerate(pivots):
        solution[column]=rows[r][-1]
    return dict(feasible=True,rank=len(pivots),solution=solution)


def _model(coefficients,terms=TERMS):
    return dict(offset=coefficients[0],linear=[coefficients[terms.index((i,))] for i in range(max((max(term) for term in terms if term),default=-1)+1)],
        quadratic=[[term[0],term[1],coefficients[index]] for index,term in enumerate(terms) if len(term)==2 and coefficients[index]],
        coefficient_terms=[list(term) for term in terms],coefficients=coefficients,
        convention="offset + linear bits + upper-triangular-once pairs")


def model_energy(model,bits):
    """Direct coefficient evaluation, independent of the LP feature matrix."""
    return (model["offset"]+sum(a*b for a,b in zip(model["linear"],bits))
            +sum(value*bits[i]*bits[j] for i,j,value in model["quadratic"]))


def verify_and_reduce(instance,model,horizon):
    accepted=[];energies=[]
    for state in range(512):
        bits=[(state>>i)&1 for i in range(9)]
        energy=model_energy(model,bits);energies.append(energy)
        makespan=independent_grid_score(instance,bits)
        good=makespan is not None and makespan<=horizon
        assert energy==0 if good else energy>=1
        if energy==0:accepted.append(state)
    constants={i:(accepted[0]>>i)&1 for i in range(9)
               if len({(state>>i)&1 for state in accepted})==1}
    groups=[];remaining=set(range(9))-constants.keys();equalities=[]
    while remaining:
        representative=min(remaining)
        group=[i for i in sorted(remaining) if all(((state>>i)&1)==((state>>representative)&1) for state in accepted)]
        groups.append(group);remaining.difference_update(group)
        for i in group[1:]:
            margin=min(energy for state,energy in enumerate(energies)
                       if ((state>>i)&1)!=((state>>representative)&1))
            assert margin>=1
            equalities.append(dict(a=representative,b=i,minimum_energy_if_unequal=margin))
    index={old:new for new,group in enumerate(groups) for old in group}
    reduced=defaultdict(int)
    full_terms=[((),model["offset"])]+[((i,),value) for i,value in enumerate(model["linear"])]+[((i,j),value) for i,j,value in model["quadratic"]]
    for term,value in full_terms:
        if any(constants.get(i)==0 for i in term):continue
        target=tuple(sorted({index[i] for i in term if i not in constants}))
        reduced[target]+=value
    terms=[()]+[(i,) for i in range(len(groups))]+list(combinations(range(len(groups)),2))
    reduced_model=_model([reduced[term] for term in terms],terms)
    cases=[];recovered=[]
    for state in range(1<<len(groups)):
        bits=[(state>>i)&1 for i in range(len(groups))]
        full=[constants[i] if i in constants else bits[index[i]] for i in range(9)]
        energy=model_energy(reduced_model,bits)
        assert energy==model_energy(model,full)
        makespan=independent_grid_score(instance,full)
        assert (energy==0)==(makespan is not None and makespan<=horizon)
        full_state=sum(bit<<i for i,bit in enumerate(full))
        if energy==0:recovered.append(full_state)
        cases.append(dict(state=state,bits=bits,energy=energy,expanded_state=full_state,makespan=makespan))
    assert sorted(recovered)==accepted
    return dict(direct_polynomial_and_independent_schedule_checks=512,
        all_good_states_retained=True,accepted_full_states=accepted,
        forced_constants=constants,forced_equalities=equalities,
        fixing_method="Exhaustive conditional minimum energy of the certified nine-bit polynomial; no single optimum preselected",
        reduced_bits=len(groups),equal_variable_groups=groups,model=reduced_model,
        reduced_states_checked=len(cases),reduced_zero_states=sum(row["energy"]==0 for row in cases),
        reduced_cases=cases,all_good_schedules=[dict(state=state,**earliest_schedule(instance,[(state>>i)&1 for i in range(9)])) for state in accepted])


def partial_critical_path(instance,assignments):
    """Only fixed job arcs and the supplied physical pair-order arcs are used."""
    durations={(j,m):instance["jobs"][j]["operations"][m]["duration"] for j in range(3) for m in range(3)}
    predecessors={node:set() for node in durations}
    for j in range(3):
        for m in range(1,3):predecessors[j,m].add((j,m-1))
    for bit,value in assignments:
        machine,pair=divmod(bit,3);a,b=PAIRS[pair]
        if value==0:a,b=b,a
        predecessors[b,machine].add((a,machine))
    pending=set(durations);ends={};paths={}
    while pending:
        ready=sorted(node for node in pending if predecessors[node]<=ends.keys())
        if not ready:return None
        for node in ready:
            parent=max(predecessors[node],key=lambda n:(ends[n],n),default=None)
            ends[node]=(ends[parent] if parent is not None else 0)+durations[node]
            paths[node]=(paths[parent] if parent is not None else [])+[node]
            pending.remove(node)
    last=max(ends,key=lambda n:(ends[n],n))
    return dict(lower_bound=ends[last],critical_path=[dict(job=instance["jobs"][j]["id"],
        machine=instance["jobs"][j]["operations"][m]["machine"],duration=durations[j,m]) for j,m in paths[last]])


def _add_indicator(polynomial,assignments):
    terms={():1}
    for bit,value in assignments:
        next_terms=defaultdict(int)
        for term,coefficient in terms.items():
            if value==0:next_terms[term]+=coefficient
            next_terms[tuple(sorted((*term,bit)))]+=coefficient*(1 if value else -1)
        terms=next_terms
    for term,value in terms.items():polynomial[term]+=value


def _poly_record(polynomial):
    return dict(degree=max((len(term) for term,value in polynomial.items() if value),default=0),
        terms=[dict(bits=list(term),coefficient=value) for term,value in sorted(polynomial.items(),key=lambda item:(len(item[0]),item[0])) if value])


def _clauses(nogoods):
    clauses=[[-(bit+1) if value else bit+1 for bit,value in row["assignments"]] for row in nogoods]
    for machine in range(3):
        for values in ((0,1,0),(1,0,1)):
            clauses.append([-(3*machine+k+1) if value else 3*machine+k+1 for k,value in enumerate(values)])
    return clauses


def _clause_state(clause,assignment):
    unresolved=[]
    for literal in clause:
        variable=abs(literal)-1
        if variable not in assignment:unresolved.append(literal)
        elif assignment[variable]==int(literal>0):return True,[]
    return False,unresolved


def sat_proof(clauses,assumptions):
    """Tiny DPLL with checkable clause-reason unit propagation and split proofs."""
    nodes=0
    def search(assignment):
        nonlocal nodes
        nodes+=1;assignment=dict(assignment);steps=[]
        while True:
            propagated=False;unresolved_clauses=[]
            for cid,clause in enumerate(clauses):
                satisfied,unresolved=_clause_state(clause,assignment)
                if satisfied:continue
                if not unresolved:return False,dict(propagations=steps,conflict_clause=cid)
                unresolved_clauses.append(unresolved)
                if len(unresolved)==1:
                    literal=unresolved[0];variable=abs(literal)-1;value=int(literal>0)
                    assignment[variable]=value;steps.append(dict(variable=variable,value=value,reason_clause=cid))
                    propagated=True;break
            if propagated:continue
            if not unresolved_clauses:
                return True,{i:assignment.get(i,0) for i in range(9)}
            counts=Counter(abs(literal)-1 for clause in unresolved_clauses for literal in clause)
            variable=min(counts,key=lambda v:(-counts[v],v));children=[]
            for value in (0,1):
                feasible,proof=search({**assignment,variable:value})
                if feasible:return True,proof
                children.append(proof)
            return False,dict(propagations=steps,branch_variable=variable,zero=children[0],one=children[1])
    feasible,witness=search(assumptions)
    return dict(satisfiable=feasible,search_nodes=nodes,**({"model":witness} if feasible else {"unsat_proof":witness}))


def verify_unsat_proof(clauses,assumptions,proof):
    """Independent proof replay: every propagation and conflict is justified."""
    assignment=dict(assumptions)
    for row in proof["propagations"]:
        satisfied,remaining=_clause_state(clauses[row["reason_clause"]],assignment)
        assert not satisfied and len(remaining)==1
        literal=remaining[0]
        assert row["variable"]==abs(literal)-1 and row["value"]==int(literal>0)
        assert row["variable"] not in assignment
        assignment[row["variable"]]=row["value"]
    if "conflict_clause" in proof:
        satisfied,remaining=_clause_state(clauses[proof["conflict_clause"]],assignment)
        assert not satisfied and not remaining
    else:
        variable=proof["branch_variable"]
        assert variable not in assignment
        for value,key in ((0,"zero"),(1,"one")):
            verify_unsat_proof(clauses,{**assignment,variable:value},proof[key])


def structural_presolve(instance,horizon,nogoods,optimize_weights=True):
    """Structural SAT closure gives a QUBO directly; an LP can sparsify it."""
    clauses=_clauses(nogoods);queries=[];equalities=[]
    def query(assumptions):
        answer=sat_proof(clauses,assumptions)
        if answer["satisfiable"]:
            assert all(_clause_state(clause,answer["model"])[0] for clause in clauses)
            assert all(answer["model"][i]==value for i,value in assumptions.items())
        else:verify_unsat_proof(clauses,assumptions,answer["unsat_proof"])
        record=dict(assumptions=[list(row) for row in sorted(assumptions.items())],**answer)
        queries.append(record);return answer["satisfiable"]
    constants={}
    for bit in range(9):
        zero=query({bit:0});one=query({bit:1})
        if not zero and not one:return dict(structural_formula_unsatisfiable=True,sat_queries=queries)
        if not zero:constants[bit]=1
        if not one:constants[bit]=0
    for a,b in combinations(range(9),2):
        unequal01=query({a:0,b:1});unequal10=query({a:1,b:0})
        if not unequal01 and not unequal10:equalities.append([a,b])
    groups=[];remaining=set(range(9))-constants.keys()
    while remaining:
        representative=min(remaining)
        group=[i for i in sorted(remaining) if i==representative or [representative,i] in equalities]
        groups.append(group);remaining.difference_update(group)
    index={old:new for new,group in enumerate(groups) for old in group}
    sat_sources=[]
    for cut_id,row in enumerate(nogoods):
        if row["arity"]<=2:
            polynomial=defaultdict(int);_add_indicator(polynomial,row["assignments"])
            sat_sources.append((polynomial,dict(kind="physical_cut",index=cut_id)))
    for query_id,row in enumerate(queries):
        if not row["satisfiable"]:
            polynomial=defaultdict(int);_add_indicator(polynomial,row["assumptions"])
            sat_sources.append((polynomial,dict(kind="proved_sat_nogood",index=query_id)))
    for machine in range(3):
        a,b,c=range(3*machine,3*machine+3)
        sat_sources.append(({(b,):1,(a,b):-1,(b,c):-1,(a,c):1},dict(kind="triangle",index=machine)))
    sat_unique={}
    for polynomial,source in sat_sources:
        reduced=defaultdict(int)
        for term,value in polynomial.items():
            if any(constants.get(i)==0 for i in term):continue
            reduced[tuple(sorted({index[i] for i in term if i not in constants}))]+=value
        key=tuple(sorted((term,value) for term,value in reduced.items() if value))
        if not key:continue
        if key not in sat_unique:sat_unique[key]=dict(polynomial=dict(key),sources=[])
        sat_unique[key]["sources"].append(source)
    sat_polynomial=defaultdict(int)
    for row in sat_unique.values():
        for term,value in row["polynomial"].items():sat_polynomial[term]+=value
    n=len(groups);sat_terms=[()]+[(i,) for i in range(n)]+list(combinations(range(n),2))
    sat_model=_model([sat_polynomial[term] for term in sat_terms],sat_terms)
    sat_checks=[];sat_decoded=[]
    for bits in product((0,1),repeat=n):
        full=[constants[i] if i in constants else bits[index[i]] for i in range(9)]
        satisfying=all(_clause_state(clause,dict(enumerate(full)))[0] for clause in clauses)
        energy=model_energy(sat_model,bits)
        assert energy==0 if satisfying else energy>=1
        assert all(sum(value*int(all(bits[i] for i in term)) for term,value in row["polynomial"].items())>=0 for row in sat_unique.values())
        # The QUBO is already constructed; these schedules are validation only.
        makespan=independent_grid_score(instance,full)
        assert (energy==0)==(makespan is not None and makespan<=horizon)
        if energy==0:sat_decoded.append(dict(bits=list(bits),expanded_bits=full,**earliest_schedule(instance,full)))
        sat_checks.append(dict(bits=list(bits),energy=energy,structural_constraints_satisfied=satisfying,makespan=makespan))
    sat_lifted=defaultdict(int);representatives=[group[0] for group in groups]
    for term,value in sat_polynomial.items():
        sat_lifted[tuple(sorted(representatives[i] for i in term))]+=value
    for group in groups:
        for member in group[1:]:
            sat_lifted[(group[0],)]+=1;sat_lifted[(member,)]+=1
            sat_lifted[tuple(sorted((group[0],member)))]-=2
    for bit,value in constants.items():sat_lifted[()]+=value;sat_lifted[(bit,)]+=1-2*value
    sat_only=dict(reduced_bits=n,forced_constants=constants,equal_variable_groups=groups,
        structural_clause_count=len(clauses),sat_implication_queries=len(queries),
        sat_search_nodes=sum(row["search_nodes"] for row in queries),sat_queries=queries,
        independent_unsat_proof_replay=True,complete_schedule_scores_used_for_presolve=0,
        unique_reduced_nonnegative_cut_functions=len(sat_unique),weighted_lp_status=None,
        weighted_lp_message="Not needed: sum of distinct SAT-proved pair penalties and triangles is already quadratic",
        construction_lp_required=False,weighted_quadratic_exists=True,
        exact_integer_weights=[1]*len(sat_unique),cut_basis=[dict(sources=row["sources"],polynomial=_poly_record(row["polynomial"]),weight=1) for row in sat_unique.values()],
        all_higher_order_coefficients_cancel_exactly=True,model=sat_model,
        exact_reduced_state_checks=sat_checks,all_good_schedules=sat_decoded,
        complete_schedule_scores_used_for_weight_construction=0,
        lifted_nine_bit_model=_model([sat_lifted[term] for term in TERMS]))
    if not optimize_weights:return sat_only
    import numpy as np
    from scipy.optimize import linprog
    source_polynomials=[]
    for row in nogoods:
        polynomial=defaultdict(int);_add_indicator(polynomial,row["assignments"]);source_polynomials.append(polynomial)
    for machine in range(3):
        a,b,c=range(3*machine,3*machine+3)
        source_polynomials.append({(b,):1,(a,b):-1,(b,c):-1,(a,c):1})
    unique={}
    for source_id,polynomial in enumerate(source_polynomials):
        reduced=defaultdict(int)
        for term,value in polynomial.items():
            if any(constants.get(i)==0 for i in term):continue
            reduced[tuple(sorted({index[i] for i in term if i not in constants}))]+=value
        key=tuple(sorted((term,value) for term,value in reduced.items() if value))
        if not key:continue
        if key not in unique:unique[key]=dict(polynomial=dict(key),source_ids=[])
        unique[key]["source_ids"].append(source_id)
    basis=list(unique.values());n=len(groups)
    if n>6:return dict(reduced_bits=n,equal_variable_groups=groups,sat_queries=queries,weighted_quadratic_attempted=False)
    states=list(product((0,1),repeat=n))
    values=np.asarray([[sum(value*int(all(bits[i] for i in term)) for term,value in row["polynomial"].items())
                        for row in basis] for bits in states],dtype=int)
    assert values.min()>=0
    bad=np.any(values>0,axis=1)
    high_terms=sorted({term for row in basis for term in row["polynomial"] if len(term)>2})
    high=np.asarray([[row["polynomial"].get(term,0) for row in basis] for term in high_terms],dtype=float)
    result=linprog(np.ones(len(basis)),A_ub=-values[bad],b_ub=-np.ones(int(sum(bad))),
                   A_eq=high if len(high_terms) else None,b_eq=np.zeros(len(high_terms)) if high_terms else None,
                   bounds=(0,None),method="highs")
    report=dict(reduced_bits=n,forced_constants=constants,equal_variable_groups=groups,
        structural_clause_count=len(clauses),sat_implication_queries=len(queries),
        sat_search_nodes=sum(row["search_nodes"] for row in queries),sat_queries=queries,
        independent_unsat_proof_replay=True,complete_schedule_scores_used_for_presolve=0,
        unique_reduced_nonnegative_cut_functions=len(basis),weighted_lp_status=int(result.status),
        weighted_lp_message=result.message,construction_lp_required=True,sat_only_quadratic=sat_only)
    if not result.success:return report
    weights,_,_=rational_integers(result.x)
    assert all(weight>=0 for weight in weights)
    polynomial=defaultdict(int)
    for weight,row in zip(weights,basis):
        for term,value in row["polynomial"].items():polynomial[term]+=weight*value
    assert all(value==0 for term,value in polynomial.items() if len(term)>2)
    terms=[()]+[(i,) for i in range(n)]+list(combinations(range(n),2))
    model=_model([polynomial[term] for term in terms],terms)
    structural_checks=[];decoded=[]
    for bits,is_bad in zip(states,bad):
        energy=model_energy(model,bits)
        assert energy>=1 if is_bad else energy==0
        full=[constants[i] if i in constants else bits[index[i]] for i in range(9)]
        # Full scheduling is used only after the model has been constructed.
        makespan=independent_grid_score(instance,full)
        assert (energy==0)==(makespan is not None and makespan<=horizon)
        if energy==0:decoded.append(dict(bits=list(bits),expanded_bits=full,**earliest_schedule(instance,full)))
        structural_checks.append(dict(bits=list(bits),energy=energy,structural_constraints_satisfied=not bool(is_bad),makespan=makespan))
    report.update(weighted_quadratic_exists=True,exact_integer_weights=weights,
        cut_basis=[dict(source_ids=row["source_ids"],polynomial=_poly_record(row["polynomial"]),weight=weight)
                   for row,weight in zip(basis,weights)],
        all_higher_order_coefficients_cancel_exactly=True,model=model,
        exact_reduced_state_checks=structural_checks,all_good_schedules=decoded,
        complete_schedule_scores_used_for_weight_construction=0)
    # Lift back to all nine variables with unit equality penalties. The reduced
    # polynomial is nonnegative everywhere, so any broken equality costs >=1.
    lifted=defaultdict(int)
    representatives=[group[0] for group in groups]
    for term,value in polynomial.items():
        if value:lifted[tuple(sorted(representatives[i] for i in term))]+=value
    for group in groups:
        for member in group[1:]:
            lifted[(group[0],)]+=1;lifted[(member,)]+=1
            lifted[tuple(sorted((group[0],member)))]-=2
    for bit,value in constants.items():
        lifted[()]+=value;lifted[(bit,)]+=1-2*value
    report["lifted_nine_bit_model"]=_model([lifted[term] for term in TERMS])
    return report


def structural_probe(instance,horizon=8,optimize_weights=True):
    """Compile physical cuts before generating full-schedule verification labels."""
    started=time.perf_counter()
    polynomial=defaultdict(int)
    for machine in range(3):
        a,b,c=range(3*machine,3*machine+3)
        for term,value in [((b,),1),((a,b),-1),((b,c),-1),((a,c),1)]:polynomial[term]+=value
    nogoods=[];snapshots=[];evaluations=0;skipped=0
    for arity in (1,2,3):
        for indices in combinations(range(9),arity):
            for values in product((0,1),repeat=arity):
                assignments=frozenset(zip(indices,values))
                if any(set(tuple(pair) for pair in row["assignments"])<=assignments for row in nogoods):
                    skipped+=1;continue
                bound=partial_critical_path(instance,sorted(assignments));evaluations+=1
                if bound is not None and bound["lower_bound"]>horizon:
                    nogoods.append(dict(assignments=[list(pair) for pair in sorted(assignments)],arity=arity,**bound))
                    _add_indicator(polynomial,sorted(assignments))
        snapshots.append(dict(arity=arity,dag_subproblems=evaluations,subsumed_partial_assignments_skipped=skipped,
                              nogoods=len(nogoods),model=_poly_record(polynomial)))
    # Presolve/cut weighting consumes only physical cuts, before any full order
    # is scored for verification. Its sixteen decoder checks are post-construction.
    for row in nogoods:
        names={(j,m):(instance["jobs"][j]["id"],instance["jobs"][j]["operations"][m]["machine"]) for j in range(3) for m in range(3)}
        allowed={(names[j,m],names[j,m+1]) for j in range(3) for m in range(2)}
        for bit,value in row["assignments"]:
            machine,k=divmod(bit,3);a,b=PAIRS[k]
            if not value:a,b=b,a
            allowed.add((names[a,machine],names[b,machine]))
        path=row["critical_path"]
        duration_lookup={(instance["jobs"][j]["id"],instance["jobs"][j]["operations"][m]["machine"]):instance["jobs"][j]["operations"][m]["duration"] for j in range(3) for m in range(3)}
        assert all(node["duration"]==duration_lookup[node["job"],node["machine"]] for node in path)
        assert sum(node["duration"] for node in path)==row["lower_bound"]>horizon
        assert len({(node["job"],node["machine"]) for node in path})==len(path)
        assert all(((a["job"],a["machine"]),(b["job"],b["machine"])) in allowed for a,b in zip(path,path[1:]))
    presolve=structural_presolve(instance,horizon,nogoods,optimize_weights)
    # All complete-order labels below are verification only.
    labels=[independent_grid_score(instance,[(state>>i)&1 for i in range(9)]) for state in range(512)]
    for snapshot in snapshots:
        uncovered=[];false_rejections=[];zero_states=0
        for state in range(512):
            bits=[(state>>i)&1 for i in range(9)]
            energy=sum(row["coefficient"]*int(all(bits[i] for i in row["bits"])) for row in snapshot["model"]["terms"])
            assert energy>=0
            makespan=labels[state]
            good=makespan is not None and makespan<=horizon
            if energy==0:zero_states+=1
            if energy==0 and not good:uncovered.append(state)
            if energy and good:false_rejections.append(state)
        assert not false_rejections
        snapshot.update(verification_bitstrings=512,zero_states=zero_states,
                        uncovered_bad_states=uncovered,false_rejections=false_rejections,
                        exact_deadline_classifier=not uncovered)
    if presolve.get("weighted_quadratic_exists"):
        lifted=presolve["lifted_nine_bit_model"];good=[]
        for state,makespan in enumerate(labels):
            bits=[(state>>i)&1 for i in range(9)];energy=model_energy(lifted,bits)
            accepted=makespan is not None and makespan<=horizon
            assert energy==0 if accepted else energy>=1
            if accepted:good.append(state)
        expanded=[sum(bit<<i for i,bit in enumerate(row["expanded_bits"])) for row in presolve["all_good_schedules"]]
        assert sorted(expanded)==good
        presolve.update(full_domain_exact_verification_states=512,
                        all_deadline_feasible_states_retained=True,accepted_full_states=good,
                        minimum_bad_lifted_energy=min(model_energy(lifted,[(state>>i)&1 for i in range(9)]) for state,value in enumerate(labels) if value is None or value>horizon))
    return dict(schema="stage2-critical-path-rank-probe.v1",horizon=horizon,
        instance_sha256=hashlib.sha256(json.dumps(instance,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
        compiled_without_complete_schedule_labels=True,partial_dag_evaluations=evaluations,
        complete_schedule_scores_used_for_construction=0,critical_path_witnesses_independently_verified=len(nogoods),minimal_nogoods=nogoods,
        stages=snapshots,structural_presolve=presolve,elapsed_seconds_including_verification=time.perf_counter()-started,
        conclusion="Unary/pair cuts are insufficient; triple physical cuts plus certified SAT presolve and nonnegative weight cancellation yield a four-bit quadratic")


def classify_deadline(rows,horizon):
    import numpy as np
    from scipy.optimize import linprog
    matrix=np.asarray([row["features"] for row in rows],dtype=float)
    good=np.asarray([row["makespan"] is not None and row["makespan"]<=horizon for row in rows])
    # L1 minimization keeps a feasible separating polynomial small. All model
    # coefficients are free; auxiliary absolute values exist only in this LP.
    n=matrix.shape[1]
    constraints=[np.c_[-matrix[~good],np.zeros((sum(~good),n))],
                 np.c_[np.eye(n),-np.eye(n)],np.c_[-np.eye(n),-np.eye(n)]]
    result=linprog(np.r_[np.zeros(n),np.ones(n)],A_ub=np.vstack(constraints),
        b_ub=np.r_[-np.ones(sum(~good)),np.zeros(2*n)],
        A_eq=np.c_[matrix[good],np.zeros((sum(good),n))],b_eq=np.zeros(sum(good)),
        bounds=[(None,None)]*n+[(0,None)]*n,method="highs")
    report=dict(lp_status=int(result.status),lp_message=result.message,good_states=int(sum(good)),
                bad_states=int(sum(~good)),lp_coefficients=n,lp_absolute_value_auxiliaries=n)
    if result.success:
        coefficients,multiplier,divisor=rational_integers(result.x[:n])
        energies=[sum(a*b for a,b in zip(row["features"],coefficients)) for row in rows]
        if any(energy!=0 if accepted else energy<1 for energy,accepted in zip(energies,good)):
            raise AssertionError("Floating LP coefficients did not yield an exact integer certificate")
        report.update(feasible=True,exact_integer_certificate=True,
            denominator_lcm=multiplier,integer_gcd_removed=divisor,model=_model(coefficients),
            independently_checked_bitstrings=len(rows),minimum_bad_energy=min(energy for energy,accepted in zip(energies,good) if not accepted),
            maximum_good_abs_energy=max(abs(energy) for energy,accepted in zip(energies,good) if accepted),
            coefficient_abs_max=max(abs(value) for value in coefficients),
            nonzero_coefficients=sum(bool(value) for value in coefficients),
            energy_histogram=dict(sorted(Counter(energies).items())))
        return report
    # Exact Farkas certificate if no separating quadratic exists:
    # nonnegative bad-state mixture equals an unrestricted good-state span.
    dual_matrix=np.c_[matrix[~good].T,-matrix[good].T]
    dual=linprog(np.zeros(dual_matrix.shape[1]),A_eq=np.r_[dual_matrix,[np.r_[np.ones(sum(~good)),np.zeros(sum(good))]]],
        b_eq=np.r_[np.zeros(n),1],bounds=[(0,None)]*int(sum(~good))+[(None,None)]*int(sum(good)),method="highs")
    if not dual.success:
        report.update(feasible=False,exact_infeasibility_certificate=False)
        return report
    integers,_,_=rational_integers(dual.x)
    bad_ids=[i for i,yes in enumerate(good) if not yes];good_ids=[i for i,yes in enumerate(good) if yes]
    lambdas=integers[:len(bad_ids)];mus=integers[len(bad_ids):]
    if not all(value>=0 for value in lambdas) or sum(lambdas)<=0:
        raise AssertionError("Invalid exact Farkas sign/mass")
    for column in range(n):
        assert sum(weight*rows[i]["features"][column] for weight,i in zip(lambdas,bad_ids))==sum(weight*rows[i]["features"][column] for weight,i in zip(mus,good_ids))
    report.update(feasible=False,exact_infeasibility_certificate=True,
        bad_weights=[dict(state=rows[i]["state"],weight=weight) for i,weight in zip(bad_ids,lambdas) if weight],
        good_weights=[dict(state=rows[i]["state"],weight=weight) for i,weight in zip(good_ids,mus) if weight],
        positive_bad_mass=sum(lambdas))
    return report


def probe(instance,horizon=8):
    started=time.perf_counter()
    rows=[]
    for state in range(512):
        bits=[(state>>i)&1 for i in range(9)]
        schedule=earliest_schedule(instance,bits)
        grid=independent_grid_score(instance,bits)
        if (None if schedule is None else schedule["makespan"])!=grid:
            raise AssertionError("Independent scheduling scorers disagree")
        rows.append(dict(state=state,bits=bits,features=features(bits),makespan=grid))
    assert sum(row["makespan"] is not None for row in rows)==216
    classification=classify_deadline(rows,horizon)
    if classification.get("feasible"):
        classification["lossless_relation_reduction"]=verify_and_reduce(instance,classification["model"],horizon)
    valid=[row for row in rows if row["makespan"] is not None]
    equality=exact_equalities([row["features"] for row in valid],[row["makespan"] for row in valid],True)
    if not equality["feasible"]:
        witness=equality["witness"]
        weights={int(index):Fraction(weight) for index,weight in witness.items()}
        assert all(sum(weight*valid[index]["features"][column] for index,weight in weights.items())==0 for column in range(46))
        discrepancy=sum(weight*valid[index]["makespan"] for index,weight in weights.items())
        assert discrepancy
        equality["witness"]=[dict(state=valid[index]["state"],weight=str(weight),makespan=valid[index]["makespan"]) for index,weight in sorted(weights.items())]
        equality["exact_feature_moments_zero"]=True;equality["nonzero_makespan_moment"]=str(discrepancy)
    else:
        equality["solution"]=[str(value) for value in equality["solution"]]
    conditional=[]
    terms=[()]+[(i,) for i in range(3)]+list(combinations(range(3),2))
    # Every fixed pair of machine orders is retained, not just a successful one.
    for varied in range(3):
        other=[m for m in range(3) if m!=varied]
        for fixed in product(list(permutations(range(3))),repeat=2):
            bits=[0]*9
            for machine,order in zip(other,fixed):
                for k,(a,b) in enumerate(PAIRS):bits[3*machine+k]=int(order.index(a)<order.index(b))
            cases=[]
            for order in permutations(range(3)):
                local=[int(order.index(a)<order.index(b)) for a,b in PAIRS]
                sample=bits[:];sample[3*varied:3*varied+3]=local
                cases.append((local,earliest_schedule(instance,sample)["makespan"]))
            fit=exact_equalities([features(local,terms) for local,_ in cases],[value for _,value in cases])
            assert fit["feasible"]
            coefficients=fit["solution"]
            def energy(local):return sum(a*b for a,b in zip(features(local,terms),coefficients))
            maximum=max(value for _,value in cases)
            invalid=[list(local) for local in product((0,1),repeat=3) if order_from_bits(local) is None]
            penalty=max([Fraction(0)]+[maximum+1-energy(local) for local in invalid])
            # Triangle penalty b - a*b - b*c + a*c is one exactly on the two cycles.
            triangle=[0,0,1,0,-1,1,-1]
            final=[a+penalty*b for a,b in zip(coefficients,triangle)]
            assert all(sum(a*b for a,b in zip(features(local,terms),final))==value for local,value in cases)
            assert all(sum(a*b for a,b in zip(features(local,terms),final))>=maximum+1 for local in invalid)
            conditional.append(dict(varied_machine=varied,fixed_orders=[list(order) for order in fixed],
                rational_coefficients=[str(value) for value in final],triangle_penalty=str(penalty),
                makespans=[dict(bits=local,makespan=value) for local,value in cases]))
    digest=hashlib.sha256(json.dumps(instance,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return dict(schema="stage2-rank-probe.v1",instance_sha256=digest,horizon=horizon,
        variable_order=[dict(index=3*m+k,machine=instance["jobs"][0]["operations"][m]["machine"],before=instance["jobs"][a]["id"],after=instance["jobs"][b]["id"]) for m in range(3) for k,(a,b) in enumerate(PAIRS)],
        full_domain=dict(bits=9,bitstrings=512,valid_machine_order_combinations=216,
                         all_valid_orders_acyclic=True,independent_scorer_checks=512,
                         makespan_histogram=dict(sorted(Counter(row["makespan"] for row in valid).items()))),
        deadline_classification=classification,exact_makespan_quadratic=equality,
        conditional_rank=dict(bits=3,contexts=len(conditional),valid_permutations_per_context=6,
            independently_checked_local_states=len(conditional)*8,all_contexts_exact=True,contexts_detail=conditional),
        construction_cost=dict(complete_order_schedules_scored=216,bitstrings_classified=512,
            lp_required=True,exact_rational_elimination=True,
            lookup_supervision_disclosed=True,elapsed_seconds=time.perf_counter()-started),
        structural_critical_path_probe=structural_probe(instance,horizon),
        limitations=["Deadline QUBO coefficient construction first scores the complete tiny order domain; it is not a scalable free reduction.",
            "A zero-energy deadline classifier is not an exact makespan objective.",
            "Conditional three-bit QUBOs freeze the other two machine orders and cannot certify the global schedule optimum.",
            "No official Stage 1 artifact was changed; no QPU or paid solver was called."],rows=rows)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instance",type=Path,default=Path(__file__).resolve().parents[1]/"instances/instance_3x3.json")
    parser.add_argument("--horizon",type=int,default=8)
    parser.add_argument("--output",type=Path,default=Path(__file__).resolve().parents[1]/"output/stage2-search/rank-probe")
    parser.add_argument("--structural-only",action="store_true",help="Skip supervised coefficient fitting; compile physical/SAT constraints with optional cut-weight LP")
    parser.add_argument("--sat-only",action="store_true",help="Use the structural SAT-closure QUBO without optional cut-weight LP (stdlib only)")
    args=parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        parser.error("Use an empty output directory to preserve previous evidence")
    instance=json.loads(args.instance.read_text())
    result=structural_probe(instance,args.horizon,not args.sat_only) if args.structural_only or args.sat_only else probe(instance,args.horizon)
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/"report.json").write_text(json.dumps(result,indent=2)+"\n")
    (args.output/"instance.json").write_text(json.dumps(instance,indent=2)+"\n")
    structural=result if args.structural_only or args.sat_only else result["structural_critical_path_probe"]
    presolve=structural["structural_presolve"]
    if presolve.get("weighted_quadratic_exists"):
        for name,key,groups in [("structural-four-bit-model","model",presolve["equal_variable_groups"]),
                                ("structural-nine-bit-model","lifted_nine_bit_model",[[i] for i in range(9)])]:
            model=presolve[key]
            artifact=dict(schema="rank-deadline-qubo.v1",encoding="pair-order-structural-presolved" if key=="model" else "pair-order-structural-lifted",
                instance_sha256=structural["instance_sha256"],horizon=args.horizon,
                variables=[dict(index=i,original_order_bits=group) for i,group in enumerate(groups)],
                decoder=dict(equal_variable_groups=groups,forced_constants=presolve.get("forced_constants",{})),
                construction=dict(complete_schedule_scores_used=0,partial_dag_evaluations=structural["partial_dag_evaluations"],
                    sat_queries=presolve["sat_implication_queries"],sat_search_nodes=presolve["sat_search_nodes"],
                    cut_weight_lp_variables=presolve["unique_reduced_nonnegative_cut_functions"] if presolve["construction_lp_required"] else 0,
                    disclosure="Exact classical structural/SAT presolve; optional cut-weight LP; not free preprocessing or quantum advantage"),
                zero_energy_full_order_states=presolve["accepted_full_states"],**model)
            (args.output/f"{name}.json").write_text(json.dumps(artifact,indent=2)+"\n")
    print(json.dumps({key:value for key,value in result.items() if key not in ("rows","conditional_rank")},indent=2))


if __name__=="__main__":main()
