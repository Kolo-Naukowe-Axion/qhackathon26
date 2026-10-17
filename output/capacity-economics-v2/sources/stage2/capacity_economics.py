"""Exact, assumption-explicit valuation of checked manufacturing schedules.

This is a cost ledger and break-even sensitivity for declared plans, not a
minimum-monetary-cost solver or a calibrated equipment purchase recommendation.
"""
import argparse
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path

from .window_qubo import check_plan, digest


def rational(value):
    if isinstance(value, bool):
        raise ValueError('Boolean is not a monetary parameter')
    try:
        result = Fraction(str(value))
    except (ValueError, ZeroDivisionError, OverflowError) as error:
        raise ValueError('A finite rational parameter is required') from error
    return result


def number(value):
    value = Fraction(value)
    return dict(numerator=value.numerator, denominator=value.denominator,
                value=float(value))


def default_profile():
    return dict(currency='illustrative PLN', calibrated=False, clock='Minutes from synthetic midnight',
        tariff_period=1440,
        tariffs=[dict(start=0, end=360, pln_per_kwh='0.50'),
                 dict(start=360, end=1080, pln_per_kwh='1.00'),
                 dict(start=1080, end=1440, pln_per_kwh='0.70')],
        active_kw={'T':'9', 'F':'12', 'S':'10', 'WASH':'4', 'H':'16', 'QA':'3', 'A':'4'},
        standby_kw='0.5', base_load_kw='12', labor_pln_per_attended_hour='40',
        night_premium_pln_per_attended_hour='10', night_intervals=[[0,360],[1320,1440]],
        machine_start_pln='5', late_pln_per_weighted_minute='10',
        powered_policy='used_from_first_start_to_last_end',
        description='All prices and power rates are explicit synthetic assumptions. '
                    'Attendance wages exclude walking, setup crews and salaried standby. '
                    'Active machine power includes standby; family-setup gaps consume standby only. '
                    'No solar, battery, export, demand charge or grid-cap optimization is claimed.')


def validate_profile(profile):
    period = profile['tariff_period']
    if type(period) is not int or period < 1:
        raise ValueError('Positive integer tariff period required')
    cursor = 0
    for band in profile['tariffs']:
        if type(band['start']) is not int or type(band['end']) is not int or band['start'] != cursor or not cursor < band['end'] <= period:
            raise ValueError('Tariff bands must partition the full clock period')
        if rational(band['pln_per_kwh']) < 0:
            raise ValueError('Nonnegative tariffs required')
        cursor = band['end']
    if cursor != period:
        raise ValueError('Tariff bands must cover the full period')
    for key in ['standby_kw','base_load_kw','labor_pln_per_attended_hour',
                'night_premium_pln_per_attended_hour','machine_start_pln','late_pln_per_weighted_minute']:
        if rational(profile[key]) < 0:
            raise ValueError('Costs and power must be nonnegative')
    standby = rational(profile['standby_kw'])
    if any(rational(power) < standby for power in profile['active_kw'].values()):
        raise ValueError('Active total power must include at least standby power')
    nights = profile['night_intervals']
    for start, end in nights:
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= period:
            raise ValueError('Night windows must be integer intervals within the clock')
    if any(a[1] > b[0] for a,b in zip(nights,nights[1:])):
        raise ValueError('Night windows must be sorted and disjoint')
    if profile['powered_policy'] != 'used_from_first_start_to_last_end':
        raise ValueError('This ledger supports the declared fixed used-machine activation policy only')
    return profile


def process(machine):
    return machine.rstrip('0123456789')


def tariff_integral(profile, start, end):
    """Exact sum of PLN/kWh rates over integer minutes, including clock wraps."""
    if type(start) is not int or type(end) is not int or start < 0 or end < start:
        raise ValueError('Nonnegative half-open integer interval required')
    period = profile['tariff_period']
    total = Fraction(0)
    while start < end:
        clock = start % period
        band = next(b for b in profile['tariffs'] if b['start'] <= clock < b['end'])
        span = min(end-start, band['end']-clock)
        total += span*rational(band['pln_per_kwh'])
        start += span
    return total


def night_minutes(profile, start, end):
    period = profile['tariff_period']
    return sum(any(a <= t % period < b for a,b in profile['night_intervals'])
               for t in range(start,end))


def ledger(problem, plan, profile):
    validate_profile(profile)
    checked = check_plan(problem, plan)
    if not checked['valid']:
        raise ValueError('Cost valuation requires a complete independently checked raw schedule')
    end = checked['makespan']
    standby = rational(profile['standby_kw'])
    active_energy = Fraction(0)
    active_electricity = Fraction(0)
    standby_energy = Fraction(0)
    standby_electricity = Fraction(0)
    attendance = premium_minutes = 0
    machines = {}
    for row in plan:
        key = process(row['machine'])
        if key not in profile['active_kw']:
            raise ValueError('Explicit active power missing for '+key)
        power = rational(profile['active_kw'][key])
        active_energy += power*(row['end']-row['start'])/60
        active_electricity += power*tariff_integral(profile,row['start'],row['end'])/60
        attendance += row['attended_end']-row['start']
        premium_minutes += night_minutes(profile,row['start'],row['attended_end'])
        machines.setdefault(row['machine'],[]).append(row)
    for mid, rows in machines.items():
        start = min(r['start'] for r in rows)
        finish = max(r['end'] for r in rows)
        occupied_minutes = sum(r['end']-r['start'] for r in rows)
        standby_energy += standby*(finish-start-occupied_minutes)/60
        idle_tariff = tariff_integral(profile,start,finish) - sum(
            (tariff_integral(profile,r['start'],r['end']) for r in rows),Fraction(0))
        standby_electricity += standby*idle_tariff/60
    base_energy = rational(profile['base_load_kw'])*end/60
    base_electricity = rational(profile['base_load_kw'])*tariff_integral(profile,0,end)/60
    labor = rational(profile['labor_pln_per_attended_hour'])*attendance/60
    premium = rational(profile['night_premium_pln_per_attended_hour'])*premium_minutes/60
    startup = rational(profile['machine_start_pln'])*len(machines)
    late = rational(profile['late_pln_per_weighted_minute'])*checked['weighted_terminal_tardiness']
    operating = active_electricity+standby_electricity+base_electricity+labor+premium+startup
    money = dict(active_electricity=active_electricity,standby_electricity=standby_electricity,
                 base_electricity=base_electricity,labor=labor,night_premium=premium,
                 machine_start=startup,operating=operating,late_penalty=late,total_before_capacity_fee=operating+late)
    return dict(problem_sha256=digest(problem),plan_sha256=digest(plan),profile_sha256=digest(profile),
                check=checked,attended_minutes=attendance,night_attended_minutes=premium_minutes,
                used_machines=sorted(machines),money={k:number(v) for k,v in money.items()},
                energy_kwh={k:number(v) for k,v in dict(active=active_energy,standby=standby_energy,base=base_energy).items()},
                scope='Exact declared-plan valuation under a fixed activation policy; not minimum monetary cost')


def value_of(record, key):
    value = record['money'][key]
    return Fraction(value['numerator'],value['denominator'])


def compare(base, replacement, late_rate, fee=0, probability=1, exposures=1,
            years=1, discount_rate=0, annual_maintenance=0, installation=0):
    """Conditional event and repeated-exposure sensitivities, with explicit recourse."""
    rate, fee, probability, discount, maintenance, installation = map(rational,
        [late_rate,fee,probability,discount_rate,annual_maintenance,installation])
    if base.get('profile_sha256') != replacement.get('profile_sha256'):
        raise ValueError('Plan valuations must use the same explicit cost profile')
    if any(v < 0 for v in [rate,fee,discount,maintenance,installation]) or not 0 <= probability <= 1:
        raise ValueError('Nonnegative costs/discount and probability within [0,1] required')
    if type(exposures) is not int or type(years) is not int or exposures < 1 or years < 1:
        raise ValueError('Positive integer exposure count and years required')
    saved = base['check']['weighted_terminal_tardiness']-replacement['check']['weighted_terminal_tardiness']
    operating_saved = value_of(base,'operating')-value_of(replacement,'operating')
    gross = operating_saved+rate*saved
    # Fee is charged only if the event triggers the declared replacement action.
    expected_annual = exposures*probability*(gross-fee)-maintenance
    present = sum((expected_annual/(1+discount)**year for year in range(1,years+1)),Fraction(0))-installation
    gross_purchase = sum(((exposures*probability*gross-maintenance)/(1+discount)**year
                          for year in range(1,years+1)),Fraction(0))-installation
    threshold = (fee-operating_saved)/saved if saved > 0 else None
    return dict(saved_weighted_late_minutes=saved,operating_saved=number(operating_saved),
                late_rate=number(rate),event_fee=number(fee),probability=number(probability),
                exposures_per_year=exposures,years=years,discount_rate=number(discount),
                annual_maintenance=number(maintenance),installation=number(installation),
                event_gross_benefit=number(gross),event_net_benefit=number(gross-fee),
                maximum_event_fee=number(gross),break_even_late_rate=number(threshold) if threshold is not None else None,
                expected_annual_net=number(expected_annual),present_value_of_net=number(present),
                maximum_upfront_purchase_price=number(gross_purchase),
                assumptions='Event probability is user-specified; event is known before replanning. '
                            'No-event operating plans/costs cancel, optional capacity stays off. '
                            'Purchase-price threshold excludes the per-event lease fee; no calibrated demand/ROI claim.')


def run(source, frontier, output):
    output.mkdir(parents=True,exist_ok=False)
    root=Path(__file__).resolve().parents[1]
    hashes={}
    for name in ['stage2/capacity_economics.py','stage2/window_qubo.py']:
        path=root/name;target=output/'sources'/name;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(path.read_bytes());hashes[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    profile=default_profile()
    protocol=dict(profile=profile,source_hashes=hashes,
        variants=['outage_complete','replacement_complete','replacement_original_pool','replacement_enriched_pool'],
        late_rates=['0','1','5','10','20'],fees=['0','100','500'],probabilities=['0','0.3','1'],
        scope='Exact plan-cost and capacity-fee sensitivity; original native plans optimize priority objective, not money',
        veloxq_calls=0,physical_qpu_calls=0)
    inputs=[source/case/name for case in ['heat-outage-32','heat-lease-32']
            for name in ['problem.json','report.json']]
    inputs.append(frontier/'heat-lease-32/cap-64/report.json')
    protocol['input_file_sha256']={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs}
    for index,path in enumerate(inputs):
        target=output/'inputs'/f'{index}-{path.name}';target.parent.mkdir(exist_ok=True)
        target.write_bytes(path.read_bytes())
    (output/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    records={}
    for name,case,key in [('outage_complete','heat-outage-32','raw_reference'),
                          ('replacement_complete','heat-lease-32','raw_reference'),
                          ('replacement_original_pool','heat-lease-32','pool_reference')]:
        directory=source/case
        problem=json.loads((directory/'problem.json').read_text())
        ref=json.loads((directory/'report.json').read_text())[key]
        records[name]=ledger(problem,ref['plan'],profile)
        records[name]['plan']=ref['plan']
    problem=json.loads((source/'heat-lease-32/problem.json').read_text())
    ref=json.loads((frontier/'heat-lease-32/cap-64/report.json').read_text())['reference']
    records['replacement_enriched_pool']=ledger(problem,ref['plan'],profile)
    records['replacement_enriched_pool']['plan']=ref['plan']
    sensitivities=[]
    for name in protocol['variants'][1:]:
        for rate in protocol['late_rates']:
            for fee in protocol['fees']:
                for probability in protocol['probabilities']:
                    sensitivities.append(dict(variant=name,**compare(records['outage_complete'],records[name],rate,fee,probability)))
    example=compare(records['outage_complete'],records['replacement_complete'],'10',fee='100',
                    probability='0.3',exposures=52,years=3,discount_rate='0.05',annual_maintenance='50',installation='100')
    assert all(hashlib.sha256((root/name).read_bytes()).hexdigest()==h for name,h in hashes.items())
    assert all(hashlib.sha256(Path(name).read_bytes()).hexdigest()==h
               for name,h in protocol['input_file_sha256'].items())
    report=dict(schema='qfactoria-capacity-economics.v1',protocol=protocol,records=records,
                sensitivities=sensitivities,illustrative_repeated_exposure=example,source_stable=True,
                veloxq_calls=0,physical_qpu_calls=0)
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    (output/'manifest.json').write_text(json.dumps({str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in output.rglob('*') if p.is_file()},indent=2)+'\n')
    print(json.dumps(dict(variants=len(records),sensitivities=len(sensitivities),
         maximum_event_fee=example['maximum_event_fee'],scope=protocol['scope'])))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=Path('output/manufacturing-recovery-v2'))
    parser.add_argument('--frontier',type=Path,default=Path('output/capacity-frontier-review-v1'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();run(args.source,args.frontier,args.output)
