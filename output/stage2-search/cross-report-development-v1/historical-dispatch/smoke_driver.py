
import json
from pathlib import Path
from stage2 import final_eval as f
config=dict(orders=1,horizon=5760,profile='full')
method=dict(id='smoke',kind='static',backend='advanced',weights=dict(wip_limit=3,mode='standard',selector='qaoa',lease_calibration=True,worker_calendar=True,preposition=False,policy_seed=0),selection_provenance=dict(data='DEVELOPMENT smoke only',training_wall_seconds=0))
for actor in (901,902):assert f._controller(method,config,actor)[0]['policy_seed']==actor
selection=dict(schema='stage2-selected-policy-spec.v1',configs=[config],actor_seeds=[901,902],methods=[method],trace_policy='all',selection_provenance=dict(data='DEVELOPMENT contract smoke only; no policy selection',training_wall_seconds=0))
Path('selection.json').write_text(json.dumps(selection));Path('protocol.json').write_text(json.dumps(f.development_protocol([0,1])))
f.freeze('selection.json','protocol.json','frozen.json',development=True)
r=f.evaluate('frozen.json','evaluation',workers=1)
assert r['actual_rows']==4 and r['missing_or_invalid']==0,r
print(json.dumps(dict(rows=r['actual_rows'],invalid=r['missing_or_invalid'],dispatch=r['source_hashes']['stage2/dispatch.py'])))
