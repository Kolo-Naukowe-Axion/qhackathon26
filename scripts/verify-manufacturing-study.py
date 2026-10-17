"""Recheck retained manufacturing plans/packets, no solver or SDK imports."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import h5py
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from stage2.window_qubo import check_plan
from stage2.manufacturing_io import load

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
    files=0;plans=0;coefficients=0;samples=0
    for name in ['manufacturing-study-v1','manufacturing-recovery-v2','manufacturing-full-recovery-v1','manufacturing-packets-v1']:
        folder=ROOT/'output'/name
        for rel,h in json.loads((folder/'manifest.json').read_text()).items():assert sha(folder/rel)==h,(name,rel);files+=1
    for name in ['manufacturing-study-v1','manufacturing-recovery-v2']:
        folder=ROOT/'output'/name
        for row in json.loads((folder/'report.json').read_text())['rows']:
            p=json.loads((folder/row['case']/'problem.json').read_text())
            for key in ['initial','raw_reference','pool_reference']:
                s=row.get(key,{})
                if s.get('plan'):
                    checked=check_plan(p,s['plan']);assert checked['valid']and checked['objective']==s['objective'];plans+=1
    packets=ROOT/'output/manufacturing-packets-v1';r=json.loads((packets/'report.json').read_text())
    for row in r['rows']:
        source=ROOT/row['source'];q,raw,w=load(source)
        for name,h in row['input_sha256'].items():assert sha(source/name)==h
        assert check_plan(q.problem,w['plan'])['valid'];plans+=1
        for entry in row['files']:
            path=packets/entry['file'];assert sha(path)==entry['sha256']
            with h5py.File(path,'r')as f:
                g=f['Ising'];assert int(g['L'][()])==len(q.linear)
                assert [int(v)for v in g['labels'][:]]==list(range(len(q.linear)))
                assert np.issubdtype(g['biases'].dtype,np.integer)
                fields=[int(v)for v in g['biases'][:]];coupling=g['couplings']
                if isinstance(coupling,h5py.Group):
                    assert np.issubdtype(coupling['V'].dtype,np.integer)
                    terms={(int(i)-1,int(j)-1):int(v)for i,j,v in zip(coupling['I'][:],coupling['J'][:],coupling['V'][:])}
                else:
                    assert np.issubdtype(coupling.dtype,np.integer);a=coupling[:];terms={(int(i),int(j)):int(a[i,j])for i,j in zip(*a.nonzero())}
                assert all(i!=j and terms.get((j,i))==v for(i,j),v in terms.items())
                edges={ij:v for ij,v in terms.items()if ij[0]<ij[1]}
                # Inverse algebra: substitute s=2x-1 into the literal HDF.
                # Compare resulting binary coefficients to 4*Q, independently
                # of the preparer's forward conversion and decoded witness.
                binary_linear=[2*h for h in fields]
                for(i,j),v in edges.items():binary_linear[i]-=2*v;binary_linear[j]-=2*v
                assert binary_linear==[4*v for v in q.linear]
                assert {ij:4*v for ij,v in edges.items()}=={ij:4*v for ij,v in q.quadratic.items()}
                assert g.attrs['offset']-sum(fields)+sum(edges.values())==4*q.offset
                coefficients+=len(fields)+len(terms)+1
                if entry['audit']['warm_replicas']:
                    spectrum=f['Spectrum'];spins=np.tile([2*b-1 for b in w['bits']],(8,1))
                    assert np.array_equal(spectrum['states'][:],spins)
                    assert np.all(spectrum['energies'][:]==4*q.energy(w['bits']))
    pilot=ROOT/'output/manufacturing-anneal-pilot-v1'
    report=json.loads((pilot/'report.json').read_text())
    for row in report['rows']:
        name=row['task'].replace('/','-')+f"-{row['penalty']}-{row['initialization']}-{row['seed']}.json"
        record=json.loads((pilot/name).read_text());q,raw,w=load(ROOT/'output/manufacturing-study-v1'/row['task'])
        valid=0
        for s in record['records']:
            checked=q.decode(s['bits']);assert checked['valid']==s['decoded']['valid'];samples+=s['count']
            if checked['valid']:valid+=s['count'];assert checked['objective']==s['decoded']['objective']
        assert valid==row['feasible_samples']
    return dict(status='passed',manifest_files=files,checked_plans=plans,exact_coefficient_checks=coefficients,annealing_samples_rechecked=samples,
                sdk_imported=False,solver_executions=0,veloxq_calls=0,auditor_sha256=sha(Path(__file__)))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=verify()
    with a.output.open('x')as f:f.write(json.dumps(r,indent=2)+'\n')
    print(json.dumps(r))
