"""Paired realism-cost experiment: exact machine changeovers and start grids."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import sys
import time
import traceback

from .window_campaign import sources,save
from .window_pump import pump_cell
from .window_qubo import compile_qubo,solve_cp,digest
from .window_experiments import encode_plan


def run(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False);root,hashes=sources(output)
    name='stage2/window_setup_experiments.py';data=(root/name).read_bytes();(output/'sources'/name).write_bytes(data);hashes[name]=hashlib.sha256(data).hexdigest()
    protocol=dict(schema='stage2-window-setup-reality-cost.v1',cases=[dict(jobs=2,horizon=1440,grid=g,metric_setups=s)for g in(60,30,15)for s in(False,True)],
        source_hashes=hashes,cp_seconds=30,cp_workers=4,qubo_max_variables=6000,scope='Complete declared finite deterministic pump/BOM cell. Machine-only setup times; human setup crews excluded. Start-grid restriction is NOT lossless relative to minute scheduling.')
    save(output/'protocol.json',protocol);rows=[];began=time.perf_counter();cpu=time.process_time()
    for index,case in enumerate(protocol['cases']):
        row=dict(case=case);folder=output/f'case{index}';folder.mkdir()
        try:
            p=pump_cell(**case);save(folder/'problem.json',p)
            t=time.perf_counter();q=compile_qubo(p,max_variables=6000,support_pruning=True);row.update(qubo=q.metadata(),compile_wall_seconds=time.perf_counter()-t,problem_sha256=digest(p))
            save(folder/'qubo.json',dict(linear=q.linear,quadratic=[[i,j,v]for(i,j),v in sorted(q.quadratic.items())],offset=q.offset,variables=q.variables,groups=q.groups))
            cp=solve_cp(p,30,4);row['native_cp']=cp
            if 'plan'in cp:
                bits=encode_plan(q,cp['plan']);decoded=q.decode(bits);assert decoded['valid']and q.energy(bits)==cp['objective'];row['encoded_cp_check']=decoded
        except Exception as exc:row.update(error=str(exc),traceback=traceback.format_exc())
        save(folder/'report.json',row);rows.append(row)
        print(json.dumps(dict(case=case,variables=row.get('qubo',{}).get('variables'),couplers=row.get('qubo',{}).get('couplers'),
            cp_status=row.get('native_cp',{}).get('status'),objective=row.get('native_cp',{}).get('objective'),bound=row.get('native_cp',{}).get('bound'),error=row.get('error'))),flush=True)
    stable=all(hashlib.sha256((root/name).read_bytes()).hexdigest()==value for name,value in hashes.items())
    summary=dict(rows=rows,source_stable=stable,wall_seconds=time.perf_counter()-began,process_cpu_seconds=time.process_time()-cpu,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin'else 1024))
    save(output/'summary.json',summary);save(output/'manifest.json',{str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(output.rglob('*'))if p.is_file()})
    return {k:v for k,v in summary.items()if k!='rows'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);a=p.parse_args();print(json.dumps(run(a.output),indent=2))
