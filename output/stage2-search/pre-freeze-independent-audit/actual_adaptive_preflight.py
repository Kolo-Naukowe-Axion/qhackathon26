"""Independent actual per-context selected artifact integration on TRAIN seed0."""
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import time

from stage2 import final_eval as f
from stage2.check import check_trace
from stage2.identity_audit import audit_trace
from stage2.spec import build


def main():
    output=Path(__file__).resolve().parent/'actual-adaptive-preflight'
    output.mkdir(exist_ok=False)
    before=f.source_hashes();rows=[];start=time.perf_counter()
    index=json.loads((f.ROOT/'output/stage2-search/final-preparation/strong-artifact-index.json').read_text())
    for entry in index:
        checkpoint=(f.ROOT/entry['source_path']).resolve()
        artifact=f._adaptive_artifact(checkpoint,entry['kind'])
        assert f.file_hash(checkpoint)==entry['sha256']
        for config in artifact['configs']:
            started=time.perf_counter()
            method=f._normalize_adaptive(dict(id=entry['name'],kind=entry['kind'],checkpoint=str(checkpoint),
                configs=[config],maintenance_outage_guard=True,
                selection_provenance=dict(data='Existing selected DEVELOPMENT artifacts; integration only')))
            instance=build(**config,seed=0);anchor=deepcopy(instance)
            weights,controller,adapters=f._controller(method,config,900001)
            assert weights['policy_seed']==controller.base['policy_seed']==900001
            trace=f._dispatch_factory(instance,weights,controller,method,config).run()
            checked=check_trace(trace,anchor);identity=audit_trace(trace,anchor)
            assert checked['valid'] and checked['terminal_requirements_met'] and identity['valid'],(checked['issues'],identity['issues'])
            assert f.digest(trace['instance'])==f.digest(anchor)
            telemetry=f.qubo_telemetry(trace);assert telemetry['decode_mismatches']==0
            assert trace['metrics']['shipped']==checked['metrics']['delivered_orders']
            assert trace['metrics']['orders']-trace['metrics']['shipped']==checked['metrics']['unfulfilled_orders']
            assert trace['metrics']['total_tardiness_ticks']==checked['metrics']['terminal_deadline_debt_ticks']
            assert trace['horizon_ticks']==anchor['horizon_ticks'] and trace['tick_minutes']==anchor['tick_minutes']
            path=output/f"{entry['name']}-n{config['orders']}-seed0-actor900001.json.gz"
            path.write_bytes(gzip.compress(json.dumps(trace,separators=(',',':')).encode(),mtime=0))
            rows.append(dict(method=entry['name'],kind=entry['kind'],config=config,environment_seed=0,actor_seed=900001,
                valid=True,checker_metrics=checked['metrics'],metrics=trace['metrics'],identity=identity,
                physical_instance_sha256=f.digest(anchor),kit_reservation=method['kit_reservation'],
                maintenance_outage_guard=True,trajectory=controller.trajectory,adapters=adapters,
                trace=path.name,trace_sha256=f.file_hash(path),wall_seconds=time.perf_counter()-started))
            print(entry['name'],config['orders'],trace['metrics']['shipped'],trace['metrics']['orders'],flush=True)
    result=dict(schema='stage2-independent-adaptive-context-preflight.v1',valid=all(r['valid'] for r in rows),
        rows=rows,source_hashes_before=before,source_hashes_after=f.source_hashes(),
        audited_driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        wall_seconds=time.perf_counter()-start,final_tapes=0,
        scope='Actual selected saved artifact/controller/factory composition on DEVELOPMENTseed0 actor900001; no tuning or reserved performance evidence')
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
