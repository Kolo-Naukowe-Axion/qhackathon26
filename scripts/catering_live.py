"""Local live demo: fresh sampling with frozen angles, no training or service."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def run_demo(output,shots=4096,seed=17102026):
    import numpy as np
    from catering.contracts import load_bundle,method_result
    from catering.decode import decode
    from catering.meal_blocks import sector_data
    from catering.meal_search import warm_state,evolve,sample_result
    from catering.qubo import energy

    started=time.monotonic();output=Path(output)
    if output.exists():raise ValueError("Fresh demo output directory required")
    if not 1<=shots<=16384:raise ValueError("Local demo supports 1–16384 shots")
    output.mkdir(parents=True)
    base=ROOT/'output/catering-complete-cell-v3'
    paths=dict(bundle=base/'quantum-qubo.json',parameters=ROOT/'scripts/catering-showcase/live-parameters.json')
    manifest=json.loads((base/'manifest.json').read_text())
    hashes={name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in paths.items()}
    if hashes['bundle']!=manifest['files']['quantum-qubo.json']:
        raise ValueError('Frozen bundle hash mismatch')
    frozen=json.loads(paths['parameters'].read_text())
    # Verify the retained campaign source, without extracting or retraining it.
    import tarfile
    source=frozen['source']
    with tarfile.open(ROOT/source['archive']) as archive:
        raw=archive.extractfile(source['member']).read()
    if hashlib.sha256(raw).hexdigest()!=source['sha256']:
        raise ValueError('Frozen trained-parameter source hash mismatch')
    original=json.loads(raw)
    params=original['configuration']['best_params']
    if [v for layer in frozen['parameters'] for v in layer]!=params:
        raise ValueError('Export differs from frozen trained angles')
    bundle=load_bundle(paths['bundle'])
    if frozen['bundle_sha256']!=bundle['bundle_sha256']:raise ValueError('Parameter/bundle mismatch')
    parameters=frozen['parameters'];warm=frozen
    sector=sector_data(bundle)
    state=warm_state(bundle,sector,set(warm['incumbent_program_ids']),warm['exploration'])
    state=evolve(state,sector,parameters,bundle['objective']['weights']['U'])
    measured,winner=sample_result(bundle,sector,state,np.random.default_rng(seed),shots)
    if winner is None:raise RuntimeError("No feasible sample returned; use retained fallback")
    result=method_result(bundle,'live_frozen_angle_xy_qaoa',measured['samples'])
    result.update(execution_kind='quantum_simulator',shots=shots,valid_shots=measured['valid_shots'],
                  configuration=dict(seed=seed,depth=len(parameters),frozen_parameters=True,
                                     training_runs=0,repair=False,parameter_source_sha256=hashes['parameters'],parameter_campaign_source=frozen['source']))
    (output/'samples.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    # Recheck every raw return rather than trusting the sampler's summary.
    checks=[]
    for sample in result['samples']:
        checked=decode(bundle,sample['bits'])
        if int(sample['reported_energy'])!=energy(bundle,sample['bits']):
            raise AssertionError("Returned energy mismatch")
        checks.append(dict(count=sample['count'],valid=checked['valid'],energy=checked['energy']))
    best=winner[1];metrics=best['check']['metrics']
    saved=json.loads((ROOT/'output/catering-complete-cell-demo-v3.json').read_text())
    displayed_count=sum(s['count'] for s in result['samples'] if s['bits']==saved['sample']['bits'])
    receipt=dict(status='completed',execution_kind='fresh_local_sampling_frozen_angles',
                 generated_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
                 data_qubits=bundle['size']['binary_variables'],sector_states=sector['states'],
                 shots=shots,valid_shots=measured['valid_shots'],distinct_returns=len(checks),
                 best_metrics=metrics,complete_meals=best['check']['completed_meal_lots']*bundle['instance']['lot_size'],
                 waste_portions=metrics['W']*bundle['instance']['lot_size'],
                 displayed_retained_sample_observed_shots=displayed_count,
                 seed=seed,training_runs=0,parameters_frozen=True,repair=False,
                 veloxq_calls=0,physical_qpu_calls=0,bundle_sha256=bundle['bundle_sha256'],
                 input_sha256=hashes,depth=len(parameters),parameter_configuration=frozen['configuration'],total_s=time.monotonic()-started,
                 source_result=str(output/'samples.json'),
                 limitation='Classically enumerated one-hot sector. No training, hardware or advantage claim.')
    (output/'checks.json').write_text(json.dumps(checks,indent=2)+'\n')
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--shots',type=int,default=4096)
    parser.add_argument('--seed',type=int,default=17102026)
    args=parser.parse_args()
    print('AXION KITCHEN / FRESH LOCAL QAOA SAMPLE / FROZEN ANGLES',flush=True)
    receipt=run_demo(args.output,args.shots,args.seed)
    print('Checked (U,W,B,R):',tuple(receipt['best_metrics'][k] for k in ('U','W','B','R')))
    print(f"Complete meals: {receipt['complete_meals']} /20. Waste: {receipt['waste_portions']} component portions.")
    print(f"{receipt['valid_shots']}/{receipt['shots']} valid shots. {receipt['total_s']:.3f}s, excluding Python imports.")
    print('Training runs 0. VeloxQ calls 0. Physical QPU calls 0.')
    print('Receipt:',args.output/'receipt.json')
