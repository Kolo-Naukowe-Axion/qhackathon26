"""Aggregate every retained screen row; run after report.json is complete."""
import json
from pathlib import Path

folder=Path(__file__).resolve().parent
report=json.loads((folder/'report.json').read_text())
summary=[];paired=[]
for group in report['groups']:
    rows=group['rows']
    baseline={row['seed']:row for row in rows if row['variant']=='neither'}
    for variant in report['variants']:
        selected=[row for row in rows if row['variant']==variant]
        qa=sum(sum(count for mode,count in row['mode_counts'].items() if mode.startswith('QA:')) for row in selected)
        failures=sum(row['qa_failures'] for row in selected)
        summary.append(dict(orders=group['orders'],variant=variant,runs=len(selected),
            fulfilled_cases=sum(row['metrics']['all_orders_fulfilled'] for row in selected),
            demand=sum(row['metrics']['orders'] for row in selected),
            shipped=sum(row['metrics']['shipped'] for row in selected),
            missing=sum(row['metrics']['orders']-row['metrics']['shipped'] for row in selected),
            terminal_deadline_debt_ticks=sum(row['metrics']['total_tardiness_ticks'] for row in selected),
            qa_inspections=qa,qa_failures=failures,qa_failure_fraction=failures/qa if qa else None,
            repairs=sum(row['repair_events'] for row in selected),scraps=sum(row['scrap_events'] for row in selected),
            replacements=sum(row['replacement_events'] for row in selected),
            careful_operations=sum(row['careful_operations'] for row in selected),
            welding_processing_ticks=sum(row['process_ticks']['S'] for row in selected),
            assembly_processing_ticks=sum(row['process_ticks']['ASSEMBLY'] for row in selected),
            energy_cost=sum(row['metrics']['energy_cost'] for row in selected),
            wall_seconds=sum(row['wall_seconds'] for row in selected)))
        for row in selected:
            b=baseline[row['seed']]
            paired.append(dict(orders=group['orders'],seed=row['seed'],variant=variant,
                shipped_delta=row['metrics']['shipped']-b['metrics']['shipped'],
                terminal_deadline_debt_delta=row['metrics']['total_tardiness_ticks']-b['metrics']['total_tardiness_ticks'],
                qa_failures_delta=row['qa_failures']-b['qa_failures'],
                energy_cost_delta=row['metrics']['energy_cost']-b['metrics']['energy_cost']))
result=dict(scope='All96 TRAIN rows; paired seeds; no validation/final performance claim',
    caution='Fewer QA failures can reflect reduced completed work; tardiness uses actual delivery ticks for shipped orders and horizon censoring for unfulfilled orders',
    source_report=str(folder/'report.json'),valid=report['valid'],source_stable=report['source_stable'],
    summary=summary,paired=paired)
(folder/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
for row in summary:print(row)
