"""Independent circuit, literal-energy and fresh-pool transfer checks."""
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from qiskit import qasm2, transpile
from qiskit.quantum_info import Statevector

from .assignment_qaoa import AssignmentSector, sample
from .column_parents import generate
from .column_qubo import compile_columns
from .qaoa_campaign import save
from .qaoa_training import assess, cost_scale
from .recipe_bridge import select_columns
from .window_qubo import check_plan


def dense_evolve(sector, fit):
    """Independent dense matrix per component, rather than pair-slice updates."""
    tensor = np.full(sector.sizes, 1 / np.sqrt(len(sector.energies)), dtype=complex)
    diagonal = (sector.energies.astype(float) - float(sector.energies[0])) / fit['scale']
    for gamma, beta in zip(fit['gammas'], fit['betas']):
        tensor *= np.exp(-1j * gamma * diagonal).reshape(sector.sizes)
        for axis, size in enumerate(sector.sizes):
            mixer = np.eye(size, dtype=complex)
            for j in range(size - 1):
                gate = np.eye(size, dtype=complex)
                gate[j, j] = gate[j + 1, j + 1] = np.cos(beta)
                gate[j, j + 1] = gate[j + 1, j] = -1j * np.sin(beta)
                mixer = gate @ mixer
            tensor = np.moveaxis(np.tensordot(mixer, tensor, axes=(1, axis)), 0, axis)
    return tensor.reshape(-1)


def checked_samples(problem, sector, assessment):
    selected = []
    for run in assessment['runs']:
        if sum(run['observed_counts'].values()) != run['shots']:
            raise AssertionError('Shot accounting failed')
        seen = [int(i) for i in run['observed_counts']]
        winner = min(seen, key=lambda i: (int(sector.energies[i]), i))
        bits = sector.bits(winner)
        if bits != run['bits'] or sector.q.energy(bits) != run['energy']:
            raise AssertionError('Return is not the best measured literal state')
        decoded = sector.q.decode(bits)
        valid = decoded['valid']
        if valid:
            check = check_plan(problem, decoded['plan'])
            if not check['valid'] or check['objective'] != decoded['objective']:
                raise AssertionError('Independent raw schedule check failed')
        selected.append(dict(seed=run['seed'], valid=valid, energy=run['energy'],
                             optimal=valid and run['energy'] == assessment['sector_exact_energy']))
    return selected


def run(campaign, polish, output):
    output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[1]
    hashes = {}
    for name in ['qaoa_audit.py', 'qaoa_training.py', 'assignment_qaoa.py', 'column_qubo.py',
                 'recipe_bridge.py', 'column_parents.py', 'window_qubo.py', 'trajectory_qubo.py']:
        data = (root / 'stage2' / name).read_bytes()
        target = output / 'sources' / 'stage2' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        hashes[name] = hashlib.sha256(data).hexdigest()
    save(output / 'protocol.json', dict(campaign=str(campaign), polish=str(polish),
         final_selection='Final alpha1 expectation selection, with no exact-hit-rate selection',
         transfer_parent_seeds=[20181, 30181], parents_wanted=64, attempts=256, cap=4,
         transfer='New constructive pools on the SAME TWO KNOWN physical problems; zero extra fit. '
                  'Transfer gamma/beta with fresh coefficient scale. Not unseen physical-instance validation.',
         independent_checks='Dense per-group matrix replay of final36qubit sector; logical QASM transpilation; '
                            'full-Hilbert replay of same angles on18qubit cap2 circuits',
         source_hashes=hashes, physical_qpu_calls=0, remote_calls=0))
    began = time.perf_counter()
    rows, transfers = [], []
    for case in ['heat-outage-32', 'heat-lease-32']:
        directory = output / case
        directory.mkdir()
        problem = json.loads((campaign / case / 'problem.json').read_text())
        columns = json.loads((campaign / case / 'columns.json').read_text())
        sector = AssignmentSector.build(compile_columns(problem, columns))
        final_path = polish / case / 'selected-alpha-1.0.json'
        final = json.loads(final_path.read_text())
        fit = final['fit']
        assessment = final['assessment']
        expected = sector.evolve(fit['gammas'], fit['betas'], fit['scale'])
        independent = dense_evolve(sector, fit)
        error = float(np.max(np.abs(independent - expected)))
        if error > 1e-10:
            raise AssertionError('Independent sector replay mismatch')
        for index in np.random.default_rng(331).integers(len(sector.energies), size=4096):
            if sector.q.energy(sector.bits(index)) != int(sector.energies[index]):
                raise AssertionError('Literal energy mismatch')
        circuit = qasm2.loads(assessment['qasm']).remove_final_measurements(inplace=False)
        compiled = transpile(circuit, basis_gates=['rz', 'sx', 'x', 'cx'], optimization_level=1, seed_transpiler=7)
        (directory / 'selected.qasm').write_text(assessment['qasm'])
        (directory / 'compiled.qasm').write_text(qasm2.dumps(compiled))
        selected = checked_samples(problem, sector, assessment)
        # Full-Hilbert circuit replay is practical at cap2, with18 logical qubits.
        historical = root / 'output' / 'recipe-bridge-review-v2' / case / 'cap-2' / 'columns.json'
        small = AssignmentSector.build(compile_columns(problem, json.loads(historical.read_text())))
        small_fit = dict(fit, scale=cost_scale(small))
        qasm = small.circuit(fit['gammas'], fit['betas'], small_fit['scale'])
        small_circuit = qasm2.loads(qasm).remove_final_measurements(inplace=False)
        full = Statevector.from_instruction(small_circuit).probabilities()
        indices = np.array([sum(b << i for i, b in enumerate(small.bits(k))) for k in range(len(small.energies))])
        small_probability = abs(small.evolve(fit['gammas'], fit['betas'], small_fit['scale'])) ** 2
        circuit_error = float(np.max(abs(full[indices] - small_probability)))
        leakage = float(max(0, full.sum() - full[indices].sum()))
        if max(circuit_error, leakage) > 1e-10:
            raise AssertionError('Independent full-Hilbert circuit mismatch')
        row = dict(case=case, layers=fit['layers'], logical_qubits=circuit.num_qubits,
                   sector_amplitude_error=error, cap2_full_hilbert_probability_error=circuit_error,
                   cap2_leakage=leakage, cap2_qubits=small_circuit.num_qubits,
                   compiled_gates=dict(compiled.count_ops()), logical_depth=compiled.depth(),
                   selected_runs=selected, hit=assessment['exact_hit_probability'], feasible=assessment['feasible_probability'])
        cvar = json.loads((polish / case / 'initial-selection.json').read_text())
        cfit, cassessment = cvar['fit'], cvar['assessment']
        cexpected = sector.evolve(cfit['gammas'], cfit['betas'], cfit['scale'])
        cerror = float(np.max(abs(dense_evolve(sector, cfit) - cexpected)))
        csmall = qasm2.loads(small.circuit(cfit['gammas'], cfit['betas'], cost_scale(small))).remove_final_measurements(inplace=False)
        cfull = Statevector.from_instruction(csmall).probabilities()
        cprobability = abs(small.evolve(cfit['gammas'], cfit['betas'], cost_scale(small))) ** 2
        cprob_error = float(np.max(abs(cfull[indices] - cprobability)))
        cleak = float(max(0, cfull.sum() - cfull[indices].sum()))
        if max(cerror, cprob_error, cleak) > 1e-10:
            raise AssertionError('Independent CVaR variant replay mismatch')
        ccircuit = qasm2.loads(cassessment['qasm']).remove_final_measurements(inplace=False)
        ccompiled = transpile(ccircuit, basis_gates=['rz', 'sx', 'x', 'cx'], optimization_level=1, seed_transpiler=7)
        (directory / 'cvar-selected.qasm').write_text(cassessment['qasm'])
        (directory / 'cvar-compiled.qasm').write_text(qasm2.dumps(ccompiled))
        row['cvar_variant'] = dict(layers=cfit['layers'], sector_amplitude_error=cerror,
                                  cap2_probability_error=cprob_error, cap2_leakage=cleak,
                                  compiled_gates=dict(ccompiled.count_ops()), logical_depth=ccompiled.depth(),
                                  selected_runs=checked_samples(problem, sector, cassessment))
        row['intermediate_variants'] = []
        for alpha in (.5, .75):
            middle = json.loads((polish / case / f'selected-alpha-{alpha}.json').read_text())
            mfit, massessment = middle['fit'], middle['assessment']
            merror = float(np.max(abs(dense_evolve(sector, mfit) -
                                     sector.evolve(mfit['gammas'], mfit['betas'], mfit['scale']))))
            if merror > 1e-10:
                raise AssertionError('Intermediate variant sector replay failed')
            row['intermediate_variants'].append(dict(alpha=alpha, sector_amplitude_error=merror,
                selected_runs=checked_samples(problem, sector, massessment)))
        rows.append(row)
        print(json.dumps(row), flush=True)
        for seed in [20181, 30181]:
            target = directory / f'transfer-{seed}'
            target.mkdir()
            parents = generate(problem, attempts=256, wanted=64, seed=seed, seconds=12)
            new_columns = select_columns(problem, parents['parents'], 4, 'first_and_incumbent')
            save(target / 'parents.json', parents)
            save(target / 'columns.json', new_columns)
            fresh = AssignmentSector.build(compile_columns(problem, new_columns))
            transferred = assess(fresh, dict(fit, scale=cost_scale(fresh)), seeds=tuple(range(211, 221)))
            baseline = sample(fresh, seed=7, evaluations=64, layers=2, alpha=.25, shots=512)
            save(target / 'transferred.json', transferred)
            save(target / 'baseline.json', baseline)
            controls = [sample(fresh, method='sa_onehot', seed=s, shots=512, sweeps=256) for s in (7, 13, 29)]
            save(target / 'sa-controls.json', controls)
            uniform = float(np.mean(fresh.energies == fresh.energies.min()))
            transfer = dict(case=case, parent_seed=seed, logical_qubits=len(fresh.q.linear), sector_states=len(fresh.energies),
                            transferred_hit=transferred['exact_hit_probability'],
                            baseline_hit=baseline['exact_hit_probability'], uniform_hit=uniform,
                            selected_runs=checked_samples(problem, fresh, transferred),
                            sa_optimal_runs=sum(c['decoded']['valid'] and c['energy'] == int(fresh.energies.min()) for c in controls))
            transfers.append(transfer)
            print(json.dumps(transfer), flush=True)
    report = dict(rows=rows, transfers=transfers, valid=True, wall_seconds=time.perf_counter() - began,
                  source_stable=all(hashlib.sha256((root / 'stage2' / n).read_bytes()).hexdigest() == sha for n, sha in hashes.items()),
                  physical_qpu_calls=0, remote_calls=0)
    save(output / 'report.json', report)
    save(output / 'manifest.json', {str(path.relative_to(output)): hashlib.sha256(path.read_bytes()).hexdigest()
                                    for path in output.rglob('*') if path.is_file()})
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign', type=Path, required=True)
    parser.add_argument('--polish', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.campaign.resolve(), args.polish.resolve(), args.output.resolve())
