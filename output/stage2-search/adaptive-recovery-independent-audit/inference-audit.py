import hashlib,json,math,random
from pathlib import Path
import torch
from stage2 import adaptive_recovery as a
from stage2 import sequential as seq
from stage2.kit_recovery import AdmissionRecoveryFactory
from stage2.spec import build
out=Path(__file__).parent;torch.set_num_threads(1);torch.manual_seed(619)
network=a.make_network(torch);policy=dict(kind='ppo',network=seq.export_network(network))
base=dict(wip_limit=8,qa_guard_threshold=4,worker_calendar=True,preposition=False,lease_calibration=True,selector='priority')
initial=AdmissionRecoveryFactory(build(12,seed=0),base).observation();rng=random.Random(890)
max_logp=max_value=0.;matched=0
for actor_seed in range(8):
 first=a.Controller(policy,base,actor_seed,False);second=a.Controller(policy,base,actor_seed,False)
 for segment in range(8):
  obs=dict(initial,tick=segment*720,completed_steps=rng.randrange(193),active_operations=rng.randrange(16),waiting_parts=rng.randrange(37),accepted_components=rng.randrange(37),shipped=rng.randrange(13),agvs_free=rng.randrange(5),workers_free=rng.randrange(11),energy_cost=rng.random()*1000)
  response=first(obs);perturbed=dict(obs,hidden_actual_seed=123456,future_quality_draw=.0001,future_urgent_orders=999)
  assert response==second(perturbed)
  step=first.trajectory[-1];x=torch.tensor([step['features']],dtype=torch.float32)
  with torch.no_grad():logits,value=network(x)
  logp=float(torch.log_softmax(logits,dim=-1)[0,step['action']]);critic=float(value[0])
  max_logp=max(max_logp,abs(logp-step['old_logp']));max_value=max(max_value,abs(critic-step['value']))
  assert abs(logp-step['old_logp'])<1e-6 and abs(critic-step['value'])<1e-6
  assert response['weights']['policy_seed']==actor_seed
  cached=first(dict(obs,tick=obs['tick']+60,shipped=999));assert cached==response
  assert len(first.trajectory)==segment+1
  deterministic=a.Controller(policy,base,actor_seed,True);deterministic(obs)
  with torch.no_grad():logits,_=network(torch.tensor([deterministic.trajectory[0]['features']],dtype=torch.float32))
  assert deterministic.trajectory[0]['action']==int(logits.argmax(-1)[0]);matched+=1
potential=[.1,.03,.24,.13];terminal=-9.183
assert math.isclose(sum(seq.trajectory_rewards(potential,terminal)),terminal,abs_tol=1e-12)
report=dict(cases=matched,numpy_torch_old_log_probability_max_abs_error=max_logp,numpy_torch_critic_max_abs_error=max_value,deterministic_argmax_all_match=True,paired_hidden_field_perturbation_all_match=True,macro_cache_does_not_append_pseudo_decisions=True,actor_seed_passed_to_weights=True,undiscounted_shaping_sum_matches_terminal=True,scope='Pure inference arithmetic/fuzz; no policy fit or factory tape execution',torch=torch.__version__,source_hashes=a.hashes())
(out/'inference-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
