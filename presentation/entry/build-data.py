"""Derive the jury view only from the frozen local entry campaign."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'output/stage2-entry-v2'
report=json.loads((source/'report.json').read_text())
audit=json.loads((ROOT/'output/stage2-entry-circuit-audit-v1/report.json').read_text())
cases={}
for name in dict.fromkeys(r['case']for r in report['rows']):
    case=json.loads((source/name/'results.json').read_text())
    example=json.loads((source/name/'test-qaoa_xy-101.json').read_text())
    reference=json.loads((source/name/'reference.json').read_text())
    cases[name]=dict(model=case['model'],example=example['decoded'],reference=reference,
                     seed=101,case=name,optimization=example['optimization'],
                     problem=json.loads((source/name/'problem.json').read_text()),methods=[])
    for method in report['protocol']['methods']:
        rows=[r for r in case['rows']if r['method']==method]
        cases[name]['methods'].append(dict(method=method,runs=len(rows),
                    valid=sum(r['valid']for r in rows),
                    encoded_optimal=sum(r['encoded_energy_gap']==0 for r in rows),
                    schedule_optimal=sum(r['decoded_objective_gap']==0 for r in rows),
                    mean_encoded_gap=sum(r['encoded_energy_gap']for r in rows)/len(rows),
                    mean_seconds=sum(r['wall_seconds']for r in rows)/len(rows)))
result=dict(schema='qfactoria-entry-presentation.v1',cases=cases,scaling=report['scaling'],audit=audit,
            protocol=report['protocol'],source='output/stage2-entry-v2/report.json',
            source_sha256=hashlib.sha256((source/'report.json').read_bytes()).hexdigest(),
            campaign_wall_seconds=report['wall_seconds'],campaign_cpu_seconds=report['process_cpu_seconds'],
            physical_qpu_calls=0,veloxq_calls=0)
(Path(__file__).parent/'data.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(cases=len(cases),source_sha256=result['source_sha256'])))
