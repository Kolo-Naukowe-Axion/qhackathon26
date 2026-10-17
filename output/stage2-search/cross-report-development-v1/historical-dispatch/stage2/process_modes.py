"""Explicit careful welding/assembly choices over frozen physical simulation.

Only ordinary standard-mode S/ASSEMBLY requests are replaced. Repair requests,
explicit other modes, certified QA, physical tables and quality tapes stay under
unchanged engine semantics. The default is exact standard-policy behavior.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import time

from .check import check_trace, check_paired_causality
from .kitting import AdmissionKitToolingSpecialistFactory
from .spec import build

ROOT = Path(__file__).resolve().parents[1]
VARIANTS = dict(neither={}, welding={'S':'careful'}, assembly={'ASSEMBLY':'careful'},
                both={'S':'careful','ASSEMBLY':'careful'})
CONTEXTS = [(12,8,4),(16,4,0),(24,4,4)]


def source_hashes():
    names = ('process_modes.py','kitting.py','admission.py','tooling.py','specialist.py',
             'advanced.py','engine.py','spec.py','check.py','dispatch.py')
    return {f'stage2/{name}':hashlib.sha256((ROOT/'stage2'/name).read_bytes()).hexdigest() for name in names}


class ProcessModesMixin:
    def __init__(self,*args,process_modes=None,**kwargs):
        super().__init__(*args,**kwargs)
        self.process_modes = dict(S='standard',ASSEMBLY='standard')
        supplied = deepcopy(process_modes or {})
        if set(supplied)-set(self.process_modes):
            raise ValueError('Only S and ASSEMBLY process-mode overrides are supported')
        if any(mode not in ('standard','careful') for mode in supplied.values()):
            raise ValueError('Process-mode override must be standard or careful')
        self.process_modes.update(supplied)
        self._repair_mode_context = False
        self.trace['provenance']['process_modes'] = deepcopy(self.process_modes)

    def effective_mode(self,process,mode,repair=False):
        if not repair and mode == 'standard':
            return self.process_modes.get(process,mode)
        return mode

    def selected_mode(self,process,order_id):
        return self.effective_mode(process,super().selected_mode(process,order_id),self._repair_mode_context)

    def remaining_processing(self,part):
        previous = self._repair_mode_context
        self._repair_mode_context = bool(part.get('rework'))
        try:
            return super().remaining_processing(part)
        finally:
            self._repair_mode_context = previous

    def estimated_machine_finish(self,part,machine):
        previous = self._repair_mode_context
        self._repair_mode_context = bool(part.get('rework'))
        try:
            return super().estimated_machine_finish(part,machine)
        finally:
            self._repair_mode_context = previous

    def process(self,m,parts,mode='standard',parents=None,kind='process',preview=False,prepare_only=False):
        # The same outermost replacement runs before tool preparation, duration,
        # worker attendance, power, quality preview and actual commitment.
        repair = any(part.get('rework') for part in parts)
        mode = self.effective_mode(m['process'],mode,repair=repair or kind!='process')
        return super().process(m,parts,mode,parents,kind,preview,prepare_only)

    def finish(self):
        super().finish()
        self.trace.setdefault('algorithm_audit',{})['process_modes'] = dict(
            selected=deepcopy(self.process_modes),
            committed=dict(Counter(f"{op['process']}:{op['mode']}" for op in self.trace['operations'] if op['kind']=='process')),
            scope='Algorithm mode choices only; original processing duration, power, wear, quality and certification')


class ProcessModesFactory(ProcessModesMixin,AdmissionKitToolingSpecialistFactory):
    pass


def run(instance,weights=None,controller=None,*,process_modes=None,tool_policy=None,kit_reservation=True):
    return ProcessModesFactory(instance,weights,controller,process_modes=process_modes,
        tool_policy=tool_policy or dict(mode='hard'),kit_reservation=kit_reservation).run()


def _group(task):
    orders,wip,guard,seeds,weights,output = task
    folder = Path(output)
    rows, causal = [], []
    for variant,modes in VARIANTS.items():
        traces = []
        for seed in seeds:
            started = time.perf_counter()
            trace = run(build(orders=orders,seed=seed),weights,process_modes=modes)
            checked = check_trace(trace)
            path = folder/f'n{orders}-s{seed}-{variant}.json.gz'
            path.write_bytes(gzip.compress(json.dumps(trace,separators=(',',':')).encode(),mtime=0))
            production = [op for op in trace['operations'] if op['kind']=='process']
            row = dict(orders=orders,wip=wip,guard=guard,seed=seed,variant=variant,
                process_modes=modes,weights=weights,valid=checked['valid'],issues=checked['issues'],
                terminal=checked['terminal_requirements_met'],metrics=trace['metrics'],
                wall_seconds=time.perf_counter()-started,trace=str(path),
                trace_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                qa_failures=sum(event['type']=='qa_result' and not event['passed'] for event in trace['events']),
                repair_events=sum(event['type']=='repair' for event in trace['events']),
                scrap_events=sum(event['type']=='scrap' for event in trace['events']),
                replacement_events=sum(event['type']=='replacement' for event in trace['events']),
                careful_operations=sum(op['mode']=='careful' for op in production),
                process_ticks={proc:sum(op['processing_ticks'] for op in production if op['process']==proc) for proc in ('S','ASSEMBLY')},
                mode_counts=dict(Counter(f"{op['process']}:{op['mode']}" for op in production)))
            rows.append(row);traces.append(trace)
        causal.append(dict(variant=variant,verification=check_paired_causality(traces)))
    return dict(orders=orders,rows=rows,causality=causal)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--teacher',type=Path,default=ROOT/'output/stage2-search/routing-coefficients-training/training-teacher.json')
    parser.add_argument('--seeds',type=int,nargs='+',default=list(range(8)))
    parser.add_argument('--workers',type=int,default=2)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args(argv)
    if any(seed>=10000 or seed<0 for seed in args.seeds):
        raise ValueError('Only nonnegative development tapes below10000 are allowed')
    if args.workers not in (1,2):raise ValueError('This bounded screen permits at most two local workers')
    args.output.mkdir(parents=True,exist_ok=True)
    before = source_hashes()
    for name in before:(args.output/Path(name).name).write_bytes((ROOT/name).read_bytes())
    teacher = json.loads(args.teacher.read_text())
    tasks = []
    for orders,wip,guard in CONTEXTS:
        index = next(index for index,context in enumerate(teacher['configs']) if context['orders']==orders)
        action = teacher['policy']['actions'][index]
        weights = dict(teacher['actions'][action]['weights'],wip_limit=wip,qa_guard_threshold=guard,
                       worker_calendar=True,preposition=False,admission_rule='family')
        tasks.append((orders,wip,guard,args.seeds,weights,str(args.output)))
    started = time.perf_counter()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:groups=list(pool.map(_group,tasks))
    after = source_hashes()
    report = dict(schema='metaltech-careful-mode-screen.v1',scope='TRAIN development screen; all runs retained; no final tapes',
        variants=VARIANTS,groups=groups,source_before=before,source_after=after,source_stable=before==after,
        teacher=dict(path=str(args.teacher.resolve()),sha256=hashlib.sha256(args.teacher.read_bytes()).hexdigest()),
        wall_seconds=time.perf_counter()-started)
    report['valid'] = before==after and all(row['valid'] and row['terminal'] for group in groups for row in group['rows']) and all(
        item['verification']['valid'] for group in groups for item in group['causality'])
    (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(valid=report['valid'],runs=sum(len(group['rows']) for group in groups),wall_seconds=report['wall_seconds'])))
    return 0 if report['valid'] else 1


if __name__=='__main__':raise SystemExit(main())
