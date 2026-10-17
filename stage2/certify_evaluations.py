"""Post-evaluation primary gap bounds; hidden QA draws never feed a policy.

This reads already completed frozen evidence. A necessary quality/material
relaxation plus a checked witness bounds the unknown missing-order gap. Equality
certifies only the primary objective on that fixed tape, not deadline debt/cost.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path

from .compare_evaluations import load_evidence,select_rows,digest,file_hash,PHYSICAL_SOURCES
from .quality_material_bound import certificate
from .spec import build
from .statistics import weighted_mean,weighted_cvar


ROOT=Path(__file__).resolve().parents[1]


def certify(evidence,method_id,config,output):
    if (set(config)!={'orders','horizon','profile'} or config['profile']!='full'
            or config['horizon'] not in (5760,14400)):
        raise ValueError('Post-evaluation proof is audited only for full minute-grid horizons 5760/14400')
    manifest,evaluation,reference=load_evidence(evidence)
    rows=select_rows(manifest,evaluation,method_id,config)
    for name in PHYSICAL_SOURCES:
        if manifest['source_hashes'][name]!=file_hash(ROOT/name):
            raise ValueError('Proof runtime differs from measured physical/verifier source: '+name)
    if manifest['source_hashes'].get('stage2/identity_audit.py')!=file_hash(ROOT/'stage2/identity_audit.py'):
        raise ValueError('Current canonical identity audit required for this fixed-lineage proof')
    grouped=defaultdict(list)
    for row in rows:grouped[row['seed']].append(row)
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    answers=[]
    for seed,group in sorted(grouped.items()):
        instance=build(**config,seed=seed);anchor=digest(instance)
        if any(row['physical_instance_sha256']!=anchor for row in group):raise ValueError('Proof/witness numerical instance mismatch')
        bound=certificate(instance)
        if bound['instance_sha256']!=anchor:raise ValueError('Proof numerical anchor mismatch')
        if any(row['metrics']['orders']!=bound['observed_realized_orders'] for row in group):raise ValueError('Proof/witness demand mismatch')
        low=bound['unfulfilled_lower_bound'];outcomes=[]
        for row in group:
            upper=row['checker_metrics']['unfulfilled_orders']
            if upper<low:raise ValueError('A checked witness violates the necessary bound; do not emit a certificate')
            outcomes.append(dict(actor_seed=row['policy_seed'],checked_missing=upper,lower_bound=low,
                unknown_primary_gap_interval=[0,upper-low],primary_optimum_attained=upper==low))
        path=output/f'seed{seed}-necessary-bound.json';path.write_text(json.dumps(bound,indent=2)+'\n')
        answers.append(dict(seed=seed,tape_weight=group[0]['tape_weight'],physical_instance_sha256=anchor,
            demand=bound['observed_realized_orders'],necessary_missing_lower_bound=low,
            certificate_path=path.name,certificate_sha256=file_hash(path),actors=outcomes,
            mean_missing=sum(r['checked_missing'] for r in outcomes)/len(outcomes),
            mean_primary_gap_upper_bound=sum(r['unknown_primary_gap_interval'][1] for r in outcomes)/len(outcomes),
            primary_attained_fraction=sum(r['primary_optimum_attained'] for r in outcomes)/len(outcomes)))
    weights=[row['tape_weight'] for row in answers]
    result=dict(schema='stage2-measured-primary-gap-certificates.v1',evaluation_role=manifest['evaluation_role'],
        method_id=method_id,config=config,protocol_sha256=manifest['protocol']['payload']['protocol_sha256'],
        source_evidence=reference,source_hashes={name:file_hash(ROOT/name) for name in
            (*PHYSICAL_SOURCES,'stage2/identity_audit.py','stage2/quality_material_bound.py','stage2/certify_evaluations.py')},
        environment_tapes=len(answers),rows=answers,
        weighted_mean_checked_missing=weighted_mean([r['mean_missing'] for r in answers],weights),
        weighted_mean_necessary_missing_lower_bound=weighted_mean([r['necessary_missing_lower_bound'] for r in answers],weights),
        weighted_mean_primary_gap_upper_bound=weighted_mean([r['mean_primary_gap_upper_bound'] for r in answers],weights),
        weighted_primary_optimum_attainment=weighted_mean([r['primary_attained_fraction'] for r in answers],weights),
        weighted_probability_nonzero_necessary_missing=weighted_mean([int(r['necessary_missing_lower_bound']>0) for r in answers],weights),
        actor_mean_environment_cvar90_primary_gap_upper_bound=weighted_cvar([r['mean_primary_gap_upper_bound'] for r in answers],weights),
        scope='Fixed realized tapes; material/quality relaxation ignores scheduling constraints. Positive U-L is only an upper bound on the unknown primary gap. Zero U=L certifies primary optimum, including trivial all-fulfilled witnesses.',
        causal_scope='Offline post-evaluation use of hidden keyed draws only; no policy changes, training labels or future-tape access during dispatch',
        secondary_optimality_gap=None)
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence',type=Path,required=True);parser.add_argument('--method',required=True)
    parser.add_argument('--config',required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=certify(args.evidence,args.method,json.loads(args.config),args.output)
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','source_evidence','source_hashes')},indent=2))


if __name__=='__main__':main()
