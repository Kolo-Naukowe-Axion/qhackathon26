"""Complete-meal QUBO with one-hot demand-anchor blocks and local XY mixers."""
from collections import Counter,defaultdict
import math

from .domain import fixture,snapshot,validate_instance,make_plan,residual_demand,digest
from .check import check_plan
from .paired_meals import PROFILE,active_meals
from .options import claims,conflict
from .qubo import validate_bundle


def meal_fixture(customers=4):
    p=fixture();p["profile_id"]=PROFILE;p["instance_id"]=f"paired-lunch-{customers}-v1"
    p["horizon_minutes"]=max(160,80+20*customers)
    p["calendars"]={r:[[0,p["horizon_minutes"]]] for r in p["calendars"]}
    p["menus"]["C"]=dict(yields=[1,2],prepare=10,cooking={"1":10,"2":20},
                           cook_attendance=10,pack_per_lot=10,clean=10,max_age=40)
    p["previous_unstarted"]=[]
    p["demand_groups"]=p["demand_groups"][:1]+[
        dict(id="committed/side",menu="C",lots=1,departure=80,revealed=0,priority=1)]
    meals=[dict(id="committed",main="A/11:50",side="committed/side",priority=1)]
    for i in range(customers):
        departure=100+20*i
        for course,menu in (("main","B"),("side","C")):
            p["demand_groups"].append(dict(id=f"customer-{i}/{course}",menu=menu,lots=1,
                                           departure=departure,revealed=0,priority=1))
        meals.append(dict(id=f"customer-{i}",main=f"customer-{i}/main",side=f"customer-{i}/side",priority=1))
    p["urgent_groups"]=[dict(id="urgent/"+course,menu=menu,lots=1,departure=p["horizon_minutes"],revealed=20,priority=1)
                           for course,menu in (("main","B"),("side","C"))]
    meals.append(dict(id="urgent",main="urgent/main",side="urgent/side",priority=1))
    p["service_model"]=dict(kind="two-course-unit.v1",meals=meals)
    return validate_instance(p)


def stratified_pool(programs,cap):
    """Nested coverage/cooker strata, then early/late timing diversity.

    No reference, whole-kitchen optimizer, feasibility search or target plan is
    used. This is a lossy heuristic, with its physical opportunity cost measured.
    """
    buckets=defaultdict(list)
    for p in programs:
        buckets[(tuple(sorted(p["allocation_order"])),p["cooker"])].append(p)
    streams=[]
    for key,values in sorted(buckets.items(),key=lambda item:(-len(item[0][0]),item[0])):
        values=sorted(values,key=lambda p:(p["pack_start"],p["cook_start"],p["prep_start"],p["id"]))
        # Early, late, next early, next late. Preserve alternatives to a greedy
        # first choice without solving the complete planning problem.
        stream=[]
        left,right=0,len(values)-1
        while left<=right:
            stream.append(values[left]);left+=1
            if left<=right:stream.append(values[right]);right-=1
        streams.append(stream)
    selected=[];depth=0
    while len(selected)<cap:
        added=False
        for stream in streams:
            if depth<len(stream):
                selected.append(stream[depth]);added=True
                if len(selected)==cap:break
        if not added:break
        depth+=1
    return sorted(selected,key=lambda p:p["id"])


def compile_meal_blocks(instance,state,programs,*,parent_domain_sha256=None,complete_domain=False):
    validate_instance(instance)
    if instance["profile_id"]!=PROFILE:raise ValueError("Paired-meal profile required")
    fixed=state["fixed_batches"];remaining=residual_demand(state)
    if any(q!=1 for q in remaining.values()):raise ValueError("Unit component groups required")
    if len({p["id"] for p in programs})!=len(programs):raise ValueError("Duplicate program")
    if not check_plan(instance,state,make_plan(instance,fixed,state.get("recovery_operations",[])))["valid"]:
        raise ValueError("Invalid committed boundary")
    for p in programs:
        if not p["allocation_order"] or len(set(p["allocation_order"]))!=len(p["allocation_order"]):
            raise ValueError("Nonempty distinct unit allocations required")
        if any(g not in remaining for g in p["allocation_order"]):raise ValueError("Nonresidual allocation")
        if not check_plan(instance,state,make_plan(instance,fixed+[p],state.get("recovery_operations",[])))["valid"]:
            raise ValueError("Invalid local program")
    n=len(programs);blocks=defaultdict(list)
    for i,p in enumerate(programs):blocks[min(p["allocation_order"])].append(i)
    groups=[dict(anchor=anchor,program_indices=indices,idle_index=n+j,indices=indices+[n+j])
            for j,(anchor,indices) in enumerate(sorted(blocks.items()))]
    total=n+len(groups)
    previous={p["id"] for p in state["previous_unstarted"]}
    fixed_coverage=Counter(g for p in fixed for g in p["allocation_order"])
    cover=defaultdict(list)
    for i,p in enumerate(programs):
        for g in p["allocation_order"]:cover[g].append(i)
    meals=active_meals(instance,state)
    bounds=dict(U=sum(m["priority"] for m in meals),
                W=sum(p["yield_lots"] for p in fixed+programs),B=n,R=n+len(previous))
    weights={}
    for key in reversed(("U","W","B","R")):
        weights[key]=1+sum(weights[k]*bounds[k] for k in weights)
    constant=weights["U"]*bounds["U"]+weights["R"]*len(previous)
    constant+=weights["W"]*sum(p["yield_lots"]-len(p["allocation_order"]) for p in fixed)
    linear=[0]*total;pairs=defaultdict(int)
    for i,p in enumerate(programs):
        linear[i]=weights["W"]*(p["yield_lots"]-len(p["allocation_order"]))+weights["B"]+weights["R"]*(-1 if p["id"] in previous else 1)
    def product(main,side,coefficient):
        nonlocal constant
        a,b=fixed_coverage[main],fixed_coverage[side]
        constant+=coefficient*a*b
        for i in cover[main]:linear[i]+=coefficient*b
        for j in cover[side]:linear[j]+=coefficient*a
        for i in cover[main]:
            for j in cover[side]:
                if i==j:linear[i]+=coefficient
                else:pairs[tuple(sorted((i,j)))]+=coefficient
    for meal in meals:
        a,b=meal["main"],meal["side"]
        constant+=weights["W"]*(fixed_coverage[a]+fixed_coverage[b])
        for i in cover[a]+cover[b]:linear[i]+=weights["W"]
        product(a,b,-weights["U"]*meal["priority"]-2*weights["W"])
    objective_pairs={key:value for key,value in pairs.items() if value}
    objective_linear=linear.copy();objective_constant=constant
    span=sum(abs(c) for c in linear)+sum(abs(c) for c in objective_pairs.values())
    penalty=span+1
    membership={i:j for j,g in enumerate(groups) for i in g["program_indices"]}
    occupations=[claims(instance,p) for p in programs]
    coverage=[set(p["allocation_order"]) for p in programs]
    cross=[]
    for i in range(n):
        for j in range(i+1,n):
            if membership[i]!=membership[j] and (coverage[i]&coverage[j] or conflict(occupations[i],occupations[j])):
                pairs[(i,j)]+=penalty;cross.append([i,j])
    for group in groups:
        constant+=penalty
        for i in group["indices"]:linear[i]-=penalty
        for k,i in enumerate(group["indices"]):
            for j in group["indices"][k+1:]:pairs[tuple(sorted((i,j)))]+=2*penalty
    pairs={key:value for key,value in pairs.items() if value}
    bundle=dict(schema_version="catering-qubo.v1",bundle_id=instance["instance_id"]+"/"+state["scenario_id"]+f"/meal-block-{n}",
                case_id=instance["instance_id"]+"/"+state["scenario_id"],profile_id=PROFILE,scenario_id=state["scenario_id"],
                instance=instance,snapshot=state,instance_sha256=digest(instance),snapshot_sha256=digest(state),
                encoding="paired-course-anchor-onehot.v1",representation_id=f"paired-course-block-{n}",
                parent_sha256=parent_domain_sha256,parent_domain_kind="All generated local program IDs; not a complete QUBO hash",
                scope=("Complete generated local-program domain on this declared finite grid and policy" if complete_domain else
                       "Complete on the explicitly offered local program domain; restriction of the physical grid"),
                representation_kind="complete_declared_grid" if complete_domain else "offered_program_restriction",
                options=programs,variable_order=["option:"+p["id"] for p in programs]+["idle:"+g["anchor"] for g in groups],
                registers=[],onehot_groups=groups,conflicts=cross,
                constant=str(constant),linear=list(map(str,linear)),
                quadratic=[dict(i=i,j=j,value=str(v)) for (i,j),v in sorted(pairs.items())],
                objective=dict(constant=str(objective_constant),linear=list(map(str,objective_linear)),
                    quadratic=[dict(i=i,j=j,value=str(v)) for (i,j),v in sorted(objective_pairs.items())],
                    weights=weights,component_bounds=bounds),penalty=str(penalty),
                penalty_proof="P exceeds the total absolute nonconstant linear and quadratic objective coefficients",
                size=dict(binary_variables=total,option_bits=n,shortfall_bits=0,auxiliary_bits=len(groups),
                          idle_data_bits=len(groups),couplers=len(pairs),objective_couplers=len(objective_pairs)),
                disabled_features=["phase_aware_WIP","interrupted_cooking","ingredients","holding","power","money"],
                mixer=dict(kind="two-local-XY-rings",preserves="One choice per anchor block; cross-block physical conflicts remain penalized",
                           initial_state="Biased one-hot product states centered on the current quantum incumbent, no optimum teacher"))
    bundle["bundle_sha256"]=digest(bundle)
    return validate_bundle(bundle)


def sector_data(bundle,max_states=2_000_000):
    import numpy as np
    if bundle.get("encoding")!="paired-course-anchor-onehot.v1":raise ValueError("Meal block encoding required")
    groups=bundle["onehot_groups"];dims=tuple(len(g["indices"]) for g in groups)
    count=math.prod(dims)
    if count>max_states:raise ValueError(f"Declared one-hot sector has {count} states; exceeds local pilot limit")
    magnitude=abs(int(bundle["objective"]["constant"]))+sum(abs(int(c)) for c in bundle["objective"]["linear"])
    magnitude+=sum(abs(int(t["value"])) for t in bundle["objective"]["quadratic"])
    magnitude+=int(bundle["penalty"])*len(bundle["conflicts"])
    if magnitude>=2**63:raise ValueError("Sector energy exceeds the proven int64 arithmetic range")
    choices=np.indices(dims,dtype=np.int16).reshape(len(dims),-1).T if dims else np.zeros((1,0),dtype=np.int16)
    position={i:(g,j) for g,group in enumerate(groups) for j,i in enumerate(group["indices"])}
    chosen={i:choices[:,g]==j for i,(g,j) in position.items()}
    objective=np.full(count,int(bundle["objective"]["constant"]),dtype=np.int64)
    for i,c in enumerate(bundle["objective"]["linear"]):
        if int(c):objective+=int(c)*chosen[i]
    for t in bundle["objective"]["quadratic"]:objective+=int(t["value"])*(chosen[t["i"]]&chosen[t["j"]])
    violations=np.zeros(count,dtype=np.int32)
    for i,j in bundle["conflicts"]:violations+=(chosen[i]&chosen[j])
    energy=objective+int(bundle["penalty"])*violations
    return dict(dims=dims,choices=choices,objective=objective,violations=violations,energy=energy,
                valid=violations==0,states=count,position=position)


def sector_bits(bundle,sector,index):
    bits=[0]*bundle["size"]["binary_variables"]
    for g,choice in zip(bundle["onehot_groups"],sector["choices"][index]):bits[g["indices"][int(choice)]]=1
    return bits


def xy_mix(state,dims,beta):
    """Exact one-hot-sector simulation of sequential two-qubit XY ring gates."""
    import numpy as np
    output=np.array(state,dtype=complex,copy=True).reshape(dims)
    c,s=math.cos(beta),-1j*math.sin(beta)
    for axis,k in enumerate(dims):
        edges=[(j,j+1) for j in range(k-1)]+([(k-1,0)] if k>2 else [])
        for a,b in edges:
            u=[slice(None)]*len(dims);v=u.copy();u[axis]=a;v[axis]=b
            u,v=tuple(u),tuple(v);x,y=output[u].copy(),output[v].copy()
            output[u]=c*x+s*y;output[v]=s*x+c*y
    return output.reshape(-1)
