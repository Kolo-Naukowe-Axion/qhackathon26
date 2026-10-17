"""Read retained results into a compact public comparison page. No solver calls."""
import json
import hashlib
import csv
import io
import statistics
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def read(path):return json.loads((ROOT/path).read_text())
def file_hash(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def public_source(path):return dict(path=path,sha256=file_hash(path))

def export():
    sources={}
    def load(path):
        sources[path]=public_source(path)
        return read(path)
    qbase='output/catering-methods/qaoa/'
    qaoa={split:load(qbase+split+'-v1/summary.json') for split in ['train','test']}
    runs=[]
    for split in ['train','test']:
        runs += [dict(split=split,**r) for r in load(qbase+split+'-v1/runs.json')]
    classical=[]
    from catering.contracts import load_bundle
    from catering.build_meal_release import result_summary
    for case in ['cell','S0','S1','S2','S3']:
        directory='output/catering-complete-cell-v3' if case=='cell' else f'output/catering-foundation-v3/{case}'
        sources[directory+'/quantum-qubo.json']=public_source(directory+'/quantum-qubo.json')
        b=load_bundle(ROOT/(directory+'/quantum-qubo.json'))
        source=directory+('/reference-sector.json' if case=='cell' else '/quantum-sector-reference.json')
        ref=load(source);metrics=(ref.get('ground') or ref)['check']['metrics']
        rawpath=directory+('/reference-raw.json' if case=='cell' else '/raw-reference.json')
        raw=load(rawpath)
        row=dict(case=case,bundle_sha256=b['bundle_sha256'],qubits=len(b['linear']),
            portfolio_optimum=[metrics[k] for k in ['U','W','B','R']],
            raw_optimum=[raw['check']['metrics'][k] for k in ['U','W','B','R']])
        sapath=directory+'/quantum-sa.json'
        if (ROOT/sapath).exists():row['sa']=result_summary(b,load(sapath))
        classical.append(row)
    # Include all service attempts. Separate matrix identities prevent false same-input rankings.
    ledger=load('output/catering-methods/veloxq/job_ledger.json')['jobs'];service=[]
    own=load('output/catering-velox-conditioned-service-v1/report.json')
    own_by_id={r['job_id']:r for r in own['rows']}
    for index,entry in enumerate(ledger,1):
        row=dict(attempt=index,case=entry.get('case_id'),job_id=entry.get('job_id'),bundle=entry.get('bundle_id'),
            packet_sha256=entry.get('packet_sha256'),status='no job created' if not entry.get('job_id') else 'receipt missing')
        if entry.get('job_id') in own_by_id:
            r=own_by_id[entry['job_id']]
            row.update(status=r['status'],variables=r['sampling_variables'],source_variables=r['source_variables'],
                valid=r['valid_rows'],shots=r['total_rows'],best=r['best'],steps=r['settings']['num_steps'],
                reps=r['settings']['num_rep'],backend_s=r['backend_statistics'].get('running_time'),
                wall_s=None if r['recovery'] else r['adapter_total_s'],download_recovered=bool(r['recovery']),
                representation=r['settings']['conditioning']['policy'])
        else:
            suffix='output/'+entry['output_dir'].split('/output/',1)[-1] if '/output/' in entry['output_dir'] else entry['output_dir']
            directory=ROOT/suffix
            path=directory/'result.json'
            if path.exists():
                r=json.loads(path.read_text());conf=r.get('configuration',{});params=conf.get('parameters',{})
                row.update(status=r.get('status','unknown'),variables=r.get('representation',{}).get('n'),
                    shots=sum(s.get('count',1) for s in r.get('samples',[])),steps=params.get('num_steps'),reps=params.get('num_rep'),
                    backend_s=r.get('backend_statistics',{}).get('running_time'),wall_s=None if r.get('recovery') else r.get('timings',{}).get('total_s'),download_recovered=bool(r.get('recovery')),
                    bundle_sha256=r.get('bundle_sha256'),representation=r.get('representation_id','smoke'))
                ep=directory/'evaluation.json'
                if ep.exists():
                    sources[str(ep.relative_to(ROOT))]=public_source(str(ep.relative_to(ROOT)))
                    ev=json.loads(ep.read_text());valid=[v for v in ev.get('results',[]) if v.get('valid')]
                    row['valid']=sum(v.get('count',1) for v in valid)
                    row['best']=min((v['check']['metrics'] for v in valid),key=lambda m:tuple(m[k] for k in ['U','W','B','R']),default=None)
                sources[str(path.relative_to(ROOT))]=public_source(str(path.relative_to(ROOT)))
        service.append(row)
    vqe=dict(verification=load('output/catering-methods/vqe/integration-v2/verification.json'),grids={})
    for case in ['cell','S0','S1','S2','S3']:
        for name in ['result.json','evaluation.json','artifacts.json']:
            path=f'output/catering-methods/vqe/method-results/{case}/{name}'
            sources[path]=public_source(path)
    for grid in ['E1','E2','E3','E5']:
        path=f'output/catering-methods/vqe/{grid}-v1/runs.csv'
        sources[path]=public_source(path)
        keep=['case','spec','tag','seed','layers','n_params','optimizer','loss','alpha','nfev','n_grad','hw_circuits_equiv','shot_hit_opt','p_opt','p_valid','shot_valid_rate','shots','status','error','t_opt']
        vqe['grids'][grid]=[{k:r.get(k) for k in keep} for r in csv.DictReader(io.StringIO((ROOT/path).read_text()))]
    primary_tag='A3-coupled-cgiv-L2|lbfgs|cvar0.1|exact|init-w0.2'
    vqe['primary_heldout']=[]
    for case in ['S2','S3']:
        rows=[r for r in vqe['grids']['E5'] if r['case']==case and r['tag']==primary_tag and r['status']=='completed']
        if len(rows)!=10:raise ValueError(f'Expected ten primary VQE rows for {case}, got {len(rows)}')
        vqe['primary_heldout'].append(dict(case=case,seeds=len(rows),hits=sum(r['shot_hit_opt']=='True' for r in rows),
            probability=statistics.median(float(r['p_opt']) for r in rows),
            valid_probability=statistics.median(float(r['p_valid']) for r in rows),
            median_evaluations=statistics.median(int(r['nfev']) for r in rows),
            median_shift_equivalents=statistics.median(int(r['hw_circuits_equiv']) for r in rows),
            parameters=sorted(set(int(r['n_params']) for r in rows)),shots=sorted(set(int(r['shots']) for r in rows))))
    data=dict(schema='catering-benchmarks.v1',qaoa=qaoa,qaoa_runs=runs,classical=classical,veloxq=service,
        source_files=list(sources.values()),scale=load('output/catering-velox-scale-v3/report.json'),
        controls=load('output/catering-velox-noidle-controls-v1/report.json'),vqe=vqe,
        notes=['QAOA compares the identical frozen portfolio; full-grid references measure representation loss.',
          'VeloxQ formulations/pools/objectives differ: compare identities before ranking.',
          'Simulator exact probabilities train QAOA; final measurements use4096 shots.',
          'Backend time, full-call time and recovery time are distinct; missing successful wall times stay blank.',
          'VQE archived hardware equivalents assume two shifts per parameter: an unvalidated legacy heuristic, not hardware cost.',
          'VQE E2 three-point NFT assumes a single-frequency control loss; primary E5 L-BFGS-B/CVaR does not use NFT.'])
    # source_files is materialized after all load() calls, including scale/controls.
    data['source_files']=list(sources.values())
    out=ROOT/'presentation/catering/benchmarks/data.json';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(data,separators=(',',':'))+'\n')
    print('Exported',len(runs),'QAOA runs and',len(service),'VeloxQ attempts')

if __name__=='__main__':export()
