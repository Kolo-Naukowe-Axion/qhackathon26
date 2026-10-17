"""Complete-domain recovery QUBOs; preserved reference plans are NOT teachers."""
import argparse
import hashlib
import json
from pathlib import Path
from .window_qubo import compile_qubo,check_plan
from .manufacturing_study import export,save


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--study',required=True,type=Path);parser.add_argument('--output',required=True,type=Path);args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False);rows=[]
    for name in ['heat-outage-32','heat-lease-32']:
        source=args.study/name;p=json.loads((source/'problem.json').read_text());parents=json.loads((source/'parents.json').read_text())['parents']
        witness=min(parents,key=lambda plan:check_plan(p,plan)['objective'])
        directory=args.output/name;directory.mkdir();save(directory/'problem.json',p)
        q=compile_qubo(p,max_variables=12000,support_pruning=True)
        metadata=export(q,directory,witness,'Complete declared grid30 operation domain with exact support pruning; no candidate cap')
        prior=json.loads((source/'report.json').read_text())
        row=dict(case=name,model=metadata,raw_reference=prior['raw_reference'],reference_used_for_compilation=False,
                 source_report_sha256=hashlib.sha256((source/'report.json').read_bytes()).hexdigest())
        save(directory/'report.json',row);rows.append(row)
        print(json.dumps(dict(case=name,bits=metadata['variables'],couplers=metadata['couplers'],penalty_factor=metadata['penalty_certificate']['ratio'])),flush=True)
    root=Path(__file__).resolve().parents[1]
    sources={n:hashlib.sha256((root/n).read_bytes()).hexdigest()for n in ['stage2/manufacturing_full.py','stage2/manufacturing_study.py','stage2/manufacturing_penalty.py','stage2/window_qubo.py','stage2/window_reduction.py']}
    save(args.output/'report.json',dict(rows=rows,source_hashes=sources,veloxq_calls=0,physical_qpu_calls=0))
    save(args.output/'manifest.json',{str(p.relative_to(args.output)):hashlib.sha256(p.read_bytes()).hexdigest()for p in args.output.rglob('*')if p.is_file()})
