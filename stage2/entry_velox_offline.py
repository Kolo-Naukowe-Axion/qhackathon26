"""Prepare actual SDK-format manufacturing packets, strictly offline.

There is deliberately no submit/resume option or solver object. Credentials are
not requested, printed or used for authentication. The SDK's import-time token
environment lookup receives an explicitly empty process-local value.
The installed SDK private writer is pinned by the recorded version and audited
by independently reloading labels, offset, fields and couplings from HDF5.
"""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import random

import h5py
# Do not read or preserve an existing credential. This affects this process only;
# the parent shell and user's configuration are unchanged.
os.environ['VELOX_TOKEN']=''
from veloxq_sdk.api.problems import File

from .entry_campaign import packet
from .entry_core import entry_cases, recovery_cell
from .window_qubo import compile_qubo, digest


def prepare(output, references):
    output=Path(output)
    output.mkdir(parents=True,exist_ok=False)
    problems=entry_cases()
    for pumps in [2,4,8]:
        problems[f'scale-{pumps}-pumps']=recovery_cell(180+120*(pumps-1),pumps=pumps)
    rows=[]
    for name,problem in problems.items():
        directory=output/name
        directory.mkdir()
        q=compile_qubo(problem,max_variables=5000,support_pruning=True)
        p=packet(q)
        path=directory/'ising-input.h5'
        # All integer-QUBO Ising coefficients are quarters. The installed SDK
        # casts non-integral inputs to float32 even when that loses energy.
        # Scale the ENTIRE Hamiltonian by four and pass actual Python ints,
        # letting its supported integer dtype path preserve every coefficient.
        scale=4
        if any(int(scale*v)!=scale*v for v in [*p['biases'],p['offset'],*[v for i,j,v in p['couplings']]]):
            raise ValueError('Integer QUBO should have quarter-integral Ising coefficients')
        File._write_ising_hdf5(path,{i:int(scale*v)for i,v in enumerate(p['biases'])},
                              {(i,j):int(scale*v)for i,j,v in p['couplings']},offset=int(scale*p['offset']))
        with h5py.File(path,'r')as file:
            group=file['Ising']
            assert group.attrs['var_type']=='SPIN'
            labels=[int(x.decode()if isinstance(x,bytes)else x)for x in group['labels'][:]]
            assert labels==list(range(len(q.linear)))
            biases=group['biases'][:]
            offset=float(group.attrs['offset'])
            couplings=group['couplings']
            if isinstance(couplings,h5py.Group):
                # SDK stores explicit symmetric one-based coordinate triples,
                # despite the subgroup's SparseMatrixCSC attribute.
                terms=[(int(i)-1,int(j)-1,float(v))for i,j,v in zip(couplings['I'][:],couplings['J'][:],couplings['V'][:])if i<j]
            else:
                dense=couplings[:]
                terms=[(i,j,float(dense[i,j]))for i in range(len(labels))for j in range(i+1,len(labels))if dense[i,j]]
            assert len(terms)==len(q.quadratic)
            rng=random.Random(20261017)
            max_error=0
            for _ in range(64):
                bits=[rng.randrange(2)for _ in labels]
                spins=[2*b-1 for b in bits]
                energy=offset+sum(float(h)*s for h,s in zip(biases,spins))+sum(v*spins[i]*spins[j]for i,j,v in terms)
                max_error=max(max_error,abs(energy/scale-q.energy(bits)))
            if max_error>1e-6:
                raise AssertionError('Serialized SDK energy changed')
        reference_record=json.loads((Path(references)/name/'reference.json').read_text())
        if reference_record['problem_sha256']!=digest(problem):
            raise ValueError('Reference is from a different manufacturing model')
        reference=reference_record['reference']
        for filename,value in [('problem.json',problem),('offline-ising.json',p),('reference.json',reference),
                               ('qubo.json',dict(linear=q.linear,quadratic=[[i,j,v]for(i,j),v in q.quadratic.items()],offset=q.offset,variables=q.variables,groups=q.groups,metadata=q.metadata()))]:
            (directory/filename).write_text(json.dumps(value,indent=2)+'\n')
        rows.append(dict(case=name,variables=len(q.linear),couplers=len(q.quadratic),
                         problem_sha256=digest(problem),hdf5_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                         energy_roundtrip_states=64,max_roundtrip_error=max_error,
                         submitted_energy_scale=scale,result_energy_conversion='original_energy = serialized_energy / 4',
                         bias_dtype=str(biases.dtype),
                         reference_status=reference.get('status'),reference_objective=reference.get('objective'),
                         remote_calls=0,backend_access_verified=False))
    result=dict(schema='qfactoria-manufacturing-offline-sdk-packets.v1',rows=rows,
                sdk_version=importlib.metadata.version('veloxq-sdk'),veloxq_calls=0,
                credentials_used_for_requests=0,backend_access_verified=False,
                sdk_token_environment='Forced empty before SDK import; existing value not read',
                preparer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                convention='s=2*x-1; symmetric HDF couplings counted once (upper triangle) plus saved offset. Complete Hamiltonian scaled by 4 and stored as exact integers to avoid SDK float32 downcasting.',
                purpose='After separate authorization, compare same-model recovery decisions and larger QUBOs. No VeloxQ performance or award eligibility established by offline preparation.')
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    (output/'manifest.json').write_text(json.dumps({str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()
                                                   for p in output.rglob('*')if p.is_file()},indent=2)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    parser.add_argument('--references',required=True)
    args=parser.parse_args()
    print(json.dumps(prepare(args.output,args.references),indent=2))
