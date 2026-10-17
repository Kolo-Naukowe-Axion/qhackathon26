"""Count declared encoding families; do not pretend a local QUBO is global.

The global start-variable count is an explicit naive time-indexed family only,
not a complete formulation. It omits workers, logistics and contingency slots,
so it is a lower bound on this particular naive construction's total bits.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from math import ceil
from pathlib import Path


def audit(instance,trace=None):
    horizon=instance['horizon_ticks'];groups=Counter();operations=0
    machines=instance['machines']
    for order in instance['orders']:
        for recipe in ('housing','rotor','flange','pump'):
            for step in instance['recipes'][recipe]:
                operations+=1;process=step['process']
                allowed=instance['modes'][process]
                if order.get('precision_required'):
                    names=instance['certification_modes']['precision'].get(process,allowed)
                else:names=allowed
                for machine in machines:
                    if machine['process']!=process:continue
                    for name in names:
                        a,b=allowed[name]['duration_factor'];c,d=machine['duration_factor']
                        duration=ceil(step['base_ticks']*a*c/(b*d))
                        # Relax route/release constraints except the order's
                        # known release. Setup, travel and resource feasibility
                        # would require more constraints, not invisible bits.
                        groups[process]+=max(0,horizon-duration-order['release_tick']+1)
    mechanisms=[
      dict(name='machine/mode/certification',naive='Machine-mode-start alternatives counted below; operation one-hot and machine-time conflicts required',local='Candidates are prevalidated against current machine, wear, mode and certification; at most one bit per offered start'),
      dict(name='qualified worker calendars',naive='Additional crew/attendance assignment variables and time-indexed capacity or pair conflicts; not counted',local='Classical availability filtering and explicit shared attendance interval conflicts; zero auxiliary bits for pair conflicts'),
      dict(name='portable tools and service',naive='Location, movement, remaining life and service decisions across time; not counted',local='Current tool identity/life/location frozen at boundary; shared tools generate pair conflicts; relocation/service scheduled classically'),
      dict(name='finite buffers and blocked outputs',naive='Inventory/reservation occupancy and pickup release across time; not counted',local='Destination reservations and blocking replayed classically; local candidates inherit fixed boundary feasibility'),
      dict(name='AGV lanes/traction/chargers',naive='Vehicle, departure, route/edge-time, payload and charge variables; not counted',local='Classical transport planner and checker, outside current start-selection QUBO; no claimed global quantum compression'),
      dict(name='BOM assembly and batch identity',naive='Matching/consumption and batch membership/activation variables; not counted',local='Classical BOM matching and homogeneous ready batches; QUBO does not choose all alternative assembly plans'),
      dict(name='power capacity',naive='Time-indexed capacity rows plus slack/other inequality encoding',local='Residual integer-centikW capacity rows; exact GCD scaling, redundant row removal, pair-only capacity-one rows, otherwise bounded binary slack'),
      dict(name='battery/energy/carbon',naive='SOC/action balances and objective coefficients across time; not counted',local='Classical causal battery actions; grid feasibility checked on full trace; energy cost/carbon reported separately'),
      dict(name='uncertainty/quality/rework',naive='Contingent activity slots/scenario copies plus nonanticipativity constraints; not counted',local='Causal simulation, keyed quality and revealed shocks; local boundary contains only observed state; future not encoded'),
      dict(name='priced tool rental',naive='Investment/arrival/location/availability variables; not counted',local='High-level causal policy controls request; hard investment budget and lead time independently replayed'),
    ]
    result=dict(schema='stage2-encoding-cost-audit.v1',instance_sha256=hashlib.sha256(json.dumps(instance,sort_keys=True).encode()).hexdigest(),
        known_initial_orders=len(instance['orders']),nominal_known_operations=operations,
        horizon_ticks=horizon,tick_minutes=instance['tick_minutes'],
        naive_known_nominal_start_bits=sum(groups.values()),naive_start_bits_by_process=dict(groups),
        naive_scope='One bit per nominal known operation/eligible machine/legal mode/integer start; all other variable families excluded',
        naive_is_complete_formulation=False,mechanisms=mechanisms,
        reduction_scope='Conditional dispatch candidate-pool decomposition; not a lossless global factory encoding',
        global_lexicographic_optimality_gap=None,
        price_of_restriction='Global loss unknown; compare same-model classical incumbents and scoped exact tiny references')
    if trace:
        from .check import check_trace
        verified=check_trace(trace)
        decisions=trace.get('qubo_decisions',[]);qs=[d['result']['qubo'] for d in decisions]
        result['measured_local']=dict(decisions=len(decisions),max_total_bits=max((q['variables'] for q in qs),default=0),
            max_core_bits=max((q['core_variables'] for q in qs),default=0),
            max_auxiliary_bits=max((q['slack_variables'] for q in qs),default=0),
            max_couplers=max((q['couplers'] for q in qs),default=0),
            genuine_qaoa_simulated_calls=sum(d['result'].get('quantum_algorithm_simulated',False) for d in decisions),
            classical_fallback_calls=sum(bool(d['result'].get('fallback_reason')) for d in decisions),
            max_simulated_quantum_total_bits=max((d['result']['qubo']['variables'] for d in decisions
                if d['result'].get('quantum_algorithm_simulated',False)),default=0),
            decode_mismatches=sum(set(d['committed'])!=set(d['result']['selected']) for d in decisions),
            note='These maxima describe local problems actually offered; they exclude classical scheduling/transport/controller work')
        result['fulfillment_primary_certificate']=dict(unfulfilled=verified['metrics']['unfulfilled_orders'],
            nonnegative_global_lower_bound=0,
            independently_checked_valid=verified['valid'],
            primary_optimal_on_this_realization=bool(verified['valid'] and verified['terminal_requirements_met'] and
                verified['metrics']['unfulfilled_orders']==0),
            scope='Zero missing orders proves primary fulfillment optimality for this realized trace only; secondary cost/tardiness and policy-wide optimality remain unproved')
    return result


if __name__=='__main__':
    import argparse
    from .spec import build
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--orders',type=int,default=24)
    p.add_argument('--trace',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();trace=json.loads(a.trace.read_text()) if a.trace else None
    result=audit(trace['instance'] if trace else build(a.orders),trace)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('nominal_known_operations','naive_known_nominal_start_bits','reduction_scope')}))
