"""Read-only live-demo preflight. Does not train, sample or call a service."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def preflight():
    checks=[]
    def check(name,passed,detail=''):
        checks.append(dict(name=name,passed=bool(passed),detail=detail))
    for name in ('numpy','ortools'):
        check('Python dependency: '+name,importlib.util.find_spec(name) is not None)
    base=ROOT/'output/catering-complete-cell-v3'
    try:
        manifest=json.loads((base/'manifest.json').read_text())['files']
        for name in ('quantum-qubo.json','p1-seed-2026/training.json','p1-seed-2026/warm-start.json'):
            digest=hashlib.sha256((base/name).read_bytes()).hexdigest()
            check('Frozen sampling input: '+name,digest==manifest[name])
        evidence=json.loads((ROOT/'scripts/catering-showcase/evidence.json').read_text())
        for name,item in evidence['source_files'].items():
            digest=hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()
            check('Displayed evidence: '+name,digest==item['sha256'],item['path'])
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
                pending=['Final method/VeloxQ result integration','Human voiceover and rehearsal','Video upload and submission'])

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
