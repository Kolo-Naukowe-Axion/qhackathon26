"""Add actual browser/fresh-run provenance to the independent document seal."""
from pathlib import Path
import hashlib
import json
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from stage2.column_qubo import compile_columns
from stage2.window_qubo import check_plan
def read(p): return json.loads((ROOT / p).read_text())
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
prior = 'output/merit-document-consistency-v1/report.json'
result = read(prior)
for p,h in result['source_hashes'].items(): assert sha(p) == h, p
qa_path = 'output/manufacturing-merit-qa-v1/report.json'
qa = read(qa_path)
assert qa['status'] == 'passed' and all(row['passed'] for row in qa['checks'])
for p,h in qa['source_hashes'].items(): assert sha(p) == h, p
for p,h in qa['screenshots'].items(): assert sha('output/manufacturing-merit-qa-v1/' + p) == h
live = qa['checks'][0]['artifact']
for p,h in read(live + '/manifest.json').items(): assert sha(live + '/' + p) == h
record = read(live + '/result.json')
p = read(live + '/problem.json')
q = compile_columns(p, read(live + '/columns.json'))
sample = record['result']
assert sample['logical_qubits'] == len(q.linear) == 28
assert q.energy(sample['bits']) == sample['energy']
assert q.decode(sample['bits']) == sample['decoded']
checked = check_plan(p, sample['decoded']['plan'])
assert checked['valid'] and checked['weighted_terminal_tardiness'] == 0 and checked['makespan'] == 855
assert record['physical_qpu_calls'] == record['veloxq_calls'] == 0
result['checks'].append(dict(name='actual_browser_fresh_pipeline', passed=True,
    proof=dict(artifact=live, logical_qubits=28, check=checked, manifest_verified=True,
               scope='Actual local fresh action; independent retained energy/whole-plan readback, not a new sample or quantum advantage')))
result['checks'].append(dict(name='browser_qa_receipt', passed=True,
    proof=dict(receipt=qa_path, source_hashes_verified=len(qa['source_hashes']), checks=len(qa['checks']), screenshots=len(qa['screenshots']))))
result['source_hashes'].update({prior:sha(prior),qa_path:sha(qa_path), live+'/result.json':sha(live+'/result.json'),live+'/manifest.json':sha(live+'/manifest.json')})
result['prior_auditor_sha256'] = result['auditor_sha256']
result['auditor_sha256'] = sha(Path(__file__))
with (Path(__file__).parent / 'report.json').open('x') as f: f.write(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(status='passed',checks=len(result['checks']),files=len(result['source_hashes']))))
