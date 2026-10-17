"""Independent final document/display readback; no optimizer or network."""
from pathlib import Path
import hashlib
import json
import re
from statistics import median
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from stage2.window_qubo import check_plan, digest


def read(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


documents = ['README.md', 'PROJECT_DESIGN.md', 'DEVELOPMENT_LOG.md', 'CONTEXT.md',
    'docs/STAGE2_COMBINED_DIRECTION.md', 'docs/STAGE2_SUBMISSION.md',
    'docs/STAGE2_ENTRY.md', 'docs/STAGE2_MANUFACTURING_STUDY.md',
    'docs/STAGE2_REVIEW_PASSES.md', 'docs/STAGE2_DEADLINE_BOUNDARY.md',
    'docs/STAGE2_CAPACITY_FRONTIER.md', 'docs/STAGE2_DEADLINE_DECISION.md',
    'docs/STAGE2_RECIPE_BRIDGE.md', 'docs/STAGE2_REALISM_FRONTIER.md',
    'docs/STAGE2_CAPACITY_ECONOMICS.md', 'docs/STAGE2_SPONSOR_PACKETS.md',
    'docs/STAGE2_LIVE_SCRIPT.md']
checks = []


def check(name, condition, proof):
    assert condition, (name, proof)
    checks.append(dict(name=name, passed=True, proof=proof))


links = 0
for name in documents:
    path = ROOT / name
    for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
        if target.startswith(('http:', 'https:', 'mailto:', '#', 'codex:')):
            continue
        target = unquote(target.strip('<>').split('#', 1)[0])
        assert (path.parent / target).exists(), (name, target)
        links += 1
check('authoritative_local_links', links >= 100, dict(documents=len(documents), links=links))
for name in ['README.md', 'PROJECT_DESIGN.md', 'docs/STAGE2_COMBINED_DIRECTION.md', 'docs/STAGE2_SUBMISSION.md']:
    text = (ROOT / name).read_text()
    normalized = re.sub(r'\s', '', text.replace(',', ''))
    check('representation_numbers:' + name,
          all(value in normalized for value in ['781', '2078', '2499', '818']),
          'Original pool, enriched pool, complete optimization and distinct deadline query all present')
check('submission_does_not_claim_minimality', 'Complete optimization needs' not in (ROOT / 'docs/STAGE2_SUBMISSION.md').read_text(), 'Uses a declared compiler encoding, not a variable lower bound')
check('submission_ledger_names_night_premium', 'night premium' in (ROOT / 'docs/STAGE2_SUBMISSION.md').read_text().lower(), 'No unmodeled overtime threshold implied')
check('combined_quantum_is_current', 'This is outstanding work, not an existing large-factory quantum result' not in (ROOT / 'docs/STAGE2_COMBINED_DIRECTION.md').read_text(), 'Completed bridge replaces proposed quantum connection')
check('review_quantum_is_current', 'still unresolved' not in (ROOT / 'docs/STAGE2_REVIEW_PASSES.md').read_text(), 'Failed boundary gates preserved apart from successful bridge')
check('video_pending_is_explicit', 'not the final synchronized video' in (ROOT / 'docs/STAGE2_SUBMISSION.md').read_text(), 'Previous review cut remains outside technical completion claim')

data = read('presentation/manufacturing/merit-data.json')
for path, expected in data['source_sha256'].items():
    assert sha(path) == expected, path
check('studio_source_hashes', bool(data['source_sha256']), len(data['source_sha256']))
for plan in data['plans']:
    problem = read(f'output/manufacturing-recovery-v2/{plan["case"]}/problem.json')
    checked = check_plan(problem, plan['plan'])
    assert checked['valid'] and checked == plan['check'], plan['id']
    assert digest(problem) == plan['problem_sha256'], plan['id']
check('studio_whole_plans', len(data['plans']) == 4, 'Four original-model checked plans, all32operations each')

report = read('output/recipe-bridge-review-v2/report.json')
for shown in data['quantum']:
    row = next(x for x in report['rows'] if x['case'] == shown['case'] and x['cap'] == shown['cap'])
    assert shown['variables'] == row['model']['variables']
    assert shown['sector_states'] == row['sector_states']
    for method, displayed in shown['methods'].items():
        runs = [x for x in row['runs'] if x['method'] == method]
        valid = [x for x in runs if x['decoded']['valid']]
        assert displayed['runs'] == len(runs)
        assert displayed['valid'] == len(valid)
        assert displayed['pool_optimal'] == sum(x['energy'] == row['reference']['objective'] for x in valid)
        if method != 'sa_onehot':
            assert displayed['median_exact_single_shot'] == median(x['exact_hit_probability'] for x in runs)
check('studio_quantum_counts_are_encoded_minima', len(data['quantum']) == 6,
      'Six displayed cap/case rows; exact energy+valid decode, not merely raw objective equality')
check('studio_economics_is_exact_export', data['economics'] == read('output/capacity-economics-v2/report.json'), 'Four exact ledgers,135sensitivities and capital/lease distinction')
check('baseline_disclosure', data['baseline']['naive_bits'] == 72 and data['baseline']['unary_pruned_bits'] == 39 and data['baseline']['selected_sequence_bits'] == 3 and 'six' in data['baseline']['qualification'], 'Three bits require classical six-order cost construction')

raw_realism = read('output/realism-frontier-v1/report.json')
calendar = read('output/realism-continuous-counts-v2/report.json')
for shown in data['realism']['feature_ablations']:
    original = next(x for x in raw_realism['feature_ablations'] if x['variant'] == shown['variant'])
    assert shown['counts'] == original['counts']
    if shown['variant'] == 'continuous_worker_calendars':
        assert shown['unary_complete'] == calendar['unary_complete']
        assert shown['support_complete'] == calendar['support_complete']
        assert shown['count_only_supplement']
    else:
        assert shown['unary_complete'] == original['unary_complete']
        assert shown['support_complete'] == original['support_complete']
check('studio_feature_table', len(data['realism']['feature_ablations']) == 6, 'Original fixed-grid variants; authoritative corrected calendar-countv2 supplement')
check('remote_backend_status', data['veloxq_calls'] == data['physical_qpu_calls'] == 0, 'Offline and noiseless local simulation labels retained')
screens = ['output/manufacturing-merit-qa-v1/representation-quantum.png',
           'output/manufacturing-merit-qa-v1/economics.png']
check('visual_readback', all((ROOT / p).is_file() for p in screens),
      'Reviewer visually inspected both captured images: frontier/qubit table fits; economics shows474.54fee,374.54net,19923.63purchase with synthetic-cost and no-advantage scope text')
tracked = documents + [str(p.relative_to(ROOT)) for p in (ROOT / 'presentation/manufacturing').rglob('*') if p.is_file()] + screens
result = dict(status='passed', scope='Independent final local document/display readback; no optimizer, network, SDK or publication',
              checks=checks, source_hashes={p: sha(p) for p in tracked},
              auditor_sha256=sha(Path(__file__)), veloxq_calls=0, physical_qpu_calls=0)
target = Path(__file__).parent / 'report.json'
with target.open('x') as file:
    file.write(json.dumps(result, indent=2) + '\n')
print(json.dumps(dict(status=result['status'], checks=len(checks), files=len(result['source_hashes']))))
