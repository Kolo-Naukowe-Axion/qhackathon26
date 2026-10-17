import json
from pathlib import Path
import tempfile
import unittest
from copy import deepcopy

from stage2.adaptive_recovery import Controller
from stage2.check import check_trace,check_paired_causality
from stage2.hybrid_schedule import load_checkpoint,construct,tasks,telemetry,digest,simulate,hashes
from stage2.maintenance_guard import AdmissionMaintenanceGuardFactory
from stage2.selector_reward import reward_override
from stage2.spec import build

CHECKPOINT=Path(__file__).resolve().parents[2]/'output/stage2-search/final-preparation/checkpoints/strong-cem6-2026.json'


class HybridScheduleTests(unittest.TestCase):
    def test_selected_checkpoint_guard_and_exact_pilot_domain(self):
        artifact=load_checkpoint(CHECKPOINT);self.assertTrue(all(p['kind']=='schedule' for p in artifact['policies_by_context']))
        declared=tasks();self.assertEqual(len(declared),264);self.assertEqual(sum(t['retain_trace'] for t in declared),33)
        self.assertEqual({t['config']['seed'] for t in declared},set(range(8)))
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'changed.json';p.write_bytes(CHECKPOINT.read_bytes()+b' ')
            with self.assertRaises(ValueError):load_checkpoint(p)

    def test_priority_and_exact_canonical_match_direct_audited_composition(self):
        artifact=load_checkpoint(CHECKPOINT);context=artifact['contexts'][0]
        for selector in ('priority','exact'):
            instance=build(12,seed=0);factory,controller=construct(instance,artifact,selector=selector,actor_seed=7);actual=factory.run()
            weights=dict(context['weights'],selector=selector,policy_seed=7)
            direct=Controller(artifact['policies_by_context'][0],weights,7,True,artifact['interval'])
            options=deepcopy(context['solver_options']);options.pop('admission')
            with reward_override('no-batch'):
                expected=AdmissionMaintenanceGuardFactory(instance,weights,direct,maintenance_outage_guard=True,**options).run()
            fields=('operations','moves','worker_moves','events','energy','metrics','decisions','admission_history')
            self.assertEqual(digest({k:actual[k] for k in fields}),digest({k:expected[k] for k in fields}))
            self.assertTrue(all(d['weights']['selector']==selector and d['weights']['policy_seed']==7 for d in actual['decisions']))
            self.assertTrue(check_trace(actual)['valid']);self.assertEqual(telemetry(actual)['decode_mismatches'],0)

    def test_actual_replayed_controller_is_causal(self):
        artifact=load_checkpoint(CHECKPOINT);traces=[]
        for seed in (0,1,2):
            f,c=construct(build(12,seed=seed),artifact,selector='exact',actor_seed=13);trace=f.run()
            self.assertTrue(check_trace(trace)['valid']);traces.append(trace)
        self.assertTrue(check_paired_causality(traces)['valid'])

    def test_actual_worker_path_checks_identity_and_retains_trace(self):
        with tempfile.TemporaryDirectory() as tmp:
            task=tasks()[0];task.update(source_hashes=hashes(),checkpoint=str(CHECKPOINT),output=tmp)
            row=simulate(task)
            self.assertTrue(row['valid'],row.get('error',row.get('issues')))
            self.assertTrue(row['identity_audit']['valid']);self.assertTrue(Path(row['trace_path']).exists())
            self.assertEqual(row['qubo_telemetry']['decode_mismatches'],0)

    def test_actual_simulation_and_coupling_not_confused_with_fallback(self):
        def decision(simulated,couplers,bits=2,fallback=None):
            return dict(tick=0,candidates=[],conflicts=[],capacities={},committed=['C0'],result=dict(selected=['C0'],method='fixture',
                qubo=dict(variables=bits,core_variables=1,slack_variables=bits-1,couplers=couplers),quantum_algorithm_simulated=simulated,
                fallback_reason=fallback,sampling=dict(circuit=dict(qubits=bits))))
        trace=dict(qubo_decisions=[decision(True,1),decision(True,0,1),decision(False,12,8,'five-bit limit')])
        out=telemetry(trace);self.assertEqual((out['qaoa_calls'],out['coupled_qaoa_calls'],out['trivial_1bit_qaoa_calls'],out['fallback_calls']),(2,1,1,1))
        self.assertEqual(out['max_actual_simulated_quantum_bits'],2);self.assertEqual(out['max_total_bits'],8)
        trace['qubo_decisions'][0]['committed']=[];self.assertEqual(telemetry(trace)['decode_mismatches'],1)


if __name__=='__main__':unittest.main()
