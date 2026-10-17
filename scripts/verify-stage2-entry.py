"""Independent retained-artifact/claim audit; no optimization or remote calls."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from stage2.window_qubo import compile_qubo,check_plan


def read(path):
    return json.loads(path.read_text())


def manifest(directory):
    files=read(directory/'manifest.json')
    for name,value in files.items():
        assert hashlib.sha256((directory/name).read_bytes()).hexdigest()==value,(directory,name)
    return len(files)


def audit():
    directory=ROOT/'output/stage2-entry-v2'
    report=read(directory/'report.json')
    files=manifest(directory)
    for name,value in report['protocol']['source_hashes'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==value,name
    view=read(ROOT/'presentation/entry/data.json')
    assert view['source_sha256']==hashlib.sha256((directory/'report.json').read_bytes()).hexdigest()
    assert not read(directory/'selection.json')['test_results_used']
    assert report['selection']==dict(layers=2,alpha=.25)
    totals={m:dict(runs=0,valid=0,schedule_optimal=0,encoded_optimal=0)for m in report['protocol']['methods']}
    checked=0
    for case,c in view['cases'].items():
        q=compile_qubo(read(directory/case/'problem.json'),support_pruning=True)
        ref=read(directory/case/'reference.json')
        assert ref['optimal']
        assert c['model']['pruned_variables']==len(q.linear)
        assert c['model']['pruned_couplers']==len(q.quadratic)
        for row in [r for r in report['rows']if r['case']==case]:
            actual=read(directory/case/f'test-{row["method"]}-{row["seed"]}.json')
            assert q.energy(actual['bits'])==row['energy']==actual['energy']
            decoded=q.decode(actual['bits'])
            assert decoded==actual['decoded']
            assert check_plan(q.problem,decoded['plan'])['valid']==row['valid']
            assert decoded['objective']==row['decoded_objective']
            assert sum(actual['observed_counts'].values())==actual['samples']
            choices=[next(j for j,i in enumerate(group)if actual['bits'][i])for group in q.groups.values()]
            index=0
            for choice,group in zip(choices,q.groups.values()):index=index*len(group)+choice
            assert actual['observed_counts'].get(str(index),0)>0,'Winner was not sampled'
            assert all(0<=int(i)<math.prod(len(g)for g in q.groups.values())and n>0 for i,n in actual['observed_counts'].items())
            assert row['encoded_energy_gap']==actual['energy']-ref['objective']
            assert row['decoded_objective_gap']==decoded['objective']-ref['objective']
            t=totals[row['method']]
            t['runs']+=1;t['valid']+=decoded['valid']
            t['schedule_optimal']+=row['decoded_objective_gap']==0
            t['encoded_optimal']+=row['encoded_energy_gap']==0
            checked+=1
        for m in c['methods']:
            rows=[r for r in report['rows']if r['case']==case and r['method']==m['method']]
            assert m['encoded_optimal']==sum(r['encoded_energy_gap']==0 for r in rows)
            assert m['schedule_optimal']==sum(r['decoded_objective_gap']==0 for r in rows)
        assert c['example']==read(directory/case/'test-qaoa_xy-101.json')['decoded']
    assert totals['qaoa_xy']==dict(runs=60,valid=60,schedule_optimal=60,encoded_optimal=57)
    assert totals['sa_onehot']==dict(runs=60,valid=60,schedule_optimal=60,encoded_optimal=60)
    assert totals['uniform_onehot']==dict(runs=60,valid=60,schedule_optimal=59,encoded_optimal=52)
    offline=ROOT/'output/stage2-entry-velox-offline-v4'
    files+=manifest(offline)
    packets=read(offline/'report.json')
    assert packets['veloxq_calls']==packets['credentials_used_for_requests']==0
    assert len(packets['rows'])==9
    assert all(r['max_roundtrip_error']==0 and r['submitted_energy_scale']==4 for r in packets['rows'])
    coefficients=read(ROOT/'output/stage2-entry-velox-coefficient-audit-v2.json')
    assert coefficients['status']=='passed'and len(coefficients['rows'])==9
    for row in coefficients['rows']:
        for filename,key in [('ising-input.h5','hdf5_sha256'),('qubo.json','qubo_sha256')]:
            assert hashlib.sha256((offline/row['case']/filename).read_bytes()).hexdigest()==row[key]
        assert row['all_energies_preserved_by_coefficient_equality']
    assert hashlib.sha256((ROOT/'stage2/entry_packet_audit.py').read_bytes()).hexdigest()==coefficients['auditor_sha256']
    audit=read(ROOT/'output/stage2-entry-circuit-audit-v1/report.json')
    assert audit['valid']
    for row in audit['rows']:
        source=directory/row['case']/'test-qaoa_xy-101.json'
        assert hashlib.sha256(source.read_bytes()).hexdigest()==row['source_sha256']
        assert hashlib.sha256(read(source)['qasm'].encode()).hexdigest()==row['qasm_sha256']
    return dict(status='passed',retained_runs_independently_redecoded=checked,
                hashed_files_checked=files,method_totals=totals,offline_sdk_packets=9,
                zero_error_serialized_energy_checks=9*64,physical_qpu_calls=0,veloxq_calls=0,
                exact_serialized_coefficient_checks=coefficients['exact_coefficient_checks'],
                scope='Retained evidence and display consistency audit; circuit probabilities and HDF energies rely on separately retained executed audits. Not a new performance sample.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    result=audit()
    if args.output:
        with args.output.open('x')as file:file.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
