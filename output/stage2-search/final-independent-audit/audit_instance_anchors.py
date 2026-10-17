"""Fresh numerical anchors for every completed final row, without factory run."""
import json
from pathlib import Path
import time

from stage2 import final_eval as f
from stage2.compare_evaluations import load_evidence,validate_payload
from stage2.quality_material_bound import realized_orders_and_stock
from stage2.spec import build


def audit():
    started=time.perf_counter();root=Path('output/stage2-search')
    cohorts={'legacy':'final-legacy-6117510','frontier':'final-frontier-6117515',
        'strong-cheap':'final-strong-cheap-6117508','quantum-stochastic':'final-quantum-stochastic-6117509',
        'mpc-13':'final-mpc-13-6117512'}
    anchors={};counts={};protocol=None
    for label,name in cohorts.items():
        manifest,evaluation,_=load_evidence(root/'final-downloaded'/name)
        validate_payload(manifest,evaluation)
        assert manifest['evaluation_role']=='final'
        actual_protocol=manifest['protocol']['payload']['protocol_sha256']
        if protocol is None:protocol=actual_protocol
        assert protocol==actual_protocol
        for source in('stage2/spec.py','stage2/engine.py','instances/stage2/metaltech_pressure.json'):
            assert manifest['source_hashes'][source]==f.file_hash(f.ROOT/source)
        for row in evaluation['rows']:
            key=(f.digest(row['config']),row['seed'])
            if key not in anchors:
                instance=build(**row['config'],seed=row['seed'])
                orders,_,leaf=realized_orders_and_stock(instance)
                anchors[key]=dict(config=row['config'],seed=row['seed'],physical_instance_sha256=f.digest(instance),
                    realized_mandatory_orders=len(orders),exogenous_leaf=leaf)
            fresh=anchors[key]
            assert row['physical_instance_sha256']==row['executed_instance_sha256']==fresh['physical_instance_sha256']
            assert row['metrics']['orders']==fresh['realized_mandatory_orders']
            assert row['checker_metrics']['delivered_orders']+row['checker_metrics']['unfulfilled_orders']==fresh['realized_mandatory_orders']
            assert row['leaf_outcomes']==fresh['exogenous_leaf']
        counts[label]=len(evaluation['rows'])
    return dict(schema='stage2-independent-full-row-numerical-anchor-audit.v1',valid=True,
        protocol_sha256=protocol,cohort_rows=counts,rows_verified=sum(counts.values()),
        distinct_configuration_tapes=len(anchors),anchors=list(anchors.values()),
        source_sha256=f.file_hash(__file__),wall_seconds=time.perf_counter()-started,factory_simulations=0,
        scope='All available completed final rows anchored to fresh source-matched numerical instances and independently reconstructed exogenous mandatory demand. Repeated methods/actors are repeated executions, not new environment samples. Exogenous labels only; no endogenous quality draw used.')


if __name__=='__main__':
    result=audit()
    output=Path(__file__).with_name('all-available-row-instance-anchors.json')
    with output.open('x')as stream:stream.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='anchors'},indent=2))
