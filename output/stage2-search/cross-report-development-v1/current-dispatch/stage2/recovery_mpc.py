"""Independent scenario lookahead over the physical kit-recovery scheduler.

Only dispatch weights change between continuations. The factory runtime class,
accepted-part locks, reservations, tool homes and admission history are copied
by the existing audited MPC continuation. No future of the real tape is read.
"""
from copy import deepcopy
import hashlib
from pathlib import Path
import time

from . import mpc
from .kit_recovery import RecoveryFactory,AdmissionRecoveryFactory

ROOT=Path(__file__).resolve().parents[1]
EXTRA_SOURCES=tuple('stage2/'+name+'.py' for name in
    ('recovery_mpc','advanced','specialist','tooling','admission','kitting','kit_recovery'))


def hashes():
    return dict(mpc.source_hashes(),**{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
        for name in EXTRA_SOURCES})


class GuardedRolloutController(mpc.RolloutController):
    def __init__(self,*args,**kwargs):
        self.extended_sources=hashes()
        super().__init__(*args,**kwargs)

    def __call__(self,observation):
        if hashes()!=self.extended_sources:raise RuntimeError('Recovery MPC source changed during execution')
        return super().__call__(observation)


def run(instance,weights=None,*,actions=None,scenarios=2,interval=1440,seed=27491,
        tool_policy=None,kit_reservation=True,admission=True,recovery_policy=None,
        risk_weight=.25,physical_check_futures=False):
    from .check import check_trace
    began=time.perf_counter();sources=hashes()
    cls=AdmissionRecoveryFactory if admission else RecoveryFactory
    factory=cls(instance,weights,tool_policy=tool_policy,kit_reservation=kit_reservation,
        recovery_policy=recovery_policy)
    if actions is None:
        # Narrow, explicit bank around the incumbent; all mode/quality/resource
        # semantics remain those of the unchanged numerical instance.
        actions=[dict(wip_limit=wip,qa_guard_threshold=guard)
            for wip in (4,6,8) for guard in (0,4)]
    controller=GuardedRolloutController(factory,actions=deepcopy(actions),scenarios=scenarios,
        interval=interval,seed=seed,risk_weight=risk_weight,
        physical_check_futures=physical_check_futures)
    factory.controller=controller;setup=time.perf_counter()-began
    trace=factory.run();check_began=time.perf_counter()
    trace['validation']=check_trace(trace,instance)
    trace['planning']=dict(method='recovery-backed-independent-scenario-rollout',
        decisions=controller.history,wall_seconds=sum(r['wall_seconds'] for r in controller.history),
        setup_wall_seconds=setup,final_check_wall_seconds=time.perf_counter()-check_began,
        total_run_wall_seconds=time.perf_counter()-began,source_hashes=sources,
        continuation_sha256=mpc.CONTINUATION_SHA256,physical_check_futures=physical_check_futures,
        risk_weight=risk_weight,actual_final_trace_valid=trace['validation']['valid'],
        disclosure='Classical causal lookahead; inherited commitments and recovery state preserved. Independent future seeds, not the real hidden tape. No full-model optimum or quantum advantage claim.')
    if hashes()!=sources:raise RuntimeError('Recovery MPC source changed during execution')
    return trace
