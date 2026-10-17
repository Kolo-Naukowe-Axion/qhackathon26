"""Recheck the retained equal-budget VeloxQ comparison. No solver/service calls."""
import hashlib
import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from catering.contracts import load_bundle
from catering.decode import decode
from catering.paired_meals import active_meals


def verify():
    report_path=ROOT/'output/catering-velox-conditioned-service-v1/report.json'
    report=json.loads(report_path.read_text())
    sources={str(report_path.relative_to(ROOT)):hashlib.sha256(report_path.read_bytes()).hexdigest()}
    comparisons=[]
    for name in ['cold-long-512','noidle-long-512']:
        row=next(r for r in report['rows'] if r['name']==name)
        settings=row['settings']
        assert settings['initializer']=='cold' and settings['num_steps']==20000 and settings['num_rep']==512
        bundle_path=ROOT/settings['source_bundle'];bundle=load_bundle(bundle_path)
        assert bundle['bundle_sha256']==settings['source_bundle_sha256']
        raw_path=report_path.parent/row['result'];raw=json.loads(raw_path.read_text())
        assert raw['bundle_sha256']==bundle['bundle_sha256']
        valid=[]
        for sample in raw['samples']:
            checked=decode(bundle,sample['bits'])
            assert int(sample['reported_energy'])==int(checked['energy']), 'Retained reported energy differs from literal decoded energy'
            if checked['valid']:valid.append((checked,sample))
        best,sample=min(valid,key=lambda pair:tuple(pair[0]['check']['metrics'][k] for k in ['U','W','B','R']))
        assert best['check']['metrics']==row['best']
        handovers=best['plan']['meal_handovers']
        served_lots=sum(h['lots'] for h in handovers)
        assert served_lots==best['check']['completed_meal_lots']
        meal_lots=len(active_meals(bundle['instance'],bundle['snapshot']))
        assert meal_lots==14 and all(m['priority']==1 for m in active_meals(bundle['instance'],bundle['snapshot']))
        assert sum(s['count'] for s in raw['samples'])==512
        valid_shots=sum(s['count'] for _,s in valid)
        assert valid_shots==row['valid_rows']
        for path in [bundle_path,raw_path]:sources[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
        comparisons.append(dict(name=name,source_bundle_sha256=bundle['bundle_sha256'],
            sampling_bundle_sha256=settings['sampling_bundle_sha256'],steps=20000,replicas=512,
            metrics=best['check']['metrics'],valid_shots=valid_shots,total_shots=512,
            active_meal_lots=meal_lots,lot_size=bundle['instance']['lot_size'],
            complete_meals=served_lots*bundle['instance']['lot_size'],
            discarded_portions=best['check']['discarded_lots']*bundle['instance']['lot_size'],
            best_bits=sample['bits'],raw_check=best['check'],meal_handovers=handovers))
    assert [r['complete_meals'] for r in comparisons]==[10,50]
    assert [r['discarded_portions'] for r in comparisons]==[30,60]
    return dict(status='passed',kind='Independent raw-handover recheck of retained equal-budget jobs',
        rows=comparisons,source_files=sources,training_runs=0,service_calls=0,
        limitation='Single exploratory job per representation; source programs/objective fixed, sampling matrices differ. CP/SA still find better schedules.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    path=args.output
    if path.exists():parser.error('Fresh output file required; retained evidence is never overwritten')
    result=verify();path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({r['name']:dict(meals=r['complete_meals'],waste=r['discarded_portions'],valid=r['valid_shots']) for r in result['rows']}))
