"""Complete deterministic pump/BOM scheduling cells derived from factory data.

This extends the declared window problem from housing prefixes to all component
recipes plus assembly and final QA. Transport remains uncapacitated minimum
lags; no tool, buffer, AGV, setup, quality or power claim is implied.
"""
from fractions import Fraction
import math

from .bounds import shortest_costs
from .spec import build
from .window_experiments import factory_cell
from .window_qubo import digest


def pump_cell(jobs=2,horizon=1440,grid=30,origin=2160,metric_setups=False):
    if not 1<=jobs<=8:raise ValueError('Development cap:8 pumps')
    source=build(max(12,jobs),seed=0);p=factory_cell(1,5,horizon,grid,origin)
    p['machines']={m['id']:dict(hall=m['hall'],available=[[0,horizon]])for m in source['machines']}
    distances=shortest_costs(source,lambda e:e['ticks']);handling=source['transport']['load_ticks']+source['transport']['unload_ticks']
    p['transport_lags']={a:{b:(0 if a==b else distances[a][b]+handling)for b in p['machines']}for a in p['machines']}
    p['operations']=[]
    for order in source['orders'][:jobs]:
        components=[]
        for kind in ('housing','rotor','flange','pump'):
            prior=list(components)if kind=='pump'else[]
            for k,step in enumerate(source['recipes'][kind]):
                process=step['process'];mode='precision'if process=='QA'and order['precision_required']else'standard'
                a,b=source['modes'][process][mode]['duration_factor']
                durations={m['id']:math.ceil(Fraction(step['base_ticks']*a*m['duration_factor'][0],b*m['duration_factor'][1]))for m in source['machines']if m['process']==process}
                release=max(0,order['release_tick']-origin);initial={}
                if not prior:initial={m:release+distances['RAW_A'][m]+handling for m in durations}
                rule=source['attendance'][process];oid=f'{order["id"]}/{kind}/step{k}'
                p['operations'].append(dict(id=oid,durations=durations,skill=source['process_skills'][process],
                    attendance=rule['kind'],start_attendance=rule['ticks'],release=release,machine_release=initial,
                    due=order['due_tick']-origin,predecessors=list(prior),family=order['family']))
                prior=[oid]
            if kind!='pump':components+=prior
    p['name']=f'factory-derived deterministic full BOM:{jobs}pumps/{len(p["operations"])}operations'
    p['provenance'].update(factory_instance_sha256=digest(source),remaining_recipe='All housing/rotor/flange steps, three-parent assembly join, final pump QA; shipping excluded',
        current_claim='Complete declared deterministic pump/BOM cell QUBO. Full physical factory constraints listed as excluded remain excluded.')
    if metric_setups:
        p['machine_setups']=source['setup_matrix']
        p['provenance']['setup_scope']='Actual family transition durations; machine-only automated changeover model. Human setup crews, tool service and downtime calendars excluded. Directed triangle inequality verified; all-pair lag inequalities exactly represent adjacent sequence changes.'
        p['provenance']['excluded']=[x for x in p['provenance']['excluded']if x!='sequence-dependent setups']+['human setup crew scheduling']
    return p
