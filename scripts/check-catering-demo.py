"""Read-only live-demo preflight. Does not train, sample or call a service."""
import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def preflight():
    checks=[]
    def check(name,passed,detail=''):
        checks.append(dict(name=name,passed=bool(passed),detail=detail))
    for name in ('numpy','ortools'):
        check('Python dependency: '+name,importlib.util.find_spec(name) is not None)
    base=ROOT/'output/catering-complete-cell-v3'
    try:
        manifest=json.loads((base/'manifest.json').read_text())['files']
        for name in ('quantum-qubo.json',):
            digest=hashlib.sha256((base/name).read_bytes()).hexdigest()
            check('Frozen sampling input: '+name,digest==manifest[name])
        import tarfile
        frozen=json.loads((ROOT/'scripts/catering-showcase/live-parameters.json').read_text())
        with tarfile.open(ROOT/frozen['source']['archive']) as archive:
            raw=archive.extractfile(frozen['source']['member']).read()
        check('Frozen trained p3 parameters',hashlib.sha256(raw).hexdigest()==frozen['source']['sha256'] and json.loads(raw)['configuration']['best_params']==[v for layer in frozen['parameters'] for v in layer])
        evidence=json.loads((ROOT/'scripts/catering-showcase/evidence.json').read_text())
        for name,item in evidence['source_files'].items():
            digest=hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()
            check('Displayed evidence: '+name,digest==item['sha256'],item['path'])
        from solver.stage1 import validate,exact_reference
        for label,plan in evidence['stage1'].items():
            original=json.loads((ROOT/evidence['source_files']['stage1_'+label]['path']).read_text())
            instance=json.loads((ROOT/'instances'/f"{plan['instance']}.json").read_text())
            check('Displayed Stage 1 '+label,plan==original and not validate(instance,plan['schedule'],plan['makespan']) and exact_reference(instance)['makespan']==plan['makespan'])
        compiler=(ROOT/'catering/meal_blocks.py').read_text().splitlines()
        excerpt='\n'.join(f'{i+1:3}  {compiler[i]}' for i in range(118,128))
        check('Displayed compiler excerpt',evidence['code_excerpt']==excerpt)
        argument=evidence['explanation']
        bundle=json.loads((ROOT/evidence['source_files']['cell_bundle']['path']).read_text())
        scale=json.loads((ROOT/evidence['source_files']['scale_domain']['path']).read_text())
        witness=argument['conflict']; i,j=witness['indices']; alternate=witness['alternative_index']
        a,b,alternative=[bundle['options'][k] for k in [i,j,alternate]]
        ends=[p['cook_start']+bundle['instance']['menus'][p['menu']]['cooking'][str(p['yield_lots'])] for p in [a,b]]
        check('Displayed real batch conflict',
            [min(i,j),max(i,j)] in bundle['conflicts']
            and a['cooker']==b['cooker']==witness['cooker']
            and witness['start']==max(a['cook_start'],b['cook_start'])
            and witness['end']==min(ends) and witness['start']<witness['end']
            and alternative['menu']==a['menu'] and alternative['allocation_order']==a['allocation_order']
            and alternative['cooker']==witness['alternative_cooker']
            and [min(j,alternate),max(j,alternate)] not in bundle['conflicts'])
        program_example=argument['program_example']
        demo=json.loads((ROOT/evidence['source_files']['demo']['path']).read_text())
        selected=bundle['options'][program_example['index']]
        check('Displayed program operation timeline',
            program_example['batch']==selected
            and demo['sample']['bits'][program_example['index']]==1
            and program_example['operations']==[o for o in demo['plan']['operations'] if o['batch_id']==selected['id']])
        span=sum(abs(int(v)) for v in bundle['objective']['linear'])+sum(abs(int(t['value'])) for t in bundle['objective']['quadratic'])
        check('Displayed penalty proof constants',argument['objective_span']==span and argument['penalty']==int(bundle['penalty'])==span+1)
        expected_rows=[dict(source_bits=r['size']['binary_variables'],program_bits=r['size']['option_bits'],qubo_pairs=r['size']['couplers']) for r in scale['rows']]
        check('Displayed scale-domain counts',argument['full_local_program_count']==scale['full_local_program_count'] and argument['scale_rows']==expected_rows)
        hybrid=json.loads((ROOT/evidence['source_files']['velox_hybrid']['path']).read_text())
        hybrid_check=json.loads((ROOT/evidence['source_files']['velox_hybrid_check']['path']).read_text())
        hybrid_row=next(r for r in hybrid['rows'] if r['name']=='lns-2048-step1')
        shown=evidence['velox']['hybrid']
        check('Displayed hybrid VeloxQ step',all(shown[k]==hybrid_row[k] for k in shown)
              and shown['start']==hybrid_check['incumbent_metrics']
              and shown['best']==hybrid_check['best']['metrics']
              and hybrid_check['best']['valid'] and shown['valid_shots']==hybrid_check['valid_shots'])
        loop=json.loads((ROOT/evidence['source_files']['velox_loop']['path']).read_text())
        check('Displayed VeloxQ loop',[dict(solver_width=r['solver_width'],start=r['start'],final=r['final'],service_jobs=r['service_jobs'],
              exact_control=r['exact_control']['final'],cp_30s=r['cp_30s'],cp_240s_4_workers=r['cp_240s_4_workers']) for r in loop['rows']]
              ==evidence['velox']['loop']['rows'])
        benchmarks=json.loads((ROOT/'presentation/catering/benchmarks/data.json').read_text())
        stale=[item['path'] for item in benchmarks['source_files'] if hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()!=item['sha256']]
        check('Benchmark source hashes',not stale,', '.join(stale) if stale else str(len(benchmarks['source_files']))+' retained sources')
        check('Benchmark coverage',len(benchmarks['qaoa_runs'])==400 and len(benchmarks['veloxq'])==137 and len(benchmarks['vqe']['verification']['checked_results'])==5)
        story=json.loads((ROOT/'scripts/catering-showcase/story.json').read_text())
        check('Video fits five minutes',sum(c['duration'] for c in story)<=300)
        check('Live route leaves speaking margin',sum(c['live_duration'] for c in story)<=165)
        check('Live speaker cues exist',all(c.get('live_narration') and c.get('live_action') for c in story if c['live_duration']))
    except (OSError,KeyError,ValueError) as exc:
        check('Retained inputs readable',False,str(exc))
    for name in ('schedule_2x2.json','schedule_3x3.json','LICENSE',
                 'presentation/catering/replay-data.json','presentation/catering/assets/kitchen-empty-v3.png'):
        check('Required file: '+name,(ROOT/name).is_file())
    return dict(ready_for_rehearsal=all(c['passed'] for c in checks),
                checks=checks,training_runs=0,sampling_runs=0,service_calls=0,
                pending=['Human voiceover and rehearsal','Video upload and submission'])

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args();result=preflight()
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2)+'\n')
    print('READY FOR REHEARSAL' if result['ready_for_rehearsal'] else 'PREFLIGHT FAILED')
    for check in result['checks']:
        print(('PASS' if check['passed'] else 'FAIL')+' '+check['name']+(': '+check['detail'] if check['detail'] else ''))
    print('No training, sampling or service calls. Final result and submission gates remain separate.')
    raise SystemExit(0 if result['ready_for_rehearsal'] else 1)
