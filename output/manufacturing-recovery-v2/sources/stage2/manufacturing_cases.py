"""Full-recipe manufacturing cases, not the small quantum validation fixture."""
from copy import deepcopy
from .window_pump import pump_cell


def production_case(pumps=2,scenario='nominal',grid=30):
    horizon={2:1440,4:2880,8:4320}[pumps]
    p=pump_cell(pumps,horizon,grid,origin=1440,metric_setups=True)
    p['name']=f'{pumps} full pumps / {16*pumps} operations / {scenario}'
    original=deepcopy(p)
    lost='H2'if scenario in ('heat-outage','heat-lease')else'F3'
    if scenario in ('mill-down','rush-and-outage','lease-recovery','heat-outage','heat-lease'):
        # Known full-window withdrawal. No interrupted setup/operation and no
        # invalid combination of intermittent calendars with metric setups.
        del p['machines'][lost]
        for op in p['operations']:
            op['durations'].pop(lost,None)
            op.get('machine_release',{}).pop(lost,None)
        p['transport_lags']={a:{b:v for b,v in row.items()if b!=lost}for a,row in p['transport_lags'].items()if a!=lost}
    if scenario in ('rush-and-outage','lease-recovery','heat-outage','heat-lease'):
        for op in p['operations']:
            if op['id'].startswith('P02/'):
                op['due']=900
    if scenario in ('heat-outage','heat-lease'):
        for op in p['operations']:
            if op['id'].startswith('P01/'):
                op['due']=900
    if scenario=='crew-shortage':
        del p['workers']['W04']
    if scenario in ('lease-recovery','heat-lease'):
        added='H3'if scenario=='heat-lease'else'F4'
        p['machines'][added]=deepcopy(original['machines'][lost])
        keys=list(p['machines'])
        alias=lambda m:lost if m==added else m
        p['transport_lags']={a:{b:(0 if a==b else original['transport_lags'][alias(a)][alias(b)])for b in keys}for a in keys}
        for op,source in zip(p['operations'],original['operations']):
            if lost in source['durations']:
                op['durations'][added]=source['durations'][lost]
                op.setdefault('machine_release',{})[added]=max(360,source.get('machine_release',{}).get(lost,0))
    if scenario not in ('nominal','mill-down','rush-and-outage','lease-recovery','crew-shortage','heat-outage','heat-lease'):
        raise ValueError('Unknown manufacturing scenario')
    p['provenance'].update(synthetic=True,scenario=scenario,
        decision='Full backlog plan at a known disruption boundary; all16 recipe operations per pump remain mandatory.',
        outage='Selected F3 or H2 withdrawn for the entire declared planning window; no in-progress work or setup is erased.',
        lease='F4/H3 copies the withdrawn machine capability/transfer lags; processing starts no earlier than360min, no fee/ROI modeled; first family is neutral as in baseline.',
        rush='When enabled, P02 terminal due date changes from1320 to900min; heat scenarios also tighten P01 from960 to900. Known at planning time.',
        excluded=['Capacitated AGVs','finite buffers','power','tool location/service','stochastic quality/rework','human setup crews','shipment'],
        setup_scope='Machine-only directed-metric family changes on uninterrupted remaining machines; no split setups or mid-operation failure model.',
        data_scope='Factory-derived synthetic parameters; not an industrial dataset or trace-extracted state.')
    return p


def cases():
    result={f'{s}-32':production_case(2,s)for s in ['nominal','mill-down','rush-and-outage','lease-recovery','crew-shortage','heat-outage','heat-lease']}
    result.update({f'nominal-{16*n}':production_case(n)for n in [4,8]})
    return result
