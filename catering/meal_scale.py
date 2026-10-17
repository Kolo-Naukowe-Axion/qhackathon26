"""Offline larger VeloxQ-track inputs for the same paired-meal decision.

Build/validate only. No service SDK, credentials, uploads, retries or calls.
Large widths are QUBO variables including idle, not quantum circuit targets.
"""
import argparse
import math
import time
from pathlib import Path

from .build_meal_release import save, seal
from .contracts import load_bundle
from .decode import decode
from .domain import digest, snapshot
from .meal_blocks import meal_fixture, compile_meal_blocks, stratified_pool
from .meal_reference import solve_bundle
from .native_slots import solve_native
from .options import enumerate_options
from .qubo import energy


def build(output, customers=12, scenario='S3', widths=(512,1024,2048), seconds=5, max_couplers=2_000_000):
    widths=tuple(widths)
    if not widths or tuple(sorted(set(widths)))!=widths or any(w<1 for w in widths):
        raise ValueError('Unique increasing positive widths required')
    if customers<1 or scenario not in ('S0','S1','S2','S3') or not math.isfinite(seconds) or seconds<=0 or max_couplers<1:
        raise ValueError('Positive workload, finite reference budget and coupler guard required')
    output=Path(output)
    if output.exists():raise ValueError('Fresh output directory required')
    output.mkdir(parents=True)
    save(output/'experiment-plan.json',dict(customers=customers,scenario=scenario,widths=list(widths),
         reference_seconds_per_case=seconds,max_couplers=max_couplers,
         purpose='Larger same-model workload for the VeloxQ owner; offline preparation only',
         selection='Nested deterministic allocation/cooker/time strata, one retained seed per anchor; no optimal-plan teacher',
         physical_qpu_calls=0,veloxq_calls=0))
    instance=meal_fixture(customers);state=snapshot(instance,scenario)
    save(output/'instance.json',instance);save(output/'snapshot.json',state)
    before=time.monotonic();programs=enumerate_options(instance,state);generation_s=time.monotonic()-before
    parent=digest([p['id'] for p in programs])
    anchors={}
    for p in programs:anchors.setdefault(min(p['allocation_order']),p)
    chosen={p['id']:p for p in anchors.values()}
    donors=stratified_pool(programs,min(len(programs),max(widths)))
    rows=[]
    raw=solve_native(instance,state,dict(wall_time_limit_s=seconds),dict(workers=1,seed=2026))
    save(output/'raw-reference.json',raw)
    for width in widths:
        target=width-len(anchors)
        if target<len(chosen) or target>len(programs):raise ValueError('Requested width cannot contain every anchor or exceeds this domain')
        for p in donors:
            if len(chosen)>=target:break
            chosen[p['id']]=p
        before=time.monotonic()
        bundle=compile_meal_blocks(instance,state,sorted(chosen.values(),key=lambda p:p['id']),
                                   parent_domain_sha256=parent,tight_bounds=True)
        build_s=time.monotonic()-before
        if bundle['size']['binary_variables']!=width:raise AssertionError('Unexpected actual width')
        if bundle['size']['couplers']>max_couplers:raise ValueError('Coupler guard reached; keep earlier tiers and reduce width')
        file=output/f'scale-{width}-qubo.json';save(file,bundle);load_bundle(file)
        witness=[0]*width
        for g in bundle['onehot_groups']:witness[g['idle_index']]=1
        checked=decode(bundle,witness)
        if not checked['valid']:raise AssertionError('Invalid all-idle witness')
        save(output/f'scale-{width}-witness.json',dict(kind='Known idle witness, not a solver result',bits=witness,decoded=checked))
        ref=solve_bundle(bundle,seconds=seconds,seed=2026)
        save(output/f'scale-{width}-reference.json',ref)
        values=[abs(int(v)) for v in bundle['linear'] if int(v)]+[abs(int(t['value'])) for t in bundle['quadratic']]
        absolute_bound=abs(int(bundle['constant']))+sum(values)
        row=dict(width=width,size=bundle['size'],bundle_sha256=bundle['bundle_sha256'],
                 density=2*bundle['size']['couplers']/(width*(width-1)),build_s=build_s,file_bytes=file.stat().st_size,
                 largest_coefficient=str(max(values)),smallest_nonzero_coefficient=str(min(values)),
                 coefficient_dynamic_range=max(values)/min(values),absolute_energy_bound=str(absolute_bound),
                 all_integer_energies_within_float64_exact_range=absolute_bound<=2**53,
                 encoded_reference_status=ref['reference']['status'],
                 encoded_reference_metrics=(ref.get('check') or {}).get('metrics'),
                 encoded_reference_bound=ref['reference']['bound'],encoded_reference_timings=ref['timings'])
        rows.append(row);print(row,flush=True)
    report=dict(profile_id=instance['profile_id'],customers=customers,scenario=scenario,full_local_program_count=len(programs),
                anchor_count=len(anchors),full_local_domain_sha256=parent,generation_s=generation_s,rows=rows,
                raw_reference_status=raw['reference_status'],raw_reference_metrics=(raw.get('check') or {}).get('metrics'),
                physical_qpu_calls=0,veloxq_calls=0,
                limitations=['Nested lossy program restrictions, not full generated QUBOs',
                    'Larger variable count or reference timeout does not demonstrate hardness or a speedup',
                    'Exact integer re-scoring is required; floating-point backend precision must be checked by its owner',
                    'Tighter proven feasible bounds preserve lexicographic order; compare raw tuples across bundles, not energy'])
    save(output/'report.json',report);seal(output);return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--customers',type=int,default=12)
    p.add_argument('--scenario',choices=['S0','S1','S2','S3'],default='S3')
    p.add_argument('--widths',type=int,nargs='+',default=[512,1024,2048])
    p.add_argument('--reference-seconds',type=float,default=5);p.add_argument('--max-couplers',type=int,default=2_000_000)
    a=p.parse_args();build(a.output,a.customers,a.scenario,a.widths,a.reference_seconds,a.max_couplers)
