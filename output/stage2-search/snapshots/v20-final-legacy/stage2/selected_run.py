"""Replay one explicitly selected policy on an existing development tape.

This convenience entry point uses the same source/instance/identity checks as
the frozen evaluator. Reserved final evidence uses final_eval directly.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path

from . import final_eval as evaluation


def execute(selection,method_id,config,seed,output,actor_seed=900000):
    selection=Path(selection).resolve();source=json.loads(selection.read_text())
    if source.get('schema')!='stage2-selected-policy-spec.v1':raise ValueError('Explicit selected-policy specification required')
    if config not in source['configs']:raise ValueError('Configuration was not selected/measured in this specification')
    chosen=[method for method in source['methods'] if method['id']==method_id and config in method.get('configs',source['configs'])]
    if len(chosen)!=1:raise ValueError('Exactly one selected method must support this configuration')
    protocol=evaluation.development_protocol([seed])
    method=evaluation._resolve_paths(chosen[0],selection.parent)
    method['configs']=[deepcopy(config)]
    spec=deepcopy(source);spec.update(configs=[deepcopy(config)],methods=[method],actor_seeds=[actor_seed],trace_policy='all')
    spec['selection_provenance']=dict(original=source['selection_provenance'],original_selection_path=str(selection),
        original_selection_sha256=evaluation.file_hash(selection),
        scope='One selected-policy development replay; no new policy search or held-out estimate')
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    (output/'selection.json').write_text(json.dumps(spec,indent=2)+'\n')
    (output/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    evaluation.freeze(output/'selection.json',output/'protocol.json',output/'frozen.json',development=True)
    result=evaluation.evaluate(output/'frozen.json',output/'execution',workers=1)
    row=result['rows'][0]
    return dict(valid=row['valid'],issues=row.get('issues',[]),error=row.get('error'),
        metrics=row.get('metrics'),trace_path=row.get('trace_path'),output=str(output),
        scope='Development replay; factory time is simulated, timing fields measure execution')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selection',type=Path,required=True);parser.add_argument('--method',required=True)
    parser.add_argument('--orders',type=int,required=True);parser.add_argument('--horizon',type=int,default=5760)
    parser.add_argument('--seed',type=int,default=0);parser.add_argument('--actor-seed',type=int,default=900000)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    result=execute(args.selection,args.method,dict(orders=args.orders,horizon=args.horizon,profile='full'),
        args.seed,args.output,args.actor_seed)
    print(json.dumps(result,indent=2))
    if not result['valid']:raise SystemExit(1)


if __name__=='__main__':main()
