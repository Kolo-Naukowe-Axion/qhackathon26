"""Report observed activity from an independently checked realization.

Durations are half-open observed intervals clipped to the execution horizon.
Enabled features are descriptions, not evidence of use or binding constraints.
"""
from collections import Counter, defaultdict
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from .check import check_trace


def union_length(intervals):
    total = 0
    end = None
    for a, b in sorted(intervals):
        if b <= a:
            continue
        if end is None or a > end:
            total += b - a
            end = b
        elif b > end:
            total += b - end
            end = b
    return total


def machine_windows(trace):
    """Reconstruct occupied/output-held windows; validation is caller's duty.

    Output stays occupied until the last batch member is physically picked up.
    A new operation at that machine without clearing output is forbidden by the
    current checker/model. This does not infer implicit same-station handoffs.
    """
    horizon = trace['horizon_ticks']
    pickups = defaultdict(list)
    processing, blocked = defaultdict(list), defaultdict(list)
    for move in trace['moves']:
        if move.get('kind', 'transport') == 'transport' and move.get('entity_type', 'part') == 'part':
            pickups[(move['unit_id'], move['from'])].append(move['pickup_tick'])
    for op in trace['operations']:
        if op['kind'] != 'process':
            continue
        mid = op['machine_id']
        processing[mid].append((op['start'], min(op['end'], horizon)))
        if op['end'] >= horizon:
            continue
        ends = [min((tick for tick in pickups[(uid, mid)] if tick >= op['end']), default=horizon)
                for uid in op['unit_ids']]
        if ends:
            blocked[mid].append((op['end'], min(max(ends), horizon)))
    return processing, blocked


def buffer_activity(trace):
    """Physical inputs plus inbound reservations, from dispatch to consumption."""
    horizon = trace['horizon_ticks']
    machines = {machine['id']: machine for machine in trace['instance']['machines']}
    starts = defaultdict(list)
    for op in trace['operations']:
        if op['kind'] != 'process':
            continue
        inputs = op.get('parent_unit_ids') or op['unit_ids']
        for uid in inputs:
            starts[(op['machine_id'], uid)].append(op['start'])
    changes = defaultdict(lambda: defaultdict(int))
    units = {unit['id']: unit for unit in trace['instance'].get('units', [])}
    units.update({event['unit']['id']: event['unit'] for event in trace.get('events', [])
                  if event['type'] == 'new_unit' and 'unit' in event})
    for event in trace.get('events', []):
        if event['type'] != 'release':
            continue
        mid = units.get(event['unit_id'], {}).get('initial_location')
        if mid not in machines:
            continue
        end = min((tick for tick in starts[(mid, event['unit_id'])] if tick >= event['tick']), default=horizon)
        end = min(end, horizon)
        if end > event['tick']:
            changes[mid][event['tick']] += 1
            changes[mid][end] -= 1
    for move in trace['moves']:
        mid = move.get('to')
        if mid not in machines or move.get('kind', 'transport') != 'transport' or move.get('entity_type', 'part') != 'part':
            continue
        end = min((tick for tick in starts[(mid, move['unit_id'])] if tick >= move['drop_tick']), default=horizon)
        end = min(end, horizon)
        if end > move['start']:
            changes[mid][move['start']] += 1
            changes[mid][end] -= 1
    result = {}
    for mid, machine in machines.items():
        occupancy = maximum = saturated = 0
        previous = 0
        for tick, delta in sorted(changes[mid].items()):
            if occupancy == machine['input_capacity']:
                saturated += tick - previous
            occupancy += delta
            maximum = max(maximum, occupancy)
            previous = tick
        result[mid] = dict(capacity=machine['input_capacity'], max_reserved_or_present=maximum,
                           full_ticks=saturated)
    return result


def audit(trace):
    checked = check_trace(trace)
    if not checked['valid']:
        raise ValueError('Activity evidence requires a physically valid checked trace')
    instance = trace['instance']
    horizon = trace['horizon_ticks']
    ops, moves = trace['operations'], trace['moves']
    production = [op for op in ops if op['kind'] == 'process']
    processing, blocked = machine_windows(trace)
    machine_ids = [m['id'] for m in instance['machines']]
    # Independently establish that held-output time never includes processing
    # or maintenance at that machine. The checker enforces physical replay too.
    overlap = {}
    for mid in machine_ids:
        occupied = [(op['start'], min(op['end'], horizon)) for op in ops
                    if op['machine_id'] == mid and op['kind'] != 'tool_service']
        overlap[mid] = union_length(occupied) + union_length(blocked[mid]) - union_length(occupied + blocked[mid])
    if any(overlap.values()):
        raise ValueError('Inferred output blocking overlaps machine occupation')

    def observed(start, end):
        return max(0, min(end, horizon) - max(0, start))

    worker_time, worker_walk = defaultdict(list), defaultdict(list)
    for op in ops:
        intervals = op.get('worker_intervals')
        if intervals is None:
            intervals = [dict(worker_id=w, start=op['start'], end=op['end']) for w in op['worker_ids']]
        for interval in intervals:
            worker_time[interval['worker_id']].append((interval['start'], min(interval['end'], horizon)))
    for walk in trace['worker_moves']:
        worker_walk[walk['worker_id']].append((walk['start'], min(walk['end'], horizon)))
    workers = {worker['id'] for worker in instance['workers']}
    events = [event for event in trace['events'] if event['tick'] <= horizon]
    stock = dict(instance.get('raw_stock_units', {}))
    minimum = dict(stock)
    # Stable sorting preserves same-tick release/delivery order recorded by the
    # causal engine. No inventory exhaustion or denied request is invented.
    for event in sorted(events, key=lambda event: event['tick']):
        if event['type'] == 'release' and event['recipe'] in stock:
            recipe = event['recipe']
            stock[recipe] -= 1
            minimum[recipe] = min(minimum[recipe], stock[recipe])
        elif event['type'] == 'delivery':
            for recipe, count in event['contents'].items():
                stock[recipe] = stock.get(recipe, 0) + count
    energy = [row for row in trace['energy'] if row['tick'] < horizon]
    charges = [move for move in moves if move['kind'] == 'charge']
    decisions = trace.get('qubo_decisions', [])
    return dict(schema='stage2-observed-activity-audit.v2',
        scope='Checked realization only; activity, saturation or utilization does not prove causal bottlenecks',
        valid=True, terminal=checked['terminal_requirements_met'],
        horizon_ticks=horizon, tick_minutes=trace['tick_minutes'],
        metrics=trace.get('metrics', {}), independently_checked_metrics=checked['metrics'],
        checker_coverage=checked['coverage'], checker_unsupported=checked['unsupported'],
        checker_provenance=checked['provenance'],
        buffer_activity=buffer_activity(trace),
        buffer_activity_scope='Inbound reservation starts at dispatch; ends at processing consumption; output excluded',
        physical_machines=len(machine_ids), production_machines_used=len(processing),
        unused_production_machines=[mid for mid in machine_ids if not processing[mid]],
        machine_activity={mid:dict(production_ticks=union_length(processing[mid]),
            production_ticks_definition='operation occupation, including setup',
            output_blocked_ticks=union_length(blocked[mid]), output_blocking_overlap_ticks=overlap[mid]) for mid in machine_ids},
        production_operations=len(production), completed_production_operations=sum(op['end'] <= horizon for op in production),
        rework_operations=sum(bool(op.get('is_rework')) for op in production),
        setup_operations=sum(op.get('setup_ticks', 0) > 0 for op in production),
        setup_ticks=sum(observed(op['start'], op['start'] + op.get('setup_ticks', 0)) for op in production),
        homogeneous_multiunit_batches=sum(op['process'] == 'HEAT' and len(op['unit_ids']) > 1 for op in production),
        processing_modes=dict(Counter(op['mode'] for op in production)),
        bom_joins=sum(op['process'] == 'ASSEMBLY' and bool(op.get('parent_unit_ids')) for op in production),
        precision_operations=sum(op['mode'] == 'precision' for op in production),
        tool_services=sum(op['kind'] == 'tool_service' for op in ops),
        machine_maintenance=sum(op['kind'] == 'maintenance' for op in ops),
        worker_attendance_ticks={wid:union_length(worker_time[wid]) for wid in sorted(workers)},
        worker_walk_ticks={wid:union_length(worker_walk[wid]) for wid in sorted(workers)},
        worker_occupied_ticks={wid:union_length(worker_time[wid] + worker_walk[wid]) for wid in sorted(workers)},
        worker_walks=len(trace['worker_moves']),
        loaded_moves=sum(move['kind'] == 'transport' for move in moves),
        loaded_moves_definition='all transport commitments, including part and tool transports',
        part_moves=sum(move.get('kind', 'transport') == 'transport' and move.get('entity_type', 'part') == 'part' for move in moves),
        tool_moves=sum(move.get('entity_type') == 'tool' for move in moves),
        agv_charge_sessions=len(charges), agv_charge_ticks=sum(observed(move['charge_start'], move['end']) for move in charges),
        empty_travel_ticks=sum(observed(leg['start'], leg['end']) for move in moves for leg in move.get('legs', []) if not leg['loaded']),
        loaded_travel_ticks=sum(observed(leg['start'], leg['end']) for move in moves for leg in move.get('legs', []) if leg['loaded']),
        event_counts=dict(Counter(event['type'] for event in events)),
        qa_failures=sum(event['type'] == 'qa_result' and not event['passed'] for event in events),
        minimum_observed_raw_stock=minimum, terminal_raw_stock=stock,
        raw_stock_exhaustion_observed=any(value == 0 for value in minimum.values()),
        raw_stock_scope='Inventory states only; trace does not record denied release attempts or prove marginal stock value',
        battery_discharge_ticks=sum(row['battery_action'] == 'discharge' for row in energy),
        battery_charge_ticks=sum(row['battery_action'] == 'charge' for row in energy),
        solar_generation_ticks=sum(row['solar_kw'] > 0 for row in energy),
        min_grid_headroom_kw=min((row['cap_kw'] - row['grid_kw'] for row in energy), default=None),
        derated_grid_ticks=sum(row['cap_kw'] < instance['energy']['normal_grid_cap_kw'] for row in energy),
        max_local_total_bits=max((decision['result']['qubo']['variables'] for decision in decisions), default=0),
        local_calls=len(decisions), simulated_qaoa_calls=sum(decision['result'].get('quantum_algorithm_simulated', False) for decision in decisions),
        enabled_mechanisms=instance.get('feature_status', {}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    data = args.trace.read_bytes()
    plain = gzip.decompress(data) if args.trace.suffix == '.gz' else data
    result = audit(json.loads(plain))
    result['source_trace'] = dict(path=str(args.trace.resolve()), file_sha256=hashlib.sha256(data).hexdigest(), json_sha256=hashlib.sha256(plain).hexdigest())
    result['activity_audit_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key:result[key] for key in ('production_machines_used', 'setup_operations', 'tool_services', 'worker_walks', 'rework_operations', 'agv_charge_sessions', 'minimum_observed_raw_stock')}))


if __name__ == '__main__':
    main()
