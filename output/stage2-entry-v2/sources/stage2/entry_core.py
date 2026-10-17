"""Complete, explicit manufacturing recovery fixtures for the competition entry.

These synthetic residual cells complement, rather than replace, the original
all-rule pump factory. No hidden future, CP-generated candidate pool or incumbent
objective is used to construct their QUBOs.
"""
from copy import deepcopy


def recovery_cell(horizon=180, spare_mill=True, outage=False, cross_skill=True,
                  pumps=1, urgent=True):
    if horizon % 30 or horizon < 120 or pumps < 1:
        raise ValueError('At least 120 minutes, 30-minute multiples and positive pumps required')
    mids = ['F1', 'T1', 'A1', 'QA1'] + (['F2'] if spare_mill else [])
    machines = {m: dict(hall='A', available=[[0, horizon]]) for m in mids}
    if outage:
        machines['F1']['available'] = [[60, horizon]]
    workers = {
        'machinist': dict(skills=['mill', 'turn'] + (['assembly'] if cross_skill else []),
                          initial_hall='A', available=[[0, horizon]]),
        'finisher': dict(skills=['assembly', 'qa'], initial_hall='A', available=[[0, horizon]]),
    }
    operations = []
    for j in range(pumps):
        prefix = f'P{j + 1:02}'
        due = 120 + j * 90
        definitions = [
            ('housing', {m: 30 for m in mids if m.startswith('F')}, 'mill', [], 0, 1),
            ('rotor', {'T1': 30}, 'turn', [], 0, 1),
            ('assembly', {'A1': 30}, 'assembly', [f'{prefix}/housing', f'{prefix}/rotor'], 0, 1),
            ('qa', {'QA1': 30}, 'qa', [f'{prefix}/assembly'], 0, 2),
        ]
        for step, durations, skill, predecessors, release, weight in definitions:
            operations.append(dict(id=f'{prefix}/{step}', durations=durations, skill=skill,
                                   attendance='full', release=release, due=due, weight=weight,
                                   predecessors=predecessors))
    if urgent:
        operations.append(dict(id='urgent/qa', durations={'QA1': 30}, skill='qa', attendance='full',
                               release=60, due=90, weight=1, predecessors=[]))
    return dict(name='Pump assembly recovery and urgent component inspection', horizon=horizon,
                grid=30, machines=machines, workers=workers, operations=operations,
                transport_lags={m: {n: 0 for n in mids} for m in mids}, worker_travel=0,
                provenance=dict(synthetic=True, recorded_full_factory_snapshot=False,
                    boundary='All earlier housing/rotor steps and flanges are completed. '
                             'Only final housing/rotor machining, pump assembly and inspection remain. '
                             'The urgent separate component is available for inspection at minute 60.',
                    outage='F1 unavailable [0,60) when enabled; no operation interrupted or erased.',
                    material='One preassigned housing, rotor and flange per pump; no substitutions or rework.',
                    included=['alternative milling machine', 'shared skilled workers', 'assembly join',
                              'due dates and weighted terminal tardiness', 'machine outage calendar',
                              'partial-state releases and known boundary material'],
                    excluded=['AGV contention', 'power', 'finite buffers', 'stochastic quality',
                              'sequence-dependent setups', 'worker travel', 'learned control'],
                    objective='(H+1)*weighted terminal tardiness + makespan',
                    scope='Complete discrete residual-cell problem, not lossless full-factory optimization.'))


def entry_cases():
    return {
        'nominal-120': recovery_cell(120),
        'nominal-150': recovery_cell(150),
        'nominal-180': recovery_cell(180),
        'outage-spare': recovery_cell(180, outage=True),
        'outage-no-spare': recovery_cell(180, spare_mill=False, outage=True),
        'without-cross-skill': recovery_cell(180, cross_skill=False),
    }
