"""Frozen selected-policy evaluation; final execution is an explicit separate act.

There is no default final protocol or implicit evaluation. Freeze a selection
specification and explicit protocol first. Development protocols use only the
declared training/validation seeds; reserved final tapes require --execute-final.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
from copy import deepcopy
from fractions import Fraction
import hashlib
import itertools
from importlib import metadata
import json
import math
import multiprocessing
import os
from pathlib import Path
import platform
import time
import traceback
import sys

ROOT=Path(__file__).resolve().parents[1]
CORE=("stage2/engine.py","stage2/spec.py","stage2/check.py","stage2/dispatch.py",
      "stage2/qubo.py","stage2/quantum.py","instances/stage2/metaltech_pressure.json")
SOURCES=CORE+tuple("stage2/"+name+".py" for name in
    ("final_eval","statistics","threshold","sequential","advanced","specialist","mpc","energy","burnin","admission","tooling","kitting","kit_recovery","routing","recovery_routing","recovery_mpc","identity_audit","selector_reward","adaptive_recovery","adaptive_modes","completion_policy","bom_probe","maintenance_guard"))
SCHEMA="stage2-frozen-selected-policy-evaluation.v1"
DEVELOPMENT_SEEDS=set(range(32))|set(range(100,116))


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def file_hash(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def runtime_metadata():
    packages={}
    for name in ('numpy','scipy','torch','ortools','qiskit','qiskit-aer'):
        try:packages[name]=metadata.version(name)
        except metadata.PackageNotFoundError:packages[name]=None
    return dict(python=sys.version,platform=sys.platform,packages=packages,
        machine=platform.machine(),processor=platform.processor() or None,host_logical_cpus=os.cpu_count(),
        allocation={key:os.environ.get(key) for key in ('SLURM_JOB_ID','SLURM_CPUS_PER_TASK','SLURM_CPUS_ON_NODE')},
        threads={key:os.environ.get(key) for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')},
        scope='Installed distribution metadata only; unavailable packages are null, not required by the standard-library factory')


def source_hashes():return {name:file_hash(ROOT/name) for name in SOURCES}


def _sealed(value,key):
    answer=deepcopy(value);answer.pop(key,None)
    return digest(answer)


def validate_protocol(protocol,development=False):
    if development:
        if protocol.get('schema')!='stage2-development-protocol.v1' or protocol.get('seed_role')!='DEVELOPMENT':
            raise ValueError('Development execution requires an explicitly marked development protocol')
    elif protocol.get('schema')!='stage2-stratified-final-protocol.v1':
        raise ValueError('Final execution requires the predeclared stratified final protocol')
    expected=protocol.get('protocol_sha256');unsigned=deepcopy(protocol);unsigned.pop('protocol_sha256',None)
    # statistics.py originally used default JSON separators for this digest.
    actual=hashlib.sha256(json.dumps(unsigned,sort_keys=True).encode()).hexdigest()
    if expected!=actual:raise ValueError('Protocol digest changed')
    seen=set();mass=Fraction(0)
    for leaf in protocol['leaves']:
        probability=Fraction(*leaf['probability']);seeds=leaf['seeds']
        if not seeds or probability<=0:raise ValueError('Positive populated protocol leaves required')
        if abs(leaf['per_tape_weight']-float(probability/len(seeds)))>1e-14:
            raise ValueError('Incorrect per-tape probability weight')
        for seed in seeds:
            if type(seed) is not int or seed in seen:raise ValueError('Unique integer environment tapes required')
            if development and seed not in DEVELOPMENT_SEEDS:raise ValueError('Development seed outside 0–31/100–115')
            if not development and seed<10000:raise ValueError('Reserved final tapes start at 10000')
            seen.add(seed)
        mass+=probability
    if mass!=1 or len(seen)!=protocol['total_tapes']:raise ValueError('Protocol mass/count mismatch')
    return protocol


def development_protocol(seeds):
    """Explicit smoke protocol, never substitutes for a stratified final sample."""
    seeds=list(seeds)
    p=dict(schema='stage2-development-protocol.v1',seed_role='DEVELOPMENT',
        selection='Explicit development smoke tapes; no final performance claim',total_tapes=len(seeds),
        leaves=[dict(outcomes=['development'],probability=[1,1],seeds=seeds,per_tape_weight=1/len(seeds))])
    p['protocol_sha256']=hashlib.sha256(json.dumps(p,sort_keys=True).encode()).hexdigest()
    return validate_protocol(p,True)


def validate_model_protocol(protocol,configs):
    """Bind final probabilities and exogenous labels to the numerical model.

    Reads only the public stage definitions and keyed exogenous branch labels;
    it never executes a factory or inspects endogenous quality/solver outcomes.
    """
    from .spec import build
    from .statistics import branch
    declared={tuple(leaf['outcomes']):Fraction(*leaf['probability']) for leaf in protocol['leaves']}
    if len(declared)!=len(protocol['leaves']):raise ValueError('Duplicate final outcome leaves')
    for config in configs:
        stages=build(**config,seed=0)['uncertainty_stages'];expected={}
        for outcomes in itertools.product(*(stage['outcomes'] for stage in stages)):
            probability=Fraction(1)
            for outcome in outcomes:probability*=Fraction(*outcome['probability'])
            if probability:expected[tuple(o['id'] for o in outcomes)]=probability
        if declared!=expected:raise ValueError('Final protocol probability map differs from the numerical model')
        for leaf in protocol['leaves']:
            if any(branch(seed,stages)!=tuple(leaf['outcomes']) for seed in leaf['seeds']):
                raise ValueError('Final protocol seed has the wrong exogenous leaf')


def _verify_core(recorded):
    for name in CORE:
        if recorded.get(name)!=file_hash(ROOT/name):raise ValueError('Artifact physical source mismatch: '+name)


def _artifact_paths(method):
    result=[]
    for key in ('checkpoint','static_teacher'):
        if method.get(key):result.append(method[key])
    result.extend(method.get('threshold_bank',[]))
    return result


def _resolve_paths(method,base):
    answer=deepcopy(method)
    for key in ('checkpoint','static_teacher'):
        if answer.get(key):answer[key]=str((base/answer[key]).resolve())
    if 'threshold_bank' in answer:
        answer['threshold_bank']=[str((base/name).resolve()) for name in answer['threshold_bank']]
    return answer


def freeze(selection,protocol_path,output,*,development=False):
    """Freeze a concrete selection; does not run a simulator or inspect outcomes."""
    before=source_hashes()
    selection_path=Path(selection).resolve();selection_digest=file_hash(selection_path);spec=json.loads(selection_path.read_text())
    protocol_path=Path(protocol_path).resolve();protocol_digest=file_hash(protocol_path);protocol=json.loads(protocol_path.read_text())
    validate_protocol(protocol,development)
    if spec.get('schema')!='stage2-selected-policy-spec.v1':raise ValueError('Selected-policy specification required')
    if not spec.get('selection_provenance'):raise ValueError('Declare selection data, criterion and prior costs')
    configs=spec['configs'];actors=spec.get('actor_seeds',[900000]);methods=spec['methods']
    if not configs or not methods or not actors or len(set(actors))!=len(actors):raise ValueError('Nonempty unique actor seeds/configs/methods required')
    if any(type(a) is not int for a in actors):raise ValueError('Integer actor seeds required')
    if len({digest(c) for c in configs})!=len(configs):raise ValueError('Duplicate configurations')
    for config in configs:
        if set(config)!={'orders','horizon','profile'}:raise ValueError('Explicit orders/horizon/profile required')
    if not development:validate_model_protocol(protocol,configs)
    normalized=[];artifacts={};ids=set()
    for original in methods:
        method=_resolve_paths(original,selection_path.parent)
        if not method.get('id') or method['id'] in ids:raise ValueError('Unique selected method IDs required')
        if not method.get('selection_provenance'):raise ValueError('Every method needs selection/training-cost provenance')
        ids.add(method['id'])
        if method['kind'] in ('adaptive_recovery','adaptive_modes'):method=_normalize_adaptive(method)
        if type(method.get('maintenance_outage_guard',False)) is not bool:raise ValueError('Maintenance guard requires an explicit boolean')
        if method.get('maintenance_outage_guard') and (method['kind']=='mpc' or method.get('backend')=='burnin'):
            raise ValueError('Maintenance guard is not audited for legacy MPC or common burn-in')
        if method['kind']=='recovery_routing':method['kind']='recovery'
        if method['kind']=='recovery_mpc':method['backend']='recovery'
        if method['kind'] in ('advanced','specialist','tooling','kitting','recovery'):
            method['backend']=method['kind'];method['kind']='static'
        if method['kind'] not in ('static','context_static','threshold','sequential','mpc','recovery_mpc','adaptive_recovery','adaptive_modes'):raise ValueError('Unsupported policy kind')
        if 'reward_mode' in method or 'reward_mode_by_config' in method:
            from .selector_reward import MODES
            if method['kind'] in ('mpc','recovery_mpc','adaptive_recovery','adaptive_modes') or method.get('backend')=='burnin':
                raise ValueError('Reward composition requires an explicitly static/non-MPC dispatch backend')
            for config in method.get('configs',configs):
                if _context_option(method,'reward_mode',config) not in MODES:raise ValueError('Unknown selector reward')
        if 'completion_policy' in method or 'completion_policy_by_config' in method:
            if method['kind'] in ('mpc','recovery_mpc','adaptive_recovery','adaptive_modes') or method.get('backend')!='recovery':
                raise ValueError('Completion credit requires a static recovery backend')
            if 'reward_mode' in method or 'reward_mode_by_config' in method:
                raise ValueError('Completion/reward combination has not been audited')
        if method.get('backend','baseline') not in ('baseline','advanced','specialist','energy','burnin','tooling','kitting','recovery'):raise ValueError('Unsupported physical-preserving backend')
        if method.get('backend') in ('kitting','recovery'):
            method.setdefault('kit_reservation',True)
            if type(method['kit_reservation']) is not bool:raise ValueError('Explicit boolean kit_reservation required')
            if 'energy_policy' in method or 'energy_policy_by_config' in method:
                raise ValueError('Kitting uses the baseline battery; energy composition is not audited')
        elif 'kit_reservation' in method:
            raise ValueError('kit_reservation requires the explicitly selected kitting backend')
        if method.get('backend')!='recovery' and ('recovery_policy' in method or 'recovery_policy_by_config' in method):
            raise ValueError('recovery_policy requires the explicitly selected recovery backend')
        if method.get('backend')!='recovery' and ('routing_policy' in method or 'routing_policy_by_config' in method):
            raise ValueError('routing_policy requires the explicitly selected recovery backend')
        if method['kind']=='mpc' and method.get('backend','baseline')!='baseline':raise ValueError('MPC requires its audited baseline continuation')
        if method['kind'] in ('mpc','recovery_mpc') and len(actors)>1 and 'seed' in method.get('mpc',{}):
            raise ValueError('Replicated MPC requires actor-controlled planning seeds; remove fixed mpc.seed')
        if method['kind']=='recovery_mpc' and _artifact_paths(method):
            raise ValueError('Recovery MPC uses explicit inline actions; checkpoint banks are not supported')
        if type(method.get('admission',False)) is not bool:raise ValueError('Admission is an explicit boolean; ranking controls belong in weights')
        if method.get('admission') and (method['kind']=='mpc' or method.get('backend')=='burnin'):
            raise ValueError('Admission composition is not implemented for MPC or common burn-in; it cannot be silently ignored')
        for name in _artifact_paths(method):
            path=Path(name);artifact=json.loads(path.read_text());_verify_core(artifact['source_hashes'])
            artifacts[str(path)]=dict(sha256=file_hash(path),metadata={k:v for k,v in artifact.items()
                if k not in ('policy','actions','params','network')})
        # Construct every selected controller now to fail before final execution.
        applicable=method.get('configs',configs)
        if not applicable or any(config not in configs for config in applicable):raise ValueError('Method configurations must belong to declared contexts')
        for config in applicable:
            if method.get('backend')=='recovery':
                recovery=_context_option(method,'recovery_policy',config)
                if not isinstance(recovery,dict) or type(recovery.get('enabled')) is not bool:
                    raise ValueError('Recovery requires an explicit recovery_policy enabled boolean')
                if method.get('specialist') is not True or _context_option(method,'tool_policy',config) is None:
                    raise ValueError('Recovery requires the audited specialist and explicit tool-policy composition')
            weights,controller,_=_controller(method,config,actors[0])
            if method['kind']!='mpc' and method.get('backend')!='burnin':
                from .spec import build
                _dispatch_factory(build(**config,seed=0),weights,controller,method,config)
        normalized.append(method)
    if source_hashes()!=before:raise ValueError('Evaluation source changed while freezing selection')
    if file_hash(selection_path)!=selection_digest or file_hash(protocol_path)!=protocol_digest:
        raise ValueError('Specification/protocol changed while freezing selection')
    for path,record in artifacts.items():
        if file_hash(path)!=record['sha256']:raise ValueError('Artifact changed while freezing selection: '+path)
    manifest=dict(schema=SCHEMA,phase='frozen-selection',evaluation_role='development' if development else 'final',
        frozen_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),runtime=runtime_metadata(),configs=configs,actor_seeds=actors,
        methods=normalized,selection_provenance=spec['selection_provenance'],
        actor_seed_policy='Declared actor seed overrides inherited policy_seed before callback construction; explicit fixed MPC planning seeds permitted only with one actor',
        selection_spec=dict(path=str(selection_path),sha256=selection_digest),
        protocol=dict(path=str(protocol_path),file_sha256=protocol_digest,payload=protocol),
        artifacts=artifacts,source_hashes=before,
        trace_policy=spec.get('trace_policy','first_per_leaf'),
        statistics_scope='Actor replicas are conditional outcomes within environment clusters, never additional factories')
    if manifest['trace_policy'] not in ('none','first_per_leaf','all'):raise ValueError('Unknown trace retention policy')
    manifest['manifest_sha256']=_sealed(manifest,'manifest_sha256')
    path=Path(output);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as stream:stream.write(json.dumps(manifest,indent=2)+'\n')
    return manifest


def verify_manifest(manifest,execute_final=False):
    if manifest.get('schema')!=SCHEMA or manifest.get('phase')!='frozen-selection':raise ValueError('Frozen policy selection required')
    if manifest.get('manifest_sha256')!=_sealed(manifest,'manifest_sha256'):raise ValueError('Frozen manifest changed')
    role=manifest['evaluation_role']
    if role not in ('development','final'):raise ValueError('Unknown evaluation role')
    if role=='final' and not execute_final:raise ValueError('Reserved final tapes require explicit --execute-final after selection freeze')
    validate_protocol(manifest['protocol']['payload'],role=='development')
    if file_hash(manifest['protocol']['path'])!=manifest['protocol']['file_sha256']:raise ValueError('Protocol file changed')
    if file_hash(manifest['selection_spec']['path'])!=manifest['selection_spec']['sha256']:raise ValueError('Selection specification changed')
    if source_hashes()!=manifest['source_hashes']:raise ValueError('Frozen evaluation source changed')
    for path,record in manifest['artifacts'].items():
        if file_hash(path)!=record['sha256']:raise ValueError('Frozen checkpoint changed: '+path)


def _load(path):return json.loads(Path(path).read_text())


def _context(artifact,config):
    try:return artifact['configs'].index(config)
    except ValueError as exc:raise ValueError('Selected artifact lacks requested measured configuration') from exc


def _adaptive_artifact(path,kind='adaptive_recovery'):
    """Require the exact measured six/eighteen-action inference contract."""
    if kind=='adaptive_recovery':from . import adaptive_recovery as a
    elif kind=='adaptive_modes':from . import adaptive_modes as a
    else:raise ValueError('Unknown adaptive inference implementation')
    from .sequential import FEATURE_NAMES
    artifact=_load(path);_verify_core(artifact['source_hashes'])
    schema='stage2-adaptive-modes-policy.v1' if kind=='adaptive_modes' else 'stage2-adaptive-recovery-policy.v1'
    if artifact.get('schema')!=schema:raise ValueError('Matching adaptive policy artifact required')
    if kind=='adaptive_modes' and (artifact.get('maintenance_outage_guard') is not True or artifact.get('identity_supplement') is not True):
        raise ValueError('Measured adaptive modes require the causal maintenance guard and identity supplement')
    if artifact['source_hashes']!=a.hashes():raise ValueError('Adaptive recovery inference source mismatch')
    if artifact.get('actions')!=list(a.ACTIONS) or artifact.get('feature_names')!=list(FEATURE_NAMES):
        raise ValueError('Adaptive recovery action/feature contract changed')
    if artifact.get('interval')!=720:raise ValueError('Expected measured 720-minute macro interval')
    contexts=artifact['contexts'];policies=artifact['policies_by_context']
    if not contexts or len(contexts)!=len(policies) or artifact['configs']!=[c['config'] for c in contexts]:
        raise ValueError('Adaptive recovery context/policy mismatch')
    import numpy as np
    shapes={'first.weight':(64,len(FEATURE_NAMES)),'first.bias':(64,),
        'second.weight':(64,64),'second.bias':(64,),'actor.weight':(len(a.ACTIONS),64),'actor.bias':(len(a.ACTIONS),),
        'critic.weight':(1,64),'critic.bias':(1,)}
    for policy in policies:
        if policy['kind']=='static':actions=[policy['action']]
        elif policy['kind']=='schedule':
            actions=policy['schedule']
            if len(actions)!=8:raise ValueError('Expected measured eight-segment schedule')
        elif policy['kind']=='ppo':
            actions=[]
            if set(policy['network'])!=set(shapes):raise ValueError('Adaptive network parameter contract changed')
            for key,shape in shapes.items():
                value=np.asarray(policy['network'][key],dtype=np.float32)
                if value.shape!=shape or not np.isfinite(value).all():raise ValueError('Invalid adaptive network tensor: '+key)
        else:raise ValueError('Unsupported adaptive recovery policy')
        if any(type(action) is not int or not 0<=action<len(a.ACTIONS) for action in actions):raise ValueError('Adaptive action outside measured domain')
    return artifact


def _normalize_adaptive(method):
    """Derive decoder options from the checkpoint; forbid silent inference changes."""
    artifact=_adaptive_artifact(method['checkpoint'],method['kind']);answer=deepcopy(method)
    allowed={'id','kind','checkpoint','selection_provenance','configs','deterministic','maintenance_outage_guard'}
    if set(answer)-allowed:raise ValueError('Adaptive decoder/options must come from its measured checkpoint')
    if answer.get('deterministic',True) is not True:raise ValueError('Adaptive checkpoint selection used deterministic inference')
    answer.update(backend='recovery',specialist=True,deterministic=True)
    if method['kind']=='adaptive_modes':
        if method.get('maintenance_outage_guard',True) is not True:raise ValueError('Adaptive modes cannot disable their measured guard')
        answer['maintenance_outage_guard']=True
    applicable=answer.get('configs',artifact['configs'])
    contexts=[artifact['contexts'][_context(artifact,c)] for c in applicable]
    if any(set(c['solver_options'])-{'tool_policy','kit_reservation','admission','recovery_policy','routing_policy'} for c in contexts):
        raise ValueError('Unsupported adaptive checkpoint decoder option')
    for key,default in (('admission',False),('kit_reservation',True)):
        values=[c['solver_options'].get(key,default) for c in contexts]
        if not values or any(type(v) is not bool or v!=values[0] for v in values):raise ValueError('Adaptive contexts require a shared explicit '+key)
        answer[key]=values[0]
    for key in ('tool_policy','recovery_policy','routing_policy'):
        answer[key+'_by_config']=[dict(config=c['config'],**{key:c['solver_options'].get(key)}) for c in contexts]
    return answer


def _controller(method,config,actor_seed):
    """Return initial weights, causal callback, and explicit version adaptations."""
    kind=method['kind'];weights=deepcopy(method.get('weights',{}));controller=None;adapters=[]
    if 'weights_by_config' in method:
        selected=[entry['weights'] for entry in method['weights_by_config'] if entry['config']==config]
        if len(selected)!=1:raise ValueError('Exactly one static weight selection per requested configuration required')
        weights.update(selected[0])
    # Actor replicas must also reach callback base weights, not just initial
    # factory weights. Training artifacts can carry a fixed policy_seed=0.
    weights['policy_seed']=actor_seed
    if kind=='context_static':
        artifact=_load(method['checkpoint']);_verify_core(artifact['source_hashes'])
        if artifact['policy']['kind']!='context_static':raise ValueError('Context-static artifact required')
        idx=_context(artifact,config);action=artifact['policy']['actions'][idx]
        weights={**artifact.get('base_weights',{}),**artifact['actions'][action]['weights'],**weights}
    elif kind=='threshold':
        from .threshold import Controller,adapt_checkpoint,assert_sources
        artifact=_load(method['checkpoint']);_verify_core(artifact['source_hashes'])
        try:assert_sources(artifact['source_hashes'])
        except RuntimeError:
            if not method.get('adapt_threshold',False):raise
            artifact=adapt_checkpoint(artifact);adapters.append(artifact['controller_adapter'])
        controller=Controller(artifact['params'][_context(artifact,config)],dict(artifact.get('base_weights',{}),**weights))
    elif kind=='sequential':
        from .sequential import Controller,check_sources,adapt_evaluation_checkpoint
        artifact=_load(method['checkpoint']);_verify_core(artifact['source_hashes'])
        try:check_sources(artifact['source_hashes'])
        except RuntimeError:
            if not method.get('adapt_learner',False):raise
            artifact=adapt_evaluation_checkpoint(artifact);adapters.append(artifact['evaluation_adapter'])
        policy=artifact['policy']
        if policy['kind']=='context_static':policy=dict(kind='static',action=policy['actions'][_context(artifact,config)])
        elif policy['kind']=='context_schedule':policy=dict(kind='schedule',schedule=policy['schedules'][_context(artifact,config)])
        controller=Controller(policy,actor_seed,method.get('deterministic',True),dict(artifact.get('base_weights',{}),**weights))
    elif kind in ('adaptive_recovery','adaptive_modes'):
        if kind=='adaptive_recovery':from .adaptive_recovery import Controller
        else:from .adaptive_modes import Controller
        artifact=_adaptive_artifact(method['checkpoint'],kind);idx=_context(artifact,config)
        weights=dict(artifact['contexts'][idx]['weights'],policy_seed=actor_seed)
        controller=Controller(artifact['policies_by_context'][idx],weights,actor_seed,True,artifact['interval'])
        if kind=='adaptive_recovery' and method.get('maintenance_outage_guard'):
            adapters.append(dict(kind='explicit-maintenance-availability-restriction',
                inference='Original measured policy unchanged; execution excludes maintenance overlapping public/observed machine outage support',
                development_replay_required=True))
    elif kind=='mpc':
        from .spec import build
        from .mpc import load_static_teacher,load_threshold_bank
        # Pure construction/contract checks on a development-seeded instance;
        # freezing never executes the reserved factory tapes.
        instance=build(**config,seed=0)
        if method.get('static_teacher'):load_static_teacher(method['static_teacher'],instance)
        if method.get('threshold_bank'):
            bank=load_threshold_bank(method['threshold_bank'],instance,method.get('adapt_threshold',False))
            adapters.extend(p['provenance'].get('threshold_adapter') for p in bank
                            if p['provenance'].get('threshold_adapter'))
    # A fixed independent actor seed controls any explicit dispatch randomization.
    # Environment seeds never enter the callback's policy RNG.
    weights['policy_seed']=actor_seed
    return weights,controller,adapters


def _context_option(method,key,config,default=None):
    result=deepcopy(method.get(key,default))
    if key+'_by_config' in method:
        matches=[entry[key] for entry in method[key+'_by_config'] if entry['config']==config]
        if len(matches)!=1:raise ValueError('Exactly one '+key+' per requested configuration required')
        result=deepcopy(matches[0])
    return result


def _dispatch_factory(instance,weights,controller,method,config):
    """Compose algorithm restrictions explicitly; no numerical instance mutation."""
    backend=method.get('backend','baseline');admission=method.get('admission',False)
    if backend=='recovery':
        kwargs=dict(tool_policy=_context_option(method,'tool_policy',config),
            kit_reservation=method.get('kit_reservation',True),
            recovery_policy=_context_option(method,'recovery_policy',config))
        routing=_context_option(method,'routing_policy',config)
        if routing is None:
            from .kit_recovery import RecoveryFactory,AdmissionRecoveryFactory
            cls=AdmissionRecoveryFactory if admission else RecoveryFactory
        else:
            from .recovery_routing import RecoveryRoutingFactory,AdmissionRecoveryRoutingFactory
            cls=AdmissionRecoveryRoutingFactory if admission else RecoveryRoutingFactory
            kwargs['routing_policy']=routing
        admission=False
    elif backend=='kitting':
        from .kitting import (KitFactory,KitSpecialistFactory,KitToolingFactory,KitToolingSpecialistFactory,
            AdmissionKitFactory,AdmissionKitSpecialistFactory,AdmissionKitToolingFactory,AdmissionKitToolingSpecialistFactory)
        policy=_context_option(method,'tool_policy',config)
        classes={(False,False,False):KitFactory,(False,True,False):KitSpecialistFactory,
            (True,False,False):KitToolingFactory,(True,True,False):KitToolingSpecialistFactory,
            (False,False,True):AdmissionKitFactory,(False,True,True):AdmissionKitSpecialistFactory,
            (True,False,True):AdmissionKitToolingFactory,(True,True,True):AdmissionKitToolingSpecialistFactory}
        cls=classes[(policy is not None,bool(method.get('specialist',False)),admission)]
        kwargs=dict(kit_reservation=method.get('kit_reservation',True))
        if policy is not None:kwargs['tool_policy']=policy
        admission=False  # The selected explicit root composition already owns it.
    elif backend=='tooling':
        from .tooling import ToolingFactory,ToolingSpecialistFactory
        cls=ToolingSpecialistFactory if method.get('specialist',False) else ToolingFactory
        kwargs=dict(tool_policy=_context_option(method,'tool_policy',config))
    elif backend=='energy':
        from .energy import EnergyFactory,EnergyAdvancedFactory
        cls=EnergyAdvancedFactory if method.get('advanced',False) else EnergyFactory
        kwargs=dict(energy_policy=_context_option(method,'energy_policy',config))
    else:
        from .engine import Factory
        from .advanced import AdvancedFactory
        from .specialist import SpecialistFactory
        cls=dict(baseline=Factory,advanced=AdvancedFactory,specialist=SpecialistFactory)[backend];kwargs={}
    if admission:
        from .admission import AdmissionMixin
        # Scenario deepcopy keeps this object's exact runtime class and its
        # AdmissionSet backlink. The class changes only persistent WIP ranking.
        cls=type('SelectedAdmission'+cls.__name__,(AdmissionMixin,cls),{})
    if method.get('maintenance_outage_guard',False):
        from .maintenance_guard import MaintenanceOutageGuardMixin
        cls=type('SelectedMaintenanceGuard'+cls.__name__,(MaintenanceOutageGuardMixin,cls),{})
        kwargs['maintenance_outage_guard']=True
    reward=_context_option(method,'reward_mode',config)
    if reward is not None:
        from .selector_reward import RewardMixin
        cls=type('SelectedReward'+cls.__name__,(RewardMixin,cls),{})
        kwargs['reward_mode']=reward
    completion=_context_option(method,'completion_policy',config)
    if completion is not None:
        from .completion_policy import CompletionMixin
        cls=type('SelectedCompletion'+cls.__name__,(CompletionMixin,cls),{})
        kwargs['completion_policy']=completion
    return cls(instance,weights,controller,**kwargs)


class TimedController:
    def __init__(self,handler):self.handler=handler;self.wall_seconds=0.;self.cpu_seconds=0.;self.calls=0
    def __call__(self,observation):
        wall=time.perf_counter();cpu=time.process_time()
        try:return self.handler(observation)
        finally:
            self.wall_seconds+=time.perf_counter()-wall;self.cpu_seconds+=time.process_time()-cpu;self.calls+=1


def qubo_telemetry(trace):
    """Count recorded execution evidence; a request is not a simulated circuit.

    Coupling means at least one nonzero quadratic coefficient in the encoded
    QUBO, including any slack bits. Repair is solver-side feasibility repair;
    selected/committed mismatch is a separate decoder failure, never a repair.
    """
    counters=dict(calls=0,coupled_calls=0,qaoa_requested_calls=0,qaoa_calls=0,
        coupled_qaoa_calls=0,uncoupled_qaoa_calls=0,qaoa_calls_unknown_coupling=0,trivial_1bit_qaoa_calls=0,
        fallback_calls=0,classical_fallback_calls=0,oversize_classical_fallback_calls=0,
        qaoa_oversize_classical_fallback_calls=0,empty_pool_calls=0,repairs=0,
        decode_mismatches=0,physical_quantum_calls=0,
        max_total_bits=0,max_core_bits=0,max_slack_bits=0,max_couplers=0,
        max_actual_simulated_quantum_bits=0,simulated_over_5bit_calls=0,
        missing_size_metadata_calls=0,simulated_calls_missing_circuit_size=0)
    totals={};simulated_sizes={};mismatches=[]
    result_elapsed=[];angle_elapsed=[]
    for decision in trace.get('qubo_decisions',[]):
        counters['calls']+=1;result=decision['result'];summary=result.get('qubo',{})
        sizes=[summary.get(key) for key in ('variables','core_variables','slack_variables','couplers')]
        if any(value is None for value in sizes):counters['missing_size_metadata_calls']+=1
        for key,value in zip(('max_total_bits','max_core_bits','max_slack_bits','max_couplers'),sizes):
            if value is not None:counters[key]=max(counters[key],value)
        total,_,_,couplers=sizes
        if total is not None:totals[str(total)]=totals.get(str(total),0)+1
        coupled=couplers is not None and couplers>0
        simulated=result.get('quantum_algorithm_simulated') is True
        requested=result.get('requested_method')=='qaoa'
        physical=result.get('physical_quantum_executed') is True
        empty=result.get('method')=='classical_empty_pool'
        fallback=bool(result.get('fallback_reason')) and not empty
        classical_fallback=fallback and not simulated and not physical
        counters['coupled_calls']+=coupled;counters['qaoa_requested_calls']+=requested
        counters['qaoa_calls']+=simulated;counters['coupled_qaoa_calls']+=simulated and coupled
        counters['uncoupled_qaoa_calls']+=simulated and couplers==0
        counters['qaoa_calls_unknown_coupling']+=simulated and couplers is None
        counters['physical_quantum_calls']+=physical;counters['empty_pool_calls']+=empty
        counters['fallback_calls']+=fallback;counters['classical_fallback_calls']+=classical_fallback
        oversize=classical_fallback and total is not None and total>5
        counters['oversize_classical_fallback_calls']+=oversize
        counters['qaoa_oversize_classical_fallback_calls']+=oversize and requested
        counters['repairs']+=result.get('repaired') is True
        sampling=result.get('sampling',{})
        if simulated:
            bits=sampling.get('circuit',{}).get('qubits')
            if bits is None:counters['simulated_calls_missing_circuit_size']+=1
            else:
                counters['max_actual_simulated_quantum_bits']=max(counters['max_actual_simulated_quantum_bits'],bits)
                counters['trivial_1bit_qaoa_calls']+=bits==1
                counters['simulated_over_5bit_calls']+=bits>5
                simulated_sizes[str(bits)]=simulated_sizes.get(str(bits),0)+1
        if result.get('elapsed_seconds') is not None:result_elapsed.append(result['elapsed_seconds'])
        optimization=sampling.get('optimization',{})
        if optimization.get('elapsed_seconds') is not None:angle_elapsed.append(optimization['elapsed_seconds'])
        selected=result.get('selected');committed=decision.get('committed')
        if selected is None or committed is None or sorted(selected)!=sorted(committed):
            counters['decode_mismatches']+=1
            mismatches.append(dict(code='qubo_decode_commit_mismatch',tick=decision.get('tick'),
                selected=selected,committed=committed,
                disclosure='Recorded selected candidate IDs must equal actual committed IDs; this is not solver feasibility repair'))
    counters.update(total_encoded_bit_histogram=totals,actual_simulated_quantum_bit_histogram=simulated_sizes,
        decode_mismatch_evidence=mismatches,
        time_breakdown_seconds=dict(result_elapsed_seconds_sum=sum(result_elapsed),
            result_elapsed_observed_calls=len(result_elapsed),
            qaoa_angle_optimization_elapsed_seconds_sum=sum(angle_elapsed),
            qaoa_angle_optimization_observed_calls=len(angle_elapsed),
            encoding_seconds=None,isolated_solver_seconds=None,decoding_seconds=None,
            scope='Only literal result.elapsed_seconds and sampling.optimization.elapsed_seconds are recorded. Original result timing has method-dependent scope: QAOA requests, including oversize SA fallback, begin after encoding; ordinary classical select paths include encoding. Angle optimization is a nested subset, not additional time. Separate encoding/solver/decoding timings are unavailable.'),
        definitions=dict(qaoa_calls='Actual quantum_algorithm_simulated=true records, not requests or classical fallbacks',
            coupled_calls='Nonzero encoded QUBO couplers, including slack-variable couplings',
            coupled_qaoa_calls='Intersection of actual simulated QAOA and coupled encoded QUBOs',
            fallback_calls='Nonempty fallback_reason excluding explicit empty-pool no-circuit calls; can overlap actual QAOA if classical postprocessing repairs its samples',
            max_actual_simulated_quantum_bits='Circuit qubits from actual simulation metadata, never size of an oversize classical fallback',
            repairs='Solver-reported feasibility repair only; decode mismatches independently invalidate the row'))
    return counters


def _execute(task):
    """One measured execution; failures remain rows rather than being discarded."""
    from .spec import build
    from .check import check_trace
    started=time.perf_counter();cpu_started=time.process_time();trace=None;simulation_start=None
    row={k:task[k] for k in ('method_id','config','seed','policy_seed','leaf','leaf_outcomes','tape_id','tape_weight')}
    row.update(schema='stage2-selected-policy-row.v1',valid=False,metrics=None,
        physical_instance_sha256=None,issues=[],
        manifest_sha256=task['manifest_sha256'],protocol_sha256=task['protocol_sha256'],
        checker_sha256=task['sources']['stage2/check.py'],checkpoint_sha256=task['artifact_hashes'],
        selection_and_training_cost_reference=dict(manifest_sha256=task['manifest_sha256'],method_id=task['method_id']))
    try:
        # Every worker checks sources and referenced artifacts before execution.
        if source_hashes()!=task['sources']:raise RuntimeError('Evaluation source changed in worker')
        for path,expected in task['artifact_hashes'].items():
            if file_hash(path)!=expected:raise RuntimeError('Checkpoint changed in worker: '+path)
        instance=build(**task['config'],seed=task['seed']);anchor=deepcopy(instance)
        row['physical_instance_sha256']=digest(anchor)
        method=task['method'];weights,controller,adapters=_controller(method,task['config'],task['policy_seed'])
        timed=TimedController(controller) if controller is not None else None
        controller=timed
        simulation_start=time.perf_counter()
        if method['kind']=='recovery_mpc':
            from .recovery_mpc import run
            options=deepcopy(method.get('mpc',{}));options.setdefault('seed',task['policy_seed'])
            trace=run(instance,weights,tool_policy=_context_option(method,'tool_policy',task['config']),
                kit_reservation=method['kit_reservation'],admission=method.get('admission',False),
                recovery_policy=_context_option(method,'recovery_policy',task['config']),
                routing_policy=_context_option(method,'routing_policy',task['config']),
                maintenance_outage_guard=method.get('maintenance_outage_guard',False),**options)
        elif method['kind']=='mpc':
            from .mpc import run
            options=deepcopy(method.get('mpc',{}));options.setdefault('seed',task['policy_seed'])
            trace=run(instance,weights,static_teacher=method.get('static_teacher'),
                threshold_bank=method.get('threshold_bank'),adapt_threshold=method.get('adapt_threshold',False),**options)
        else:
            backend=method.get('backend','baseline')
            if backend=='burnin':
                from .burnin import run
                bundle=run(instance,weights,controller,boundary_tick=method.get('boundary_tick',480),
                    prefix_weights=method.get('prefix_weights'),method_id=method['id'])
                trace=bundle['trace'];row['burnin_verification']=bundle['verification']
            else:
                trace=_dispatch_factory(instance,weights,controller,method,task['config']).run()
        row['simulation_wall_seconds']=time.perf_counter()-simulation_start
        check_start=time.perf_counter();checked=check_trace(trace,anchor)
        row.update(checker_wall_seconds=time.perf_counter()-check_start,valid=checked['valid'],issues=checked['issues'],
            metrics=trace['metrics'],adapters=adapters,planning_wall_seconds=trace.get('planning',{}).get('wall_seconds',0.),
            controller_decisions=len(trace.get('decisions',[])),measured_execution=True)
        row['terminal_requirements_met']=checked.get('terminal_requirements_met',False)
        if not row['terminal_requirements_met']:
            row['valid']=False;row['issues'].append(dict(code='terminal_requirements_unmet'))
        from .identity_audit import audit_trace
        row['identity_audit']=audit_trace(trace,anchor)
        if not row['identity_audit']['valid']:
            row['valid']=False;row['issues'].extend(row['identity_audit']['issues'])
        row['executed_instance_sha256']=digest(trace.get('instance'))
        if row['executed_instance_sha256']!=row['physical_instance_sha256']:
            row['valid']=False;row['issues'].append(dict(code='frozen_instance_changed'))
        if trace.get('horizon_ticks')!=anchor['horizon_ticks'] or trace.get('tick_minutes')!=anchor['tick_minutes']:
            row['valid']=False;row['issues'].append(dict(code='frozen_execution_horizon_or_units_changed'))
        independent=checked.get('metrics',{})
        row['checker_metrics']=independent
        verified=dict(orders=independent.get('delivered_orders',0)+independent.get('unfulfilled_orders',0),
            shipped=independent.get('delivered_orders'),total_tardiness_ticks=independent.get('terminal_deadline_debt_ticks'),
            all_orders_fulfilled=checked.get('all_orders_fulfilled'),
            terminal_soc_satisfied=checked.get('terminal_requirements_met'))
        for key,expected in verified.items():
            if trace['metrics'].get(key)!=expected:
                row['valid']=False;row['issues'].append(dict(code='independent_metric_mismatch',metric=key,
                    reported=trace['metrics'].get(key),independent=expected))
        row['independently_reconstructed_outcome']=verified
        for key in ('total_cost','carbon_kg','grid_kwh','terminal_soc'):
            reported=trace['metrics'].get(key);expected=independent.get(key)
            if not isinstance(reported,(int,float)) or not isinstance(expected,(int,float)) or not math.isclose(reported,expected,rel_tol=1e-9,abs_tol=1e-5):
                row['valid']=False;row['issues'].append(dict(code='independent_metric_mismatch',metric=key,
                    reported=reported,independent=expected))
        row['qubo_telemetry']=qubo_telemetry(trace)
        if row['qubo_telemetry']['decode_mismatches']:
            row['valid']=False;row['issues'].extend(row['qubo_telemetry']['decode_mismatch_evidence'])
        row.update(controller_inference_wall_seconds=timed.wall_seconds if timed else 0.,
            controller_inference_cpu_seconds=timed.cpu_seconds if timed else 0.,
            controller_cost_scope='Callback cost for non-MPC policy; MPC costs recorded separately as planning_wall_seconds')
        if row.get('burnin_verification',{}).get('valid') is False:
            row['valid']=False;row['issues'].append(dict(code='burnin_bundle_verification_failed'))
        if task['expected_outcomes'] is not None:
            actual=[r['outcome'] for r in trace['audit']['realized_stages']]
            if actual!=task['expected_outcomes']:
                row['valid']=False;row['issues'].append(dict(code='protocol_leaf_mismatch',actual=actual,expected=task['expected_outcomes']))
        if source_hashes()!=task['sources']:raise RuntimeError('Evaluation source changed during episode')
    except Exception as exc:
        row.update(valid=False,error=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc()))
    row.setdefault('simulation_wall_seconds',time.perf_counter()-simulation_start if simulation_start is not None else 0.)
    row.setdefault('checker_wall_seconds',0.);row.setdefault('planning_wall_seconds',0.)
    row.update(wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu_started)
    if trace is not None and (task['save_trace'] or not row['valid']):
        path=Path(task['trace_path']);path.parent.mkdir(parents=True,exist_ok=True)
        trace['validation']=dict(valid=row['valid'],issues=row.get('issues',[]))
        with path.open('x') as stream:stream.write(json.dumps(trace)+'\n')
        row['trace_path']=str(path);row['trace_sha256']=file_hash(path)
    return row


def tasks(manifest,output):
    protocol=manifest['protocol']['payload'];result=[];output=Path(output)
    for mi,method in enumerate(manifest['methods']):
        hashes={path:manifest['artifacts'][path]['sha256'] for path in _artifact_paths(method)}
        for ci,config in enumerate(manifest['configs']):
            if config not in method.get('configs',manifest['configs']):continue
            for li,leaf in enumerate(protocol['leaves']):
                for si,seed in enumerate(leaf['seeds']):
                    for ai,actor in enumerate(manifest['actor_seeds']):
                        save=manifest['trace_policy']=='all' or (manifest['trace_policy']=='first_per_leaf' and si==0 and ai==0)
                        result.append(dict(method_id=method['id'],method=method,config=config,seed=seed,policy_seed=actor,
                            leaf=li,leaf_outcomes=leaf['outcomes'],expected_outcomes=None if manifest['evaluation_role']=='development' else leaf['outcomes'],
                            tape_id=f'leaf-{li}:seed-{seed}',tape_weight=leaf['per_tape_weight'],
                            manifest_sha256=manifest['manifest_sha256'],protocol_sha256=protocol['protocol_sha256'],
                            sources=manifest['source_hashes'],artifact_hashes=hashes,save_trace=save,
                            trace_path=str(output/'traces'/f'method-{mi}-config-{ci}-leaf-{li}-seed-{seed}-actor-{actor}.json')))
    return result


def summarize(rows,manifest):
    from .statistics import clustered_rows,weighted_mean,weighted_cvar
    output=[];protocol=manifest['protocol']['payload']
    for method in manifest['methods']:
        for config in manifest['configs']:
            if config not in method.get('configs',manifest['configs']):continue
            selected=[r for r in rows if r['method_id']==method['id'] and r['config']==config]
            group=dict(method_id=method['id'],config=config,rows=len(selected),invalid=sum(not r['valid'] for r in selected),
                unique_environment_tapes=len({r['seed'] for r in selected}),actor_replicas=len(manifest['actor_seeds']))
            expected=protocol['total_tapes']*len(manifest['actor_seeds'])
            group['expected_rows']=expected
            if len(selected)==expected and not group['invalid']:
                group['metrics']={}
                for key in ('unfulfilled','total_tardiness_ticks','total_cost','carbon_kg'):
                    metric=(lambda r:r['metrics']['orders']-r['metrics']['shipped']) if key=='unfulfilled' else lambda r,k=key:r['metrics'][k]
                    clustered=clustered_rows(selected,protocol,metric)
                    joint_weights=[r['tape_weight']/len(manifest['actor_seeds']) for r in selected]
                    group['metrics'][key]=dict(mean=weighted_mean([r['value'] for r in clustered],[r['weight'] for r in clustered]),
                        actor_mean_environment_cvar90=weighted_cvar([r['value'] for r in clustered],[r['weight'] for r in clustered]),
                        joint_actor_environment_cvar90=weighted_cvar([metric(r) for r in selected],joint_weights))
                complete=clustered_rows(selected,protocol,lambda r:float(r['metrics']['all_orders_fulfilled']))
                group['probability_all_orders_fulfilled']=weighted_mean([r['value'] for r in complete],[r['weight'] for r in complete])
            else:group['performance_suppressed']='Invalid or missing executions retained; no valid-only cherry picking'
            output.append(group)
    return output


def evaluate(manifest_path,output,workers=32,*,execute_final=False):
    manifest=_load(manifest_path);verify_manifest(manifest,execute_final)
    if workers<1:raise ValueError('Positive worker count required')
    target=Path(output).resolve();target.mkdir(parents=True,exist_ok=False)
    (target/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    started=time.perf_counter();rows=[];work=tasks(manifest,target)
    with (target/'rows.jsonl').open('x') as log:
        if workers==1:
            iterator=map(_execute,work)
            for row in iterator:rows.append(row);log.write(json.dumps(row)+'\n');log.flush()
        else:
            with ProcessPoolExecutor(max_workers=workers,mp_context=multiprocessing.get_context('spawn')) as pool:
                pending={pool.submit(_execute,t):t for t in work}
                for future in as_completed(pending):
                    task=pending[future]
                    try:row=future.result()
                    except Exception as exc:
                        row={k:task[k] for k in ('method_id','config','seed','policy_seed','leaf','leaf_outcomes','tape_id','tape_weight')}
                        row.update(schema='stage2-selected-policy-row.v1',valid=False,metrics=None,issues=[],
                            physical_instance_sha256=None,checker_sha256=task['sources']['stage2/check.py'],
                            checkpoint_sha256=task['artifact_hashes'],protocol_sha256=task['protocol_sha256'],
                            simulation_wall_seconds=None,checker_wall_seconds=None,planning_wall_seconds=None,
                            wall_seconds=None,cpu_seconds=0.,cost_disclosure='Worker failure; consumed cost unmeasured, not asserted zero',
                            error=dict(type=type(exc).__name__,message=str(exc)),manifest_sha256=manifest['manifest_sha256'])
                    rows.append(row);log.write(json.dumps(row)+'\n');log.flush()
    verify_manifest(manifest,execute_final)
    rows.sort(key=lambda r:(r['method_id'],digest(r['config']),r['leaf'],r['seed'],r['policy_seed']))
    result=dict(schema=SCHEMA,manifest_sha256=manifest['manifest_sha256'],evaluation_role=manifest['evaluation_role'],
        protocol_sha256=manifest['protocol']['payload']['protocol_sha256'],expected_rows=len(work),actual_rows=len(rows),
        rows=rows,summary=summarize(rows,manifest),wall_seconds=time.perf_counter()-started,
        measured_cpu_seconds=sum(r.get('cpu_seconds',0.) for r in rows),runtime=runtime_metadata(),
        unmeasured_worker_failures=sum(r.get('cost_disclosure') is not None for r in rows),
        missing_or_invalid=sum(not r['valid'] for r in rows),source_hashes=manifest['source_hashes'],
        inference_cost_scope='Per-row simulation wall and process CPU include causal callbacks and all MPC futures; checker wall separate',
        training_cost_scope='Immutable method selection_provenance and artifact metadata in manifest; report once or explicitly amortize',
        statistical_scope='Separate actor-mean environment CVaR and joint actor/environment CVaR; actors remain nested within factories')
    with (target/'evaluation.json').open('x') as stream:stream.write(json.dumps(result,indent=2)+'\n')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    f=sub.add_parser('freeze');f.add_argument('--selection',type=Path,required=True);f.add_argument('--protocol',type=Path,required=True)
    f.add_argument('--output',type=Path,required=True);f.add_argument('--development',action='store_true')
    e=sub.add_parser('run');e.add_argument('--manifest',type=Path,required=True);e.add_argument('--output',type=Path,required=True)
    e.add_argument('--workers',type=int,default=32);e.add_argument('--execute-final',action='store_true')
    d=sub.add_parser('development-protocol');d.add_argument('--seeds',required=True);d.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.command=='freeze':
        result=freeze(a.selection,a.protocol,a.output,development=a.development)
        print(json.dumps(dict(manifest_sha256=result['manifest_sha256'],role=result['evaluation_role'],simulations_executed=0)))
    elif a.command=='run':
        result=evaluate(a.manifest,a.output,a.workers,execute_final=a.execute_final)
        print(json.dumps({k:result[k] for k in ('actual_rows','missing_or_invalid','wall_seconds','summary')}))
    else:
        protocol=development_protocol(int(s) for s in a.seeds.split(','))
        with a.output.open('x') as stream:stream.write(json.dumps(protocol,indent=2)+'\n')


if __name__=='__main__':main()
