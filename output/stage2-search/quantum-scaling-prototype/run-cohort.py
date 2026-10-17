import json,os,subprocess,sys,time
from pathlib import Path
out=Path(__file__).parent
fixture=Path('output/stage2-search/selector-domain-training-audit/expanded-pool-fixtures')
cohort=[dict(total_bits=bits,core_bits=core,layers=p,seed=seed,evaluations=32,shots=1024) for bits,core in ((11,6),(19,13),(23,14)) for p in (1,2) for seed in range(3)]
protocol=dict(schema='quantum-scaling-pilot-cohort.v1',role='DEVELOPMENT_FIXED_POOL_ONLY',cases=cohort,selection='three actual checked expanded-crew pools selected by total size before this cohort, not final factory tapes',runtime_environment={k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS')})
(out/'cohort-protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
for case in cohort:
 bits,core,p,seed=(case[k] for k in ('total_bits','core_bits','layers','seed'));target=out/f'pool{bits}-p{p}-seed{seed}.json'
 if target.exists():continue
 subprocess.run([sys.executable,str(out/'pool-benchmark.py'),str(fixture/f'pool-total{bits}-core{core}.json'),str(target),str(seed),str(p),'32'],check=True)
rows=[]
for c in cohort:
 r=json.loads((out/f"pool{c['total_bits']}-p{c['layers']}-seed{c['seed']}.json").read_text())
 rows.append(dict(**c,qaoa_reward=r['reward'],uniform_reward=r['uniform']['reward'],sa_reward=r['sa']['reward'],exact_reward=r['reference']['reward'],repaired=r['repaired'],ideal=r['ideal'],seconds=r['elapsed_seconds'],timings=r['timings'],peak_rss_bytes=r['peak_process_rss_bytes'],source_sha256=r['source_sha256']))
(out/'cohort-summary.json').write_text(json.dumps(dict(protocol=protocol,rows=rows),indent=2)+'\n')
print(json.dumps(rows,indent=2))
