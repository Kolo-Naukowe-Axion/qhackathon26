"""Independent integer-coefficient proof for saved SDK HDF5 packets.

Checks the literal files against an independent algebraic conversion, covering
all states through coefficient equality, beyond the 64 sampled-energy checks.
No solver, token or network client is constructed.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path

import h5py
import numpy as np


def audit(directory):
    directory=Path(directory)
    rows=[]
    for case in sorted(directory.iterdir()):
        if not(case/'ising-input.h5').exists():continue
        q=json.loads((case/'qubo.json').read_text())
        n=len(q['linear'])
        # 4*E((s+1)/2): fields=2*c_i+sum_j Q_ij,
        # couplers=Q_ij, constant=4*c0+2*sum c_i+sum Q_ij.
        fields=[2*int(v)for v in q['linear']]
        pairs={}
        constant=4*q['offset']+2*sum(q['linear'])
        for i,j,v in q['quadratic']:
            assert i<j
            fields[i]+=v;fields[j]+=v;pairs[i,j]=v;constant+=v
        with h5py.File(case/'ising-input.h5','r')as file:
            g=file['Ising']
            assert g.attrs['var_type']=='SPIN'
            assert int(g['L'][()])==n
            assert [int(x)for x in g['labels'][:]]==list(range(n))
            assert np.issubdtype(g['biases'].dtype,np.integer)
            assert [int(x)for x in g['biases'][:]]==fields
            assert g.attrs['offset']==constant
            c=g['couplings']
            if isinstance(c,h5py.Group):
                assert list(c['dims'][:])==[n,n]
                assert np.issubdtype(c['V'].dtype,np.integer)
                actual={(int(i)-1,int(j)-1):int(v)for i,j,v in zip(c['I'][:],c['J'][:],c['V'][:])}
            else:
                assert np.issubdtype(c.dtype,np.integer)
                dense=c[:]
                actual={(i,j):int(dense[i,j])for i in range(n)for j in range(n)if dense[i,j]}
            expected=dict(pairs)
            expected.update({(j,i):v for(i,j),v in pairs.items()})
            assert actual==expected
        rows.append(dict(case=case.name,variables=n,couplers=len(pairs),
                         exact_coefficient_checks=n+2*len(pairs)+1,
                         hdf5_sha256=hashlib.sha256((case/'ising-input.h5').read_bytes()).hexdigest(),
                         qubo_sha256=hashlib.sha256((case/'qubo.json').read_bytes()).hexdigest(),
                         all_energies_preserved_by_coefficient_equality=True))
    assert len(rows)==9
    return dict(schema='qfactoria-offline-all-state-coefficient-audit.v1',status='passed',rows=rows,
                exact_coefficient_checks=sum(r['exact_coefficient_checks']for r in rows),
                auditor_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                h5py=importlib.metadata.version('h5py'),physical_qpu_calls=0,veloxq_calls=0,
                scope='Exact local serialized Hamiltonian equals four times the original QUBO under s=2x-1 for every state. Platform acceptance/internal precision unverified.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packets',required=True)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    result=audit(args.packets)
    with args.output.open('x')as file:file.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='rows'},indent=2))
