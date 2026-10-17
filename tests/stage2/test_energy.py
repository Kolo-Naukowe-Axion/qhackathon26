"""Battery action physics, causal strategy and exact fixed-load DP references."""
from copy import deepcopy
import itertools
import unittest

from stage2.energy import run,EnergyFactory,fixed_load_dp,apply_battery_plan,battery_metrics,source_hashes
from stage2.engine import Factory
from stage2.advanced import AdvancedFactory
from stage2.spec import build
from stage2.check import check_trace,check_paired_causality


class EnergyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.instance=build(orders=3,horizon=2880,seed=20)
        cls.weights=dict(wip_limit=4,mode='standard',lease_calibration=True)
        cls.baseline=Factory(cls.instance,cls.weights).run()

    def test_baseline_mixin_exactly_preserves_legacy_energy_and_physical_actions(self):
        trace=run(self.instance,self.weights,energy_policy=dict(strategy='baseline'))
        for key in ('operations','moves','worker_moves','events','energy','metrics'):
            self.assertEqual(trace[key],self.baseline[key],key)

    def test_causal_energy_optimization_preserves_static_physical_schedule(self):
        for advanced in (False,True):
            with self.subTest(advanced=advanced):
                original=AdvancedFactory(self.instance,self.weights).run() if advanced else self.baseline
                for reserve in ('terminal','recovery'):
                    trace=run(self.instance,self.weights,advanced=advanced,energy_policy=dict(reserve=reserve))
                    report=check_trace(trace)
                    self.assertTrue(report['valid'],report['issues']);self.assertTrue(report['terminal_requirements_met'])
                    for key in ('operations','moves','worker_moves','events','qubo_decisions'):
                        self.assertEqual(trace[key],original[key],key)
                    for key in ('orders','shipped','shipped_at','total_tardiness_ticks','unfinished'):
                        self.assertEqual(trace['metrics'][key],original['metrics'][key],key)
                    self.assertLess(trace['metrics']['energy_cost'],original['metrics']['energy_cost'])

    def test_conservative_reserve_is_never_spent_and_battery_actually_cycles(self):
        trace=run(self.instance,self.weights);metrics=battery_metrics(trace)
        self.assertGreater(metrics['action_counts']['discharge'],0)
        self.assertGreater(metrics['action_counts']['charge'],0)
        self.assertGreaterEqual(metrics['soc_min'],self.instance['energy']['stationary_soc_terminal_min'])

    def test_no_distant_peak_means_no_unnecessary_final_low_tariff_fill(self):
        instance=build(orders=0,horizon=100)
        trace=run(instance)
        self.assertTrue(all(row['battery_action']=='idle' for row in trace['energy']))
        self.assertEqual(trace['metrics']['terminal_soc'],600)

    def test_solar_surplus_can_justify_charging_at_peak(self):
        factory=EnergyFactory(build(orders=0));factory.t=720;factory.soc=600
        self.assertEqual(factory.battery_action(12,16,90),'charge')
        self.assertEqual(factory.battery_action(12,12,90),'idle')

    def test_partial_peak_discharge_respects_loss_cost_and_no_export(self):
        factory=EnergyFactory(build(orders=0));factory.t=900;factory.soc=800
        self.assertEqual(factory.battery_action(12,7,90),'discharge')
        self.assertEqual(factory.battery_action(12,9,90),'idle')
        # The fixed output cannot be dumped or exported when total load is <9.
        self.assertEqual(factory.battery_action(5,0,90),'idle')

    def test_charge_headroom_and_soc_capacity_are_hard_limits(self):
        factory=EnergyFactory(build(orders=0));factory.t=0;factory.soc=2400
        self.assertEqual(factory.battery_action(12,0,90),'idle')
        factory.soc=600
        self.assertEqual(factory.battery_action(85,0,90),'idle')

    def test_recovery_reserve_is_empirical_and_terminal_failure_is_reported(self):
        instance=build(orders=0);instance['energy'].update(base_load_kw=90,solar_peak_kw=0)
        safe=run(instance,energy_policy=dict(reserve='terminal'))
        risky=run(instance,energy_policy=dict(reserve='recovery'))
        self.assertTrue(check_trace(safe)['valid']);self.assertTrue(check_trace(safe)['terminal_requirements_met'])
        self.assertTrue(check_trace(risky)['valid']);self.assertFalse(check_trace(risky)['terminal_requirements_met'])
        self.assertLess(risky['metrics']['terminal_soc'],600)

    def test_paired_tapes_do_not_expose_actual_seed_or_future_outcomes(self):
        for reserve in ('terminal','recovery'):
            traces=[run(build(orders=3,horizon=2880,seed=s),self.weights,advanced=True,
                energy_policy=dict(reserve=reserve)) for s in range(4)]
            result=check_paired_causality(traces);self.assertTrue(result['valid'],result['issues'])
            self.assertTrue(all(check_trace(t)['valid'] for t in traces))

    def test_same_inputs_and_physical_sources_are_unchanged(self):
        before=deepcopy(self.instance);hashes=source_hashes();run(self.instance,self.weights)
        self.assertEqual(self.instance,before);self.assertEqual(source_hashes(),hashes)

    def test_fixed_load_dp_is_checked_and_dominates_both_causal_policies(self):
        for objective,metric in [('cost','energy_cost'),('carbon','carbon_kg')]:
            result=fixed_load_dp(self.baseline,objective)
            self.assertEqual(result['status'],'OPTIMAL');self.assertTrue(result['verification']['valid'],result['verification']['issues'])
            self.assertTrue(result['verification']['terminal_requirements_met'])
            self.assertAlmostEqual(result['objective_value'],result['trace']['metrics'][metric],places=9)
            for reserve in ('terminal','recovery'):
                causal=run(self.instance,self.weights,energy_policy=dict(reserve=reserve))
                self.assertLessEqual(result['objective_value'],causal['metrics'][metric]+1e-8)
            for key in ('operations','moves','worker_moves','events'):
                self.assertEqual(result['trace'][key],self.baseline[key])

    def test_exact_dp_matches_independent_exhaustive_small_reference(self):
        # Eight ticks, 31 SOC states and a price transition: every action string
        # is enumerated independently, including lossy 9/-10 SOC arithmetic.
        instance=build(orders=0,horizon=8);instance['day_ticks']=12
        instance['energy'].update(stationary_soc_capacity=30,stationary_soc_initial=10,
            stationary_soc_min=0,stationary_soc_terminal_min=10,solar_peak_kw=0)
        trace=Factory(instance).run();best=float('inf');best_actions=None
        for actions in itertools.product(('idle','charge','discharge'),repeat=8):
            soc=10;cost=0;okay=True
            for tick,action in enumerate(actions):
                delta={'idle':0,'charge':9,'discharge':-10}[action];soc+=delta
                if not 0<=soc<=30:okay=False;break
                grid=12+{'idle':0,'charge':10,'discharge':-9}[action]
                price=.34 if 4<=tick<9 else .12;cost+=grid*price/60
            if okay and soc>=10 and cost<best:best=cost;best_actions=actions
        result=fixed_load_dp(trace)
        self.assertEqual(result['status'],'OPTIMAL');self.assertAlmostEqual(result['objective_value'],best,places=12)
        self.assertTrue(result['verification']['valid'],result['verification']['issues'])

    def test_dp_cannot_invent_grid_headroom_or_battery_energy(self):
        instance=build(orders=0,horizon=2);instance['energy'].update(base_load_kw=12,
            normal_grid_cap_kw=5,solar_peak_kw=0,stationary_soc_capacity=60,
            stationary_soc_initial=30,stationary_soc_min=0,stationary_soc_terminal_min=0)
        trace=Factory(instance).run();result=fixed_load_dp(trace)
        self.assertEqual(result['status'],'OPTIMAL');self.assertEqual(result['actions'],['discharge','discharge'])
        self.assertTrue(result['verification']['valid'],result['verification']['issues'])
        instance['energy']['stationary_soc_terminal_min']=30
        result=fixed_load_dp(Factory(instance).run());self.assertEqual(result['status'],'INFEASIBLE')

    def test_plan_replay_rejects_invalid_action_lengths_and_soc(self):
        with self.assertRaises(ValueError):apply_battery_plan(self.baseline,['idle'])
        with self.assertRaises(ValueError):apply_battery_plan(self.baseline,['discharge']*2880)

    def test_invalid_strategy_arguments_are_rejected(self):
        for policy in [dict(strategy='magic'),dict(objective='magic'),dict(reserve='magic')]:
            with self.assertRaises(ValueError):run(self.instance,energy_policy=policy)
        with self.assertRaises(ValueError):fixed_load_dp(self.baseline,'magic')


if __name__=='__main__':unittest.main()
