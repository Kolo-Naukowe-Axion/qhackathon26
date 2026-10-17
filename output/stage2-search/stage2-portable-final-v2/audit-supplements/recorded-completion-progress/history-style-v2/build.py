"""Recorded shipment progress inside the fixed H240 final runs; no new runs."""
from collections import defaultdict
from fractions import Fraction
import hashlib,json,math,platform
from pathlib import Path
from stage2.compare_evaluations import load_evidence,select_rows


def build():
    directory=Path('output/stage2-search/final-downloaded/final-frontier-6117515')
    manifest,evaluation,reference=load_evidence(directory)
    config=dict(orders=32,horizon=14400,profile='full')
    rows=select_rows(manifest,evaluation,'selected-stretch-32',config)
    assert len(rows)==256 and manifest['actor_seeds']==[900000]
    protocol=manifest['protocol']['payload'];ship_events=defaultdict(Fraction);complete_events=defaultdict(Fraction)
    demand=Fraction(0);total_weight=Fraction(0);last=0;complete_times=[]
    for row in rows:
        weight=Fraction(*protocol['leaves'][row['leaf']]['probability'])/32
        total_weight+=weight;n=row['metrics']['orders'];demand+=weight*n
        shipments=row['checker_metrics']['delivery_ticks']
        assert n==len(shipments)+row['checker_metrics']['unfulfilled_orders']
        for t in shipments.values():
            assert type(t)is int and 0<=t<=14400
            ship_events[t]+=weight;last=max(last,t)
        if len(shipments)==n:
            t=max(shipments.values());complete_events[t]+=weight;complete_times.append(t)
    assert total_weight==1 and demand==33
    delivered=Fraction(0);fulfilled=Fraction(0);curve=[]
    for t in sorted({0,14400,*ship_events,*complete_events}):
        delivered+=ship_events[t];fulfilled+=complete_events[t]
        curve.append(dict(clock_minutes=t,clock_hours=t/60,mean_delivered=float(delivered),mean_missing_from_final_demand=float(demand-delivered),all_final_demand_shipped_probability=float(fulfilled)))
    selected_clocks=[]
    for hours in (96,108,120,132,144,168,192,216,240):
        t=hours*60;point=max((p for p in curve if p['clock_minutes']<=t),key=lambda p:p['clock_minutes'])
        selected_clocks.append(dict(point,clock_minutes=t,clock_hours=hours))
    final_missing=sum(Fraction(*protocol['leaves'][r['leaf']]['probability'])*r['checker_metrics']['unfulfilled_orders']/32 for r in rows)
    final_success=sum(Fraction(*protocol['leaves'][r['leaf']]['probability'])*r['metrics']['all_orders_fulfilled']/32 for r in rows)
    assert math.isclose(curve[-1]['mean_missing_from_final_demand'],float(final_missing),abs_tol=1e-12)
    assert math.isclose(curve[-1]['all_final_demand_shipped_probability'],float(final_success),abs_tol=1e-12)
    quantiles={str(target):next((p['clock_minutes'] for p in curve if p['all_final_demand_shipped_probability']>=target),None) for target in (.1,.5,.9,.95)}
    return dict(schema='stage2-recorded-final-shipment-progress.v1',method='selected-stretch-32',config=config,environment_tapes=256,actor_seed=900000,
        expected_final_demand=float(demand),curve=curve,selected_clocks=selected_clocks,first_complete_recorded_run_minutes=min(complete_times),latest_recorded_shipment_minutes=last,
        observed_completion_probability_crossing_minutes=quantiles,
        scope='Posthoc descriptive progress within the unchanged preselected H14400 runs. A point at an earlier clock is NOT a new shorter-horizon policy evaluation, terminal-SOC check or optimum certificate. Policies know the original cutoff. All-final-demand refers to realized initial plus urgent orders, including before urgency is revealed. Unfulfilled atH is right-censored; no permanent inability to finish is inferred. No new factory executions, policy selection, primary tests or confidence intervals.',
        source_evidence=reference,protocol_sha256=protocol['protocol_sha256'],source_hashes=manifest['source_hashes'],analysis_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),analysis_python=platform.python_version(),factory_runs=0)


def plot(data,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    points=data['curve'];hours=[p['clock_hours'] for p in points]
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#b5bfc4','axes.labelcolor':'#284455','xtick.color':'#425965','ytick.color':'#425965'})
    fig,(ax,bx)=plt.subplots(1,2,figsize=(11.5,4.5),layout='constrained')
    ax.step(hours,[p['mean_delivered'] for p in points],where='post',color='#295570',lw=2)
    ax.axhline(data['expected_final_demand'],color='#a47b3b',ls='--',lw=1,label='Mean final demand: 33')
    ax.set(ylabel='Probability-weighted mean orders shipped',xlabel='Clock inside the recorded 240-hour run (h)',xlim=(0,240),ylim=(0,35));ax.legend(frameon=False,loc='upper left')
    bx.step(hours,[100*p['all_final_demand_shipped_probability'] for p in points],where='post',color='#295570',lw=2)
    bx.set(ylabel='All final demand shipped: observed probability (%)',xlabel='Clock inside the recorded 240-hour run (h)',xlim=(0,240),ylim=(0,100))
    for a in (ax,bx):
        a.grid(axis='y',color='#e5e9ec',lw=.7);a.set_xticks([0,48,96,144,192,240]);a.axvline(96,color='#b5bfc4',ls=':',lw=1)
    fig.suptitle('The 32-order stress case uses the longer calendar',fontsize=15,color='#203e51')
    for suffix in ('png','svg'):fig.savefig(out/('shipment-progress.'+suffix),dpi=180)
    plt.close(fig)
    return dict(matplotlib=matplotlib.__version__,scope='Descriptive fixed-run progress; not alternate-horizon performance')


if __name__=='__main__':
    out=Path(__file__).resolve().parent;data=build()
    for name in ('report.json','shipment-progress.png','shipment-progress.svg'):
        if (out/name).exists():raise ValueError('Preserve prior export')
    plotting=plot(data,out);data['plotting_runtime']=plotting
    (out/'report.json').write_text(json.dumps(data,indent=2)+'\n')
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()}
    (out/'output-index.json').write_text(json.dumps(hashes,indent=2)+'\n')
    print(json.dumps({key:data[key] for key in ('selected_clocks','first_complete_recorded_run_minutes','latest_recorded_shipment_minutes','observed_completion_probability_crossing_minutes')},indent=2))
