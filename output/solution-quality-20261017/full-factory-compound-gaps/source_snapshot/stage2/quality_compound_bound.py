"""Stronger offline QA relaxation using every mandatory manufacturing step.

The audited engine updates risk as r <- 1-(1-r)(1-p). Taking the minimum
legal-mode base p at each mandatory step, and granting zero wear, produces
1-product(1-p_min) as a policy-independent lower bound. No statistical
independence of inspection draws is used. All original source/domain guards
remain mandatory; no factory or frozen certificate is changed.
"""
from fractions import Fraction
import hashlib

from .quality_material_bound import (certificate as original_certificate, keyed_uniform,
    material_relaxation, RECIPES)


def compound_floors(instance):
    # Invoke the original certificate for its full audited engine/domain guards.
    original = original_certificate(instance)
    margin = Fraction(1,10**10)
    floors = {}
    for recipe, route in instance['recipes'].items():
        survival = Fraction(1)
        for step in route:
            if step['process'] == 'QA':
                continue
            table = instance['quality']['manufacturing_defect_probabilities'][step['process']]
            minimum = min(Fraction(str(table[mode])) for mode in instance['modes'][step['process']])
            survival *= 1-minimum
        floors[recipe] = max(Fraction(0), 1-survival-margin)
    repair = Fraction(str(instance['quality']['repair_residual_probability']))-margin
    return original, floors, repair


def certificate(instance):
    original, floors, repair = compound_floors(instance)
    demands, evidence = {}, []
    for order in original['necessary_blank_demands']:
        need, impossible = [], False
        for recipe in (*RECIPES,'pump'):
            uid=f'{order}/{recipe}/1'
            def forced_scrap(unit):
                first=keyed_uniform(instance['seed'],f'quality:{unit}:0')
                second=keyed_uniform(instance['seed'],f'quality:{unit}:1')
                forced=first<floors[recipe] and second<repair
                if forced:
                    evidence.append(dict(order_id=order,recipe=recipe,unit_id=unit,
                        first_draw=float(first),repair_draw=float(second),
                        first_risk_floor=float(floors[recipe]),repair_risk_floor=float(repair),necessary_scrap=True))
                return forced
            first=forced_scrap(uid)
            if recipe=='pump':
                impossible |= first
            else:
                need.append(1+int(first))
                if first:
                    impossible |= forced_scrap(uid+'~r1')
        demands[order] = None if impossible else tuple(need)
    bound=material_relaxation(demands,original['available_raw_blanks'])
    if bound['unfulfilled_lower_bound'] < original['unfulfilled_lower_bound']:
        raise AssertionError('Compounded necessary bound must dominate original max-step bound')
    return dict(original, **dict(bound,
        schema='stage2-quality-compound-necessary-bound.v1',
        necessary_blank_demands=demands,unavoidable_quality_evidence=evidence,
        original_max_step_lower_bound=original['unfulfilled_lower_bound'],
        risk_floor_method='1-product(1-min_legal_mode_base_risk) across all mandatory non-QA steps, minus1e-10 rounding margin; zero wear granted',
        compound_risk_floor_rationals={r:[v.numerator,v.denominator] for r,v in floors.items()},
        compound_source_sha256=hashlib.sha256(__import__('pathlib').Path(__file__).read_bytes()).hexdigest()))
