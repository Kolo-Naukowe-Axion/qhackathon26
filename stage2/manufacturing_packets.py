"""Serialize retained manufacturing models with pinned SDK writer; no submit API."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import h5py
import numpy as np
import dimod
os.environ['VELOX_TOKEN']=''  # process-local, before SDK import; do not read old value
from veloxq_sdk.api.problems import File
from .manufacturing_io import load

ROOT=Path(__file__).resolve().parents[1]
TASKS={
 'nominal-32-complete':'manufacturing-study-v1/nominal-32/full-domain',
 'rush-outage-32-complete':'manufacturing-study-v1/rush-and-outage-32/full-domain',
 'heat-outage-32-complete':'manufacturing-full-recovery-v1/heat-outage-32',
 'heat-replacement-32-complete':'manufacturing-full-recovery-v1/heat-lease-32',
 'nominal-64-restricted':'manufacturing-study-v1/nominal-64',
 'nominal-128-restricted':'manufacturing-study-v1/nominal-128'}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def audit(path,q,witness,fields,edges,offset,warm):
    with h5py.File(path,'r')as f:
        g=f['Ising'];labels=[int(v.decode()if isinstance(v,bytes)else v)for v in g['labels'][:]]
        assert labels==list(range(len(q.linear)))and g.attrs['var_type']=='SPIN'
        actual=[int(v)for v in g['biases'][:]]
        assert actual==fields and int(g.attrs['offset'])==offset and float(offset)==g.attrs['offset']
        c=g['couplings'];found={}
        if isinstance(c,h5py.Group):
            directed={(int(i)-1,int(j)-1):int(v)for i,j,v in zip(c['I'][:],c['J'][:],c['V'][:])}
            assert all(directed.get((j,i))==v for(i,j),v in directed.items())
            found={ij:v for ij,v in directed.items()if ij[0]<ij[1]}
        else:
            a=c[:];assert np.array_equal(a,a.T)
            found={(i,j):int(a[i,j])for i,j in zip(*np.triu(a,1).nonzero())}
        assert found==edges
        spins=[2*x-1 for x in witness['bits']]
        energy=offset+sum(h*s for h,s in zip(actual,spins))+sum(v*spins[i]*spins[j]for(i,j),v in found.items())
        assert energy==4*witness['energy']
        if warm:
            s=f['Spectrum'];assert int(s['num_rep'][()])==8
            assert np.array_equal(s['states'][:],np.tile(spins,(8,1)))
            assert np.all(s['energies'][:]==4*witness['energy'])
        else:assert 'Spectrum'not in f
        return dict(coefficients_checked=len(actual)+len(found)+1,coefficient_equality_all_states=True,
                    witness_energy_exact=True,bias_dtype=str(g['biases'].dtype),warm_replicas=8 if warm else 0)
def prepare(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False);rows=[]
    for name,relative in TASKS.items():
        source=ROOT/'output'/relative;q,raw,w=load(source)
        fields=[2*int(v)for v in q.linear];edges={ij:int(v)for ij,v in q.quadratic.items()}
        for(i,j),v in edges.items():fields[i]+=v;fields[j]+=v
        offset=4*q.offset+2*sum(q.linear)+sum(edges.values())
        folder=output/name;folder.mkdir();files=[]
        spins=np.tile([2*b-1 for b in w['bits']],(8,1))
        initial=dimod.SampleSet.from_samples((spins,list(range(len(fields)))),dimod.SPIN,energy=[4*w['energy']]*8,sort_labels=False)
        for warm in [False,True]:
            path=folder/('witness-initialized.h5'if warm else 'cold.h5')
            File._write_ising_hdf5(path,dict(enumerate(fields)),edges,offset=int(offset),init_state=initial if warm else None)
            checked=audit(path,q,w,fields,edges,offset,warm)
            files.append(dict(file=str(path.relative_to(output)),bytes=path.stat().st_size,sha256=sha(path),audit=checked))
        coeff=[abs(v)for v in [*fields,*edges.values()]if v]
        row=dict(case=name,source=str(source.relative_to(ROOT)),input_sha256={p.name:sha(p)for p in [source/'qubo.json',source/'witness.json']},
                 variables=len(fields),couplers=len(edges),density=2*len(edges)/len(fields)/(len(fields)-1),
                 min_nonzero_coefficient=min(coeff),max_abs_coefficient=max(coeff),dynamic_range=max(coeff)/min(coeff),
                 witness_objective=w['energy'],witness_source='Saved feasible list heuristic, generated before native CP; eight identical disclosed replicas',
                 penalty_certificate=raw['metadata']['penalty_certificate'],files=files,backend_acceptance_verified=False)
        (folder/'receipt.json').write_text(json.dumps(row,indent=2)+'\n');rows.append(row)
        print(json.dumps(dict(case=name,variables=len(fields),couplers=len(edges))),flush=True)
    result=dict(schema='qfactoria-complete-recipe-offline-packets.v1',rows=rows,sdk_version=importlib.metadata.version('veloxq-sdk'),
                preparer_sha256=sha(Path(__file__)),veloxq_calls=0,physical_qpu_calls=0,credentials_used_for_requests=0,
                sdk_token_environment='Forced empty before SDK import; original value not read',
                mapping='s=2x-1; entire Ising Hamiltonian multiplied by4, Python integer coefficients; returned energy /4 includes offset',
                limits='SDK writer layout verified offline. Service acceptance, quotas, internal precision, recommended initialization and performance are unverified. No solver object constructed.')
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    (output/'manifest.json').write_text(json.dumps({str(p.relative_to(output)):sha(p)for p in output.rglob('*')if p.is_file()},indent=2)+'\n')
    return result
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True);a=parser.parse_args();r=prepare(a.output);print(json.dumps(dict(packets=len(r['rows']),veloxq_calls=0)))
