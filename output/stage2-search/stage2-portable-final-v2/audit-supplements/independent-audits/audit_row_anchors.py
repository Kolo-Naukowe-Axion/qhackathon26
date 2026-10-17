"""Fresh numerical anchors for every supplied completed final row; no factory."""
import argparse
import json
from pathlib import Path
import time

from stage2 import final_eval as f
from stage2.compare_evaluations import load_evidence,validate_payload
from stage2.quality_material_bound import realized_orders_and_stock
from stage2.spec import build


def audit(index):
    started=time.perf_counter();paths=json.loads(Path(index).read_text())
    anchors={};counts={};protocol=None;references={}
    for label,path in paths.items():
        manifest,evaluation,reference=load_evidence(path);validate_payload(manifest,evaluation)
        assert manifest['evaluation_role']=='final'and evaluation['missing_or_invalid']==0
        references[label]=reference
        actual_protocol=manifest['protocol']['payload']['protocol_sha256']
        if protocol is None:protocol=actual_protocol
        assert protocol==actual_protocol
        for source in('stage2/spec.py','stage2/engine.py','instances/stage2/metaltech_pressure.json'):
            assert manifest['source_hashes'][source]==f.file_hash(f.ROOT/source)
        for row in evaluation['rows']:
            key=(f.digest(row['config']),row['seed'])
            if key not in anchors:
                instance=build(**row['config'],seed=row['seed']);orders,_,leaf=realized_orders_and_stock(instance)
                anchors[key]=dict(config=row['config'],seed=row['seed'],physical_instance_sha256=f.digest(instance),
                    realized_mandatory_orders=len(orders),exogenous_leaf=leaf)
            fresh=anchors[key]
            assert row['valid']is True
            assert row['physical_instance_sha256']==row['executed_instance_sha256']==fresh['physical_instance_sha256']
            assert row['metrics']['orders']==fresh['realized_mandatory_orders']
            assert row['checker_metrics']['delivered_orders']+row['checker_metrics']['unfulfilled_orders']==fresh['realized_mandatory_orders']
            assert row['leaf_outcomes']==fresh['exogenous_leaf']
        counts[label]=len(evaluation['rows'])
    return dict(schema='stage2-independent-full-row-numerical-anchor-audit.v2',valid=True,
        protocol_sha256=protocol,cohort_rows=counts,rows_verified=sum(counts.values()),
        distinct_configuration_tapes=len(anchors),anchors=list(anchors.values()),evidence=references,
        input_index_sha256=f.file_hash(index),source_sha256=f.file_hash(__file__),
        physical_sources={source:f.file_hash(f.ROOT/source)for source in('stage2/spec.py','stage2/engine.py','instances/stage2/metaltech_pressure.json')},
        wall_seconds=time.perf_counter()-started,factory_simulations=0,
        scope='Every supplied completed final row anchored to a fresh source-matched numerical instance, independently reconstructed exogenous mandatory demand and leaf. Repeated methods/actors are not new environments. Exogenous labels only; no endogenous quality draw used.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--index',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    result=audit(args.index)
    with args.output.open('x')as stream:stream.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k not in('anchors','evidence')},indent=2))
