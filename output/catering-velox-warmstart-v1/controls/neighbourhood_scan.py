import sys,json,itertools,time
import numpy as np
sys.path.insert(0,'.')
from catering.contracts import load_bundle
from catering.conditioning import eliminate_idle, lift_bits
from catering.veloxq_pilot import incumbent_start
from catering.decode import decode
from catering.qubo import energy
w=int(sys.argv[1]);k=int(sys.argv[2])
src=load_bundle(f'output/catering-velox-scale-v3/scale-{w}-qubo.json');v=eliminate_idle(src)
x0l,info=incumbent_start(src,v,sys.argv[3] if len(sys.argv)>3 else f'output/catering-classical-scale-v3/scale-{w}-reference.json')
n=len(v['linear']);lin=np.array([int(c) for c in v['linear']],dtype=np.float64)
Q=np.zeros((n,n))
for t in v['quadratic']:Q[t['i'],t['j']]+=int(t['value'])
Qs=Q+Q.T;x0=np.array(x0l,dtype=np.float64);E0=energy(v,x0l);C=int(v['constant'])
blocks=[g['program_indices'] for g in src['onehot_groups']]
def scan(bl):
    F=[i for b in bl for i in b];m=len(F)
    rest=x0.copy();rest[F]=0
    h=lin[F]+Qs[np.ix_(F,range(n))]@rest;QFF=Q[np.ix_(F,F)]
    base=C+lin@rest+rest@Q@rest
    offs=np.cumsum([0]+[len(b) for b in bl])
    grids=np.meshgrid(*[np.arange(len(b)+1) for b in bl],indexing='ij')
    Y=np.zeros((grids[0].size,m))
    for t,g in enumerate(grids):
        g=g.ravel();sel=g>0
        Y[np.nonzero(sel)[0],offs[t]+g[sel]-1]=1
    e=base+Y@h+np.einsum('ij,ij->i',Y@QFF,Y)
    j=int(np.argmin(e));return e[j],Y[j],F
t0=time.time();best=None;cnt=0
for combo in itertools.combinations(range(len(blocks)),k):
    e,y,F=scan([blocks[c] for c in combo])
    if e<E0-0.5:
        print('  ',combo,len(F),E0-e)
        cnt+=1
        if best is None or e<best[0]:best=(e,combo,len(F),y,F)
print(w,k,'improving',cnt,'time',round(time.time()-t0))
if best:
    e,combo,m,y,F=best;x=x0.copy();x[F]=y
    full=lift_bits(src,v,[int(a) for a in x]);d=decode(src,full)
    print(' best gain',E0-e,'blocks',combo,'vars',m,'valid',d['valid'],d['check']['metrics'],'from',info['metrics'])
