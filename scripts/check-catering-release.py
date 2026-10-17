"""Check the release locally without training, recording, publishing or service calls."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def verify(output, full_qaoa=False):
    output = Path(output).resolve()
    if output.exists():
        raise ValueError('Choose a fresh output directory')
    for name in ['node','npm']:
        if shutil.which(name) is None:
            raise ValueError(name+' is required')
    output.mkdir(parents=True)
    env = dict(os.environ, PYTHONPATH=str(ROOT))
    # No command below reads credentials, installs dependencies or contacts a service.
    stages = [
        ('site', ['npm','run','build']),
        ('stage1', [sys.executable,'scripts/check-stage1.py','--output',str(output/'stage1.json')]),
        ('submission-tests', [sys.executable,'-m','unittest','discover','-s','tests','-p','test_submission_checks.py','-q']),
        ('preflight', [sys.executable,'scripts/check-catering-demo.py','--output',str(output/'preflight.json')]),
        ('realism-counts', [sys.executable,'scripts/report-catering-realism.py','--output',str(output/'realism.json')]),
        ('mathematics', [sys.executable,'-m','catering.audit_math','--output',str(output/'mathematics.json')]),
        ('qaoa-archives', [sys.executable,'scripts/check-catering-qaoa.py','--output',str(output/'qaoa.json')]
                         + (['--full-samples'] if full_qaoa else [])),
        ('vqe-exports', [sys.executable,'scripts/check-catering-vqe.py','--output',str(output/'vqe.json')]),
        ('velox-payoff', [sys.executable,'scripts/check-catering-velox-payoff.py','--output',str(output/'velox-payoff.json')]),
        ('core-tests', [sys.executable,'-c',
            "import unittest; s=unittest.TestSuite(); "
            "[s.addTests(unittest.defaultTestLoader.discover('tests/catering',pattern=p+'.py')) "
            "for p in ['test_foundation','test_meal_blocks','test_native_slots']]; "
            "r=unittest.TextTestRunner(verbosity=1).run(s); raise SystemExit(not r.wasSuccessful())"]),
    ]
    stages += [(f'sampling-{i}',[sys.executable,'scripts/catering_live.py','--output',str(output/f'sampling-{i}')])
               for i in range(1,4)]
    results = []
    for i,(name,command) in enumerate(stages,1):
        print(f'[{i}/{len(stages)}] {name}',flush=True)
        start = time.monotonic()
        with (output/(name+'.log')).open('w') as log:
            process = subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
        results.append(dict(name=name,passed=process.returncode==0,seconds=time.monotonic()-start,
                            log=name+'.log'))
        if process.returncode:
            print('Failed; see '+str(output/(name+'.log')),flush=True)
            break
    samples = []
    for i in range(1,4):
        path = output/f'sampling-{i}'/'receipt.json'
        if path.exists():
            r = json.loads(path.read_text())
            samples.append(dict(repetition=i,total_s=r['total_s'],shots=r['shots'],
                valid_shots=r['valid_shots'],best_metrics=r['best_metrics'],
                retained_distribution_reproduced=r['retained_distribution_reproduced']))
    same_sample = len(samples)==3 and all(
        r['shots']==4096 and r['valid_shots']==2173 and r['best_metrics']==dict(U=0,W=0,B=2,R=2)
        and r['retained_distribution_reproduced'] for r in samples)
    try:
        commit = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True,stderr=subprocess.DEVNULL).strip()
        tracked_changes = bool(subprocess.check_output(
            ['git','status','--porcelain','--untracked-files=no'],cwd=ROOT,text=True).strip())
    except subprocess.CalledProcessError:
        commit = None  # A git archive has no .git directory; the caller records its source commit.
        tracked_changes = None
    paths = ['schedule_2x2.json','schedule_3x3.json','LICENSE','README.md','PROJECT_DESIGN.md',
             'DEVELOPMENT_LOG.md','scripts/catering-showcase/story.json',
             'scripts/catering-showcase/evidence.json','scripts/catering-showcase/live-parameters.json',
             'presentation/catering/benchmarks/data.json','output/catering-methods/qaoa/plan-v1.json',
             'scripts/check-stage1.py','scripts/report-catering-realism.py',
             'scripts/check-catering-release.py','tests/test_submission_checks.py',
             'output/catering-realism-cost-v1/report.json']
    paths += ['docs/'+name+'.md' for name in ['CATERING_PRESENTATION','CATERING_VOICEOVER',
        'CATERING_LIVE','CATERING_RECORDING','CATERING_QA','STAGE2_SUBMISSION']]
    dependencies = {}
    for name in ['numpy','ortools','scipy']:
        try:
            dependencies[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            dependencies[name] = None
    ready = len(results)==len(stages) and all(r['passed'] for r in results) and same_sample
    receipt = dict(schema='catering-release-check.v1',technical_ready=ready,submission_ready=False,
        source_commit=commit,tracked_changes=tracked_changes,python=platform.python_version(),dependencies=dependencies,
        checks=results,sampling_repetitions=samples,
        sampling_note='Three repeat executions of the same frozen angles and sampling seed, not independent training or human rehearsals.',
        source_files={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},
        pending=['Three human timed rehearsals','Final video recording, human voiceover and upload',
                 'Final authorized public-source access check','Team/form details and submission acknowledgment'],
        training_campaigns=0,video_recordings=0,physical_qpu_calls=0,veloxq_calls=0)
    (output/'release.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print('TECHNICAL CHECKS PASSED' if ready else 'TECHNICAL CHECK FAILED',flush=True)
    print('Human rehearsal, video and final publication/submission remain separate.')
    return ready


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--full-qaoa',action='store_true',help='Independently decode every QAOA sample, in addition to archive hashes')
    args = parser.parse_args()
    raise SystemExit(0 if verify(args.output,args.full_qaoa) else 1)
