import hashlib,json,os,platform,resource,sys,time
from pathlib import Path
import numpy as np
from stage2.qubo import build_qubo
from stage2.quantum_scaling import Budget,Kernel
n=int(sys.argv[1]);out=Path(sys.argv[2]);start=time.perf_counter()
q=build_qubo([dict(id=str(i),reward=1+(i*7)%19,resources={}) for i in range(n)],[(str(i),str((i+1)%n)) for i in range(n)])
k=Kernel(q,Budget(max_bits=24,memory_mib=1536,seconds=120,evaluations=3))
rows=[]
for p in (1,2):
 t=time.perf_counter();v=k.evolve([.37]*p,[-.25]*p);rows.append(dict(layers=p,seconds=time.perf_counter()-t,norm=float(np.vdot(v,v).real)));del v
peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
out.write_text(json.dumps(dict(total_bits=n,core_bits=n,slack_bits=0,qubo=q.summary(),preprocessing_seconds=k.preprocessing_seconds,evolutions=rows,estimated_bytes=k.estimated_bytes,peak_process_rss_bytes=peak if sys.platform=='darwin' else peak*1024,total_seconds=time.perf_counter()-start,runtime=dict(python=platform.python_version(),numpy=np.__version__,platform=platform.platform(),threads={name:os.environ.get(name) for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS')}),source_sha256={name:hashlib.sha256(Path('stage2',name).read_bytes()).hexdigest() for name in ('quantum_scaling.py','quantum.py','qubo.py')}),indent=2)+'\n')
print(out.read_text())
