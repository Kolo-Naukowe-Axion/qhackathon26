import hashlib,json,os,resource,sys,time
from pathlib import Path
from stage2.qubo import build_qubo
from stage2.quantum_scaling import Budget,select_qaoa
fixture=Path(sys.argv[1]);out=Path(sys.argv[2]);seed=int(sys.argv[3]);p=int(sys.argv[4]);evaluations=int(sys.argv[5])
d=json.loads(fixture.read_text());t=time.perf_counter();q=build_qubo(d['candidates'],d['conflicts'],d['capacities']);build_seconds=time.perf_counter()-t
r=select_qaoa(q,seed=seed,layers=p,shots=1024,budget=Budget(max_bits=24,memory_mib=1536,seconds=180,evaluations=evaluations,reference_core_bits=16,sa_sweeps=100,sa_restarts=4))
r['timings']['build_qubo_seconds']=build_seconds;r['elapsed_including_qubo_construction_seconds']=r['elapsed_seconds']+build_seconds
r['fixture_path']=str(fixture.resolve());r['input_sha256']=hashlib.sha256(fixture.read_bytes()).hexdigest()
r['fixture_provenance']={k:v for k,v in d.items() if k not in ('candidates','conflicts','capacities','offered_operations')}
peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;r['peak_process_rss_bytes']=peak if sys.platform=='darwin' else peak*1024
r['runtime']['thread_environment']={k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS')}
out.write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(dict(path=str(out),bits=q.size,core=len(q.candidates),seed=seed,p=p,evals=r['optimization']['evaluations'],reward=r['reward'],optimum=r['reference'].get('reward'),uniform=r['uniform']['reward'],sa=r['sa']['reward'],repaired=r['repaired'],ideal=r['ideal'],timings=r['timings'],elapsed=r['elapsed_seconds'],rss_MiB=r['peak_process_rss_bytes']/1024**2),indent=2))
