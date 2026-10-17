"""Read-only diagnosis of assembly-kit flag versus calibration rental."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
COHORT = ROOT / 'output/stage2-search/final-downloaded/final-strong-cheap-6117508'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=read(COHORT/'manifest.json')
sources=('stage2/bounds.py','stage2/selected_run.py','stage2/final_eval.py','stage2/dispatch.py',
         'stage2/engine.py','stage2/spec.py','stage2/kitting.py','stage2/kit_recovery.py',
         'stage2/adaptive_recovery.py','stage2/adaptive_modes.py','stage2/recovery_mpc.py',
         'instances/stage2/metaltech_pressure.json')
source_hashes={name:sha(ROOT/name) for name in sources}
for name,h in source_hashes.items():
    if name in manifest['source_hashes']:assert manifest['source_hashes'][name]==h
methods=[];artifact_hashes={}
for index,method in enumerate(manifest['methods']):
    if not any(c['orders']==24 for c in method['configs']):continue
    if method['kind']=='static':
        weights=method['weights'];origin='frozen final method weights'
    else:
        assert method['kind'] in ('adaptive_recovery','adaptive_modes')
        remote=method['checkpoint'];local=ROOT/'output/stage2-search/final-preparation/checkpoints'/Path(remote).name
        assert sha(local)==manifest['artifacts'][remote]['sha256']
        artifact_hashes[str(local.relative_to(ROOT))]=sha(local)
        artifact=read(local);contexts=[c for c in artifact['contexts'] if c['config']['orders']==24]
        assert len(contexts)==1;weights=contexts[0]['weights'];origin='immutable checkpoint context base weights'
        assert contexts[0]['solver_options']['kit_reservation'] is False
    assert weights['lease_calibration'] is True and method['kit_reservation'] is False
    methods.append(dict(method_index=index,id=method['id'],kind=method['kind'],lease_calibration=True,
                        kit_reservation=False,weight_origin=origin))
assert len(methods)==8
traces=[]
for path in sorted((COHORT/'traces').glob('*-config-2-*.json')):
    t=read(path);assert len(t['instance']['orders'])==24 and t['horizon_ticks']==5760
    option=t['instance']['lease_options'][0]
    assert option['id']=='calibration-kit' and option['cost']==150 and option['lead_ticks']==480
    assert option['resource']['id']=='calibration_lease' and option['resource']['kind']=='calibration'
    assert t['instance']['investment_budget']==250
    # Exact event types: substring 'lease' would incorrectly include 'release'.
    requests=[e for e in t['events'] if e['type']=='lease_request']
    deliveries=[e for e in t['events'] if e['type']=='lease_delivery']
    assert len(requests)==len(deliveries)==1
    request,delivery=requests[0],deliveries[0]
    assert request==dict(tick=0,type='lease_request',option_id='calibration-kit',arrival_tick=480,cost=150)
    assert delivery['tick']==480 and delivery['option_id']=='calibration-kit'
    assert delivery['tool']==option['resource']
    assert t['metrics']['investment_cost']==150 and t['provenance']['kit_space_reservation'] is False
    traces.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path),lease_request=request,
                       lease_delivery_tick=480,investment_cost=150,assembly_kit_reservation=False,
                       actor_seed=900000,scope='Predeclared retained first-tape/first-actor record; no fresh physical replay'))
assert len(traces)==64
counts=Counter(Path(t['path']).name.split('-config-')[0] for t in traces)
assert set(counts)=={f"method-{m['method_index']}" for m in methods} and set(counts.values())=={8}
mpc_path=ROOT/'output/stage2-search/final-preparation/mpc-24-selection.json';mpc=read(mpc_path)['methods'][0]
assert mpc['weights']['lease_calibration'] is True and mpc['kit_reservation'] is False
assert all('lease_calibration' not in action for action in mpc['mpc']['actions'])
result=dict(schema='stage2-static-no-rental-premise-review.v1',valid=True,
    scope='Diagnostic source/saved-record interpretation only; no new performance estimate or conditional theorem',
    conclusion='False premise: kit_reservation=False disables assembly whole-BOM-space admission, not calibration-kit rental. All eight strong cheap final24 methods retain lease_calibration=True; the final24 MPC specification does too.',
    method_scope='Eight static/adaptive methods of final-strong-cheap-6117508 and final MPC24 specification; no universal claim about older legacy learner action domains',
    no_rental_bound_applicable_to_these_controllers=False,new_bound_derived=False,
    global_lease_enabled_optimality_gap='unknown',
    policy_mechanisms=dict(kit_reservation='Conceptual three-component assembly input-space reservations only, implemented by KitMixin.assembly; false delegates ordinary assembly routing. It does not change tools, rental budget or objective.',
        lease_calibration='Independent weight in engine.capacity_decisions: request150-cost calibration kit,480-minute lead, maxone under250 investment budget.',
        adaptive_six='Actions override WIP/QAguard only. Controller copies context base weights, retaining lease_calibration=True.',
        adaptive_eighteen='Actions override WIP/QAguard/T-Fmode only; lease remains in context base weights.',
        evaluator='Adaptive normalization gets kit flag from solver_options, while controller obtains lease flag from checkpoint context weights; these are distinct paths.'),
    existing_bound_scope='stage2.bounds.labor_and_tools gives necessary QA/tool/service/calendar workload bounds for fixed initial capacity. Its full report explicitly discloses no leases/shocks/rework/rush/initialWIP; applying it unchanged to rented capacity or as an unconditional all-order primary bound is invalid. No new rush/precision/cardinality envelope is needed after the premise fails.',
    methods=methods,retained_trace_coverage=dict(cohort=str(COHORT.relative_to(ROOT)),methods=8,leaves_per_method=8,traces=64,
        all_requests_at_tick=0,all_deliveries_at_tick=480,investment_cost_per_trace=150,
        scope='Only64 retained24 traces counted; not a claim that all2048 final24 executions were physically replayed or event-counted here'),
    retained_traces=traces,final_mpc24=dict(id=mpc['id'],lease_calibration=True,kit_reservation=False,actions_preserve_lease=True),
    source_hashes=source_hashes,source_hashes_match_frozen_manifest_where_present=True,
    immutable_checkpoint_hashes=artifact_hashes,
    input_manifest_sha256=sha(COHORT/'manifest.json'),mpc_selection_sha256=sha(mpc_path),
    analysis_source_sha256=sha(Path(__file__)),factory_runs=0,solver_runs=0,test_reruns=0,
    frozen_files_modified=False,policy_selection_changed=False)
(OUT/'report.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('valid','conclusion','no_rental_bound_applicable_to_these_controllers','retained_trace_coverage')},indent=2))
