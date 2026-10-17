from copy import deepcopy
from fractions import Fraction
import unittest

from stage2.capacity_economics import compare,default_profile,ledger,number,tariff_integral,value_of,validate_profile
from stage2.window_experiments import tiny_problem
from stage2.window_qubo import assignments,check_plan


class CapacityEconomicsTests(unittest.TestCase):
    def test_tariff_integrates_boundaries_and_clock_wrap_exactly(self):
        p=default_profile()
        self.assertEqual(tariff_integral(p,350,370),15)
        self.assertEqual(tariff_integral(p,1430,1450),12)
        self.assertEqual(tariff_integral(p,0,2880),2*tariff_integral(p,0,1440))
        p['tariffs'][1]['start']=361
        with self.assertRaises(ValueError):validate_profile(p)

    def test_attendance_and_standby_are_not_double_counted(self):
        p=tiny_problem();p.update(horizon=8,grid=2)
        p['machines']['M']['available']=[[0,8]];p['workers']['W']['available']=[[0,8]]
        p['operations'][0].update(attendance='start',start_attendance=1,due=8)
        p['operations'][1].update(due=8)
        plan=[next(r for r in assignments(p,p['operations'][0]) if r['start']==0),
              next(r for r in assignments(p,p['operations'][1]) if r['start']==4)]
        self.assertTrue(check_plan(p,plan)['valid'])
        profile=default_profile();profile['active_kw']={'M':'6'};profile['standby_kw']='3'
        result=ledger(p,plan,profile)
        self.assertEqual(result['attended_minutes'],3)
        self.assertEqual(result['energy_kwh']['active'],number(Fraction(2,5)))
        self.assertEqual(result['energy_kwh']['standby'],number(Fraction(1,10)))
        self.assertEqual(value_of(result,'active_electricity'),Fraction(1,5))

    def test_break_even_probability_discount_and_fee_have_exact_semantics(self):
        base=dict(profile_sha256='a'*64,check=dict(weighted_terminal_tardiness=45),money=dict(operating=number(100)))
        capacity=dict(profile_sha256='a'*64,check=dict(weighted_terminal_tardiness=0),money=dict(operating=number(120)))
        r=compare(base,capacity,10,fee=100,probability='0.3',exposures=10,years=2,discount_rate='0.1')
        self.assertEqual(r['event_gross_benefit'],number(430))
        self.assertEqual(r['expected_annual_net'],number(990))
        self.assertEqual(r['present_value_of_net'],number(Fraction(9900,11)+Fraction(99000,121)))
        self.assertEqual(r['break_even_late_rate'],number(Fraction(8,3)))
        self.assertEqual(compare(base,capacity,10,probability=0)['expected_annual_net'],number(0))
        with self.assertRaises(ValueError):compare(base,capacity,10,probability='1.1')
        with self.assertRaises(ValueError):compare(dict(base,profile_sha256='a'),dict(capacity,profile_sha256='b'),10)
        with self.assertRaises(ValueError):compare(dict(base,profile_sha256=None),dict(capacity,profile_sha256=None),10)

    def test_invalid_schedule_and_uncalibrated_parameters_cannot_silently_pass(self):
        p=tiny_problem();profile=default_profile();profile['active_kw']={'M':'6'}
        with self.assertRaises(ValueError):ledger(p,[],profile)
        for key,value in [('standby_kw','-1'),('labor_pln_per_attended_hour','nan')]:
            bad=deepcopy(profile);bad[key]=value
            with self.assertRaises(ValueError):validate_profile(bad)


if __name__=='__main__':unittest.main()
