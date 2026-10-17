"""Post-hoc membership/energy certificate from retained recovery evidence.

No optimizer, SDK, network client or sampling is invoked. The known enriched
optimum is used as a diagnostic teacher, never as a new blind search method.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from stage2.operation_qubo import compile_operations
from stage2.window_qubo import check_plan, digest


def explain():
    names = {
        'problem': 'output/manufacturing-recovery-v2/heat-lease-32/problem.json',
        'columns': 'output/manufacturing-recovery-v2/heat-lease-32/columns.json',
        'original_report': 'output/manufacturing-recovery-v2/heat-lease-32/report.json',
        'nested_baseline': 'output/capacity-frontier-review-v1/heat-lease-32/baseline.json',
        'enriched_report': 'output/capacity-frontier-review-v1/heat-lease-32/cap-64/report.json',
    }
    inputs = {key: json.loads((ROOT / path).read_text()) for key, path in names.items()}
    problem, columns = inputs['problem'], inputs['columns']
    original, enriched = inputs['original_report'], inputs['enriched_report']['reference']
    assert digest(columns) == digest(inputs['nested_baseline']) == original['pool']['pool_sha256']
    assert enriched['optimal'] and enriched['check']['objective'] == 855
    plan = enriched['plan']
    checked = check_plan(problem, plan)
    assert checked['valid'] and checked['objective'] == 855
    assert original['pool_reference']['optimal'] and original['pool_reference']['objective'] == 65790
    full = original['raw_reference']
    assert full['optimal'] and full['objective'] == full['bound'] == 855
    assert check_plan(problem, full['plan'])['objective'] == 855

    domain = {op: {digest(option) for option in options} for op, options in columns.items()}
    missing = [row for row in plan if digest([row]) not in domain[row['operation']]]
    assert len(missing) == 1
    base = compile_operations(problem, columns)
    assert len(base.variables) == original['pool']['variables'] == 781
    assert len(base.quadratic) == original['pool']['couplers'] == 26307
    try:
        base.encode(plan)
    except ValueError as error:
        assert missing[0]['operation'] in str(error)
    else:
        raise AssertionError('Original pool unexpectedly represents the recovery witness')

    augmented = deepcopy(columns)
    for row in missing:
        augmented[row['operation']].append([deepcopy(row)])
    model = compile_operations(problem, augmented)
    bits = model.encode(plan)
    decoded = model.decode(bits)
    assert decoded['valid'] and model.energy(bits) == decoded['objective'] == 855
    assert len(model.variables) == 782
    h3 = [dict(row, already_in_original_pool=digest([row]) in domain[row['operation']])
          for row in plan if row['machine'] == 'H3']
    assert h3 and all(row['already_in_original_pool'] for row in h3)
    report = dict(
        status='passed', scope='Post-hoc diagnostic using a retained enriched optimum; not a blind generator or solver benchmark',
        original=dict(variables=len(base.variables), couplers=len(base.quadratic),
                      retained_exact_objective=65790, retained_weighted_late_minutes=45),
        witness=dict(check=checked, assignments=len(plan), represented_in_original=len(plan)-len(missing),
                     missing_assignments=missing, spare_furnace_assignments=h3),
        augmented=dict(variables=len(model.variables), couplers=len(model.quadratic),
                       compiler_penalty=model.penalty, energy=model.energy(bits),
                       encoded_makespan=decoded['encoded_makespan'], check={key: decoded[key] for key in checked},
                       optimum_certificate='Checked representable witness gives upper bound855; retained complete-model optimum gives lower bound855, since this pool is a restriction of the same raw model'),
        caveats=['The added row was read from a known optimal reference: this is privileged post-hoc diagnosis.',
                 'This does not replace the independently generated 2078-bit enrichment experiment.',
                 '782 is not a lower bound on correct formulation size, and the repair is not a lossless full-domain encoding.',
                 'The existing four sponsor packets and all historical inputs/results are unchanged.',
                 'Compilation uses the original conservative compiler penalty; no sampler performance follows.'],
        input_sha256={path: hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in names.values()},
        optimizer_calls=0, sampling_calls=0, veloxq_calls=0, physical_qpu_calls=0,
    )
    return report, plan, bits, augmented


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report, plan, bits, augmented = explain()
    args.output.mkdir(parents=True, exist_ok=False)
    for name, value in [('report.json', report), ('witness.json', plan), ('bits.json', bits), ('columns.json', augmented)]:
        (args.output/name).write_text(json.dumps(value, indent=2)+'\n')
    sources = [Path(__file__).resolve(), ROOT/'stage2/operation_qubo.py', ROOT/'stage2/column_qubo.py',
               ROOT/'stage2/window_qubo.py', ROOT/'stage2/trajectory_qubo.py']
    for source in sources:
        target = args.output/'sources'/source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    manifest = {str(path.relative_to(args.output)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in args.output.rglob('*') if path.is_file()}
    (args.output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps({key: report[key] for key in ['status', 'original', 'witness', 'augmented', 'optimizer_calls', 'veloxq_calls']}, indent=2))
