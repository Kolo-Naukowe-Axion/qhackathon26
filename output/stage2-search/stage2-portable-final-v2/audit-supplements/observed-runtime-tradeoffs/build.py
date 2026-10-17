"""Read-only final runtime/quality extraction. No factory runs or statistical refits."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / 'output/stage2-search/final-complete-report'
ACCOUNTING = ROOT / 'output/stage2-search/final-compute-0127-summary.json'
SELECTED = {12: 'static-grid-12', 16: 'cem6-2026-16', 24: 'cem6-2026-24'}
FAMILIES = [
    ('static-grid', 'Broad static grid', 'static'),
    ('static-matched18', 'Domain-matched static', 'static'),
    ('original-strong', 'Original strong static', 'static'),
    ('ppo6-2026', 'PPO6 fit 2026', 'ppo'),
    ('ppo6-2027', 'PPO6 fit 2027', 'ppo'),
    ('cem6-2026', 'CEM6 fit 2026', 'cem'),
    ('mpc', 'MPC', 'mpc'),
    ('no-batch-sa', 'No-batch SA', 'local'),
    ('no-batch-qaoa', 'No-batch simulated QAOA', 'local'),
    ('no-batch-uniform', 'No-batch uniform', 'local'),
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def close(a, b):
    assert math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-9), (a, b)


def main():
    source_files = {str(p.relative_to(ROOT)): sha(p) for p in [SOURCE / 'all-groups.json', SOURCE / 'report.json', ACCOUNTING]}
    groups = load(SOURCE / 'all-groups.json')
    accounting = load(ACCOUNTING)
    for p, expected in accounting['inputs'].items():
        assert sha(ROOT / p) == expected, p
        source_files[p] = expected
    selected_groups = []
    for n in SELECTED:
        for prefix, label, family in FAMILIES:
            method_id = f'mpc-{2 if n == 16 else 4}future-{n}' if prefix == 'mpc' else f'{prefix}-{n}'
            matches = [g for g in groups if g['method_id'] == method_id and g['config'] == {'orders': n, 'horizon': 5760, 'profile': 'full'}]
            assert len(matches) == 1, method_id
            selected_groups.append((matches[0], label, family))

    manifests, evaluations, artifacts = {}, {}, {}
    all_raw = defaultdict(list)
    physical_by_environment = defaultdict(set)
    for directory in sorted({g['source_evidence']['directory'] for g, _, _ in selected_groups}):
        example = next(g for g, _, _ in selected_groups if g['source_evidence']['directory'] == directory)
        for evidence in example['source_evidence']['files'].values():
            p = Path(evidence['path'])
            assert sha(p) == evidence['sha256'], p
            source_files[str(p.relative_to(ROOT))] = evidence['sha256']
        manifest = load(Path(directory) / 'manifest.json')
        evaluation = load(Path(directory) / 'evaluation.json')
        assert evaluation['missing_or_invalid'] == 0
        manifests[directory] = manifest
        evaluations[directory] = {k: evaluation[k] for k in ['runtime', 'inference_cost_scope', 'training_cost_scope', 'statistical_scope']}
        for r in evaluation['rows']:
            all_raw[(directory, r['method_id'])].append(r)

    rows, audits = [], []
    for g, label, family in selected_groups:
        directory = g['source_evidence']['directory']
        method_id, n = g['method_id'], g['config']['orders']
        manifest = manifests[directory]
        method = next(m for m in manifest['methods'] if m['id'] == method_id)
        raw = all_raw[(directory, method_id)]
        envs = defaultdict(list)
        for r in raw:
            assert r['valid'] and r['terminal_requirements_met'] and r['identity_audit']['valid']
            assert r['config'] == g['config']
            envs[(r['leaf'], r['seed'], r['tape_id'])].append(r)
            physical_by_environment[(n, r['seed'])].add(r['physical_instance_sha256'])
        actors = sorted({r['policy_seed'] for r in raw})
        assert len(envs) == 256 and len(raw) == 256 * len(actors)
        assert g['summary']['actor_replicas'] == len(actors) and g['summary']['invalid'] == 0
        weighted = defaultdict(float)
        leaf_counts = defaultdict(int)
        total_weight = 0.0
        for (leaf, _, _), rs in envs.items():
            assert sorted(r['policy_seed'] for r in rs) == actors
            weights = {r['tape_weight'] for r in rs}
            assert len(weights) == 1
            w = weights.pop()
            total_weight += w
            leaf_counts[leaf] += 1
            for key in ['cpu_seconds', 'wall_seconds', 'planning_wall_seconds', 'checker_wall_seconds', 'controller_inference_cpu_seconds']:
                weighted[key] += w * math.fsum(r[key] for r in rs) / len(rs)
            weighted['missing_orders'] += w * math.fsum(r['metrics']['orders'] - r['metrics']['shipped'] for r in rs) / len(rs)
            weighted['all_fulfilled'] += w * math.fsum(r['metrics']['all_orders_fulfilled'] for r in rs) / len(rs)
            weighted['deadline_debt_ticks'] += w * math.fsum(r['metrics']['total_tardiness_ticks'] for r in rs) / len(rs)
        close(total_weight, 1)
        assert set(leaf_counts.values()) == {32} and len(leaf_counts) == 8
        for key in ['cpu_seconds', 'wall_seconds', 'planning_wall_seconds', 'checker_wall_seconds', 'controller_inference_cpu_seconds']:
            close(weighted[key], g['cost']['timings'][key]['weighted_actor_mean_environment'])
        close(weighted['missing_orders'], g['summary']['metrics']['unfulfilled']['mean'])
        close(weighted['all_fulfilled'], g['summary']['probability_all_orders_fulfilled'])
        close(weighted['deadline_debt_ticks'], g['summary']['metrics']['total_tardiness_ticks']['mean'])
        checkpoint = method.get('checkpoint')
        if checkpoint:
            artifact = manifest['artifacts'][checkpoint]
            md = artifact['metadata']
            key = artifact['sha256']
            retained = {
                'checkpoint_sha256': key, 'checkpoint_path_in_manifest': checkpoint,
                'fit_episodes': md['fit_episodes'], 'reused_validation_episodes': md['validation_episodes'],
                'fit_wall_seconds': md['actual_wall_seconds'], 'configured_workers': md['workers'],
                'fit_seed': md['seed'], 'method': md['method'],
                'shared_prior_context_provenance': [c['selection_provenance'] for c in md['contexts']],
                'cost_scope': 'One shared historical fit across 12/16/24 contexts. Wall × workers is not measured process CPU; do not multiply by final episodes or add to the accounting ledger again.',
            }
            if key in artifacts:
                assert artifacts[key] == retained
            artifacts[key] = retained
        result = {
            'orders': n, 'horizon_minutes': 5760, 'profile': 'full',
            'method_id': method_id, 'label': label, 'family': family,
            'preselected_classical_controller': method_id == SELECTED[n],
            'cohort': g['cohort'], 'environment_tapes': 256, 'actors': len(actors), 'actor_seeds': actors,
            'literal_executions': len(raw),
            'weighted_episode_cpu_seconds': g['cost']['timings']['cpu_seconds']['weighted_actor_mean_environment'],
            'weighted_episode_wall_seconds': g['cost']['timings']['wall_seconds']['weighted_actor_mean_environment'],
            'mean_missing_orders': g['summary']['metrics']['unfulfilled']['mean'],
            'weighted_all_fulfilled': g['summary']['probability_all_orders_fulfilled'],
            'mean_horizon_censored_deadline_debt_minutes': g['summary']['metrics']['total_tardiness_ticks']['mean'],
            'nested_timing_summary': g['cost']['timings'],
            'local_selector_execution_totals': g['cost']['qubo_literal_execution_totals'],
            'local_selector_size_maxima': g['cost']['qubo_maxima'],
            'checkpoint_sha256': artifacts[manifest['artifacts'][checkpoint]['sha256']]['checkpoint_sha256'] if checkpoint else None,
            'manifest_sha256': g['manifest_sha256'],
            'method_definition': method, 'source_evidence': g['source_evidence'],
        }
        rows.append(result)
        audits.append({'method_id': method_id, 'weighted_values_recomputed_from_original_rows': dict(weighted), 'leaf_environment_counts': dict(leaf_counts), 'rows': len(raw)})
    assert all(len(v) == 1 for v in physical_by_environment.values())
    assert len(physical_by_environment) == 3 * 256

    report = {
        'schema': 'stage2-observed-runtime-quality-tradeoffs.v1',
        'scope': 'Observed final CPU-simulation resources; descriptive point estimates only. No new runs, bootstrap, policy selection, hardware/QPU execution or normalized speedup claim.',
        'selection': 'Fixed named families before extraction; both PPO6 fit seeds and every stochastic actor retained; legacy excluded. Selected frontier unchanged.',
        'weighting': 'Average actors within each of 256 environments, then sum leaf probability/32 weighted environment means. 768 stochastic executions are 256 environments × 3 actors.',
        'timing_scope': 'Whole measured episode process CPU includes setup/hashing/checkpoint loading, simulation, online MPC futures/optimization and final independent checking. Worker startup/imports and trace JSON writing are outside parts of the timer. Planning/check/inference are nested and must not be added. CPU seconds are not campaign wall time.',
        'comparability': 'Same 96h physical factory contexts and keyed environments, but controller domains, outer policies, prior searches, runtime source versions and online budgets differ. Only no-batch SA/QAOA/uniform are matched local-selector controls; no equal-budget tournament or causal inference from runtimes.',
        'quality_scope': 'Missing includes original and realized urgent orders. Debt includes unfinished orders censored at the 96h cutoff; this is not realized final lateness. All-fulfilled is a weighted empirical estimate, not a true probability guarantee; zero observed at n24 is not proof of impossibility.',
        'preselected_methods': SELECTED,
        'rows': rows,
        'shared_checkpoint_costs_deduplicated_by_sha256': list(artifacts.values()),
        'shared_development_costs': 'Static grids, strong-prior development, MPC selection, selector reward studies, both PPO fits and CEM fit are not free. Costs overlap and are not allocated uniquely to methods. Use frozen manifests for provenance and the as-of scheduler ledger for shared costs, not a per-episode training surcharge.',
        'accounting_as_of': accounting,
        'execution_cohorts': evaluations,
        'audit': {'all_source_hashes_verified': True, 'all_30_group_means_recomputed': True, 'all_768_context_environment_identities_match_across_methods': True, 'checks': audits},
        'source_sha256': source_files,
        'builder_sha256': sha(__file__),
    }
    write(OUT / 'report.json', report)
    columns = ['orders', 'horizon_minutes', 'method_id', 'preselected_classical_controller', 'weighted_episode_cpu_seconds', 'mean_missing_orders', 'weighted_all_fulfilled', 'mean_horizon_censored_deadline_debt_minutes', 'environment_tapes', 'actors', 'literal_executions', 'cohort']
    with (OUT / 'table.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore'); writer.writeheader(); writer.writerows(rows)
    lines = ['# Observed final CPU-simulation tradeoffs', '', 'All contexts use a 96-hour factory horizon. ★ marks the preselected classical controller; no final reselection. These are weighted episode process CPU seconds, not normalized speedups. Actors are nested within 256 environments.', '']
    for n in SELECTED:
        lines += [f'## {n} initial orders (+ realized urgent orders)', '', '| Exact method ID | CPU s/episode | Mean missing | Weighted fulfilled | Actors |', '|---|---:|---:|---:|---:|']
        for r in [r for r in rows if r['orders'] == n]:
            lines.append(f"| `{r['method_id']}`{' ★' if r['preselected_classical_controller'] else ''} | {r['weighted_episode_cpu_seconds']:.3f} | {r['mean_missing_orders']:.5f} | {100*r['weighted_all_fulfilled']:.3f}% | {r['actors']} |")
        lines.append('')
    lines += ['Fit costs below are shared across all three loads and are shown once per checkpoint; they are neither episode CPU nor uniquely attributable total development cost.', '', '| Shared checkpoint | Fit episodes | Reused VAL episodes | Fit wall s | Configured workers |', '|---|---:|---:|---:|---:|']
    for a in artifacts.values():
        lines.append(f"| {a['method']}6 / fit {a['fit_seed']} | {a['fit_episodes']} | {a['reused_validation_episodes']} | {a['fit_wall_seconds']:.3f} | {a['configured_workers']} |")
    lines += ['', 'Source hashes, exact definitions, runtime packages/SLURM IDs, independent mean-recomputation checks and as-of shared accounting are retained in `report.json`. No prior search or training is assumed free. The families have different action domains and outer controls; this is not an equal-budget tournament. Historical source versions are retained per manifest. No bootstrap or simulator was run to make this table.', '']
    (OUT / 'table.md').write_text('\n'.join(lines))
    plot(rows)
    for p, digest in source_files.items():
        assert sha(ROOT / p) == digest, f'Source changed during export: {p}'
    write(OUT / 'output-index.json', {'schema': 'stage2-runtime-tradeoff-output-index.v1', 'files': {p.name: sha(p) for p in OUT.iterdir() if p.is_file() and p.name != 'output-index.json'}})
    print(json.dumps({'groups': len(rows), 'literal_executions': sum(r['literal_executions'] for r in rows), 'sources': len(source_files), 'source_unchanged': True, 'simulations_run': 0}))


def plot(rows):
    os.environ.setdefault('MPLCONFIGDIR', '/private/tmp/qh26-runtime-matplotlib')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    style = {'static': ('#596d7b', 's'), 'ppo': ('#b56b2c', '^'), 'cem': ('#457b4d', 'D'), 'mpc': ('#795897', 'P'), 'local': ('#337e9e', 'o')}
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.6), layout='constrained')
    for ax, n in zip(axes, SELECTED):
        rs = [r for r in rows if r['orders'] == n]
        for family, (color, marker) in style.items():
            fs = [r for r in rs if r['family'] == family]
            ax.scatter([r['weighted_episode_cpu_seconds'] for r in fs], [r['mean_missing_orders'] for r in fs], c=color, marker=marker, s=50, alpha=.85, label={'static':'Classical static', 'ppo':'PPO6 (both fits)', 'cem':'CEM6 schedule', 'mpc':'Classical MPC', 'local':'Matched local controls'}[family])
        chosen = next(r for r in rs if r['preselected_classical_controller'])
        ax.scatter([chosen['weighted_episode_cpu_seconds']], [chosen['mean_missing_orders']], facecolors='none', edgecolors='#161d22', linewidth=1.4, s=180, zorder=4)
        ax.annotate('Preselected', (chosen['weighted_episode_cpu_seconds'], chosen['mean_missing_orders']), xytext=(12, -23 if n == 16 else 21), textcoords='offset points', fontsize=8, arrowprops={'arrowstyle':'-', 'lw':.7}, color='#202a30')
        ax.set_xscale('log'); ax.set_xlim(1.7, 400)
        ax.set_title(f'{n} initial orders · 96h factory', fontsize=11)
        ax.set_xlabel('Weighted episode process CPU seconds (log)')
        ax.grid(True, alpha=.18); ax.set_axisbelow(True)
        ax.spines[['top','right']].set_visible(False)
    axes[0].set_ylabel('Weighted mean unfulfilled orders ↓')
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='outside lower center', ncol=5, frameon=False, fontsize=9)
    fig.suptitle('Observed CPU-simulation tradeoffs — different controller domains and prior search costs', fontsize=12)
    for ext in ['png', 'svg']:
        fig.savefig(OUT / f'runtime-quality.{ext}', dpi=180, metadata={'Title':'Observed final CPU simulation resources; no speedup claim'})
    plt.close(fig)


if __name__ == '__main__':
    main()
