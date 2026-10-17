"""Freeze paired-meal quantum and nested scale inputs, with local references.

No SDK clients, credentials, uploads or remote execution. New directories only.
V2 inputs are preserved; V3 has different whole-meal/disposal semantics.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import shutil
import time

import numpy as np

from .contracts import load_bundle
from .decode import decode
from .domain import digest, snapshot
from .meal_blocks import meal_fixture, compile_meal_blocks, sector_data, sector_bits, stratified_pool
from .meal_reference import solve_bundle
from .meal_search import portfolio
from .methods.classical import solve_qubo
from .native_slots import solve_native
from .options import enumerate_options
from .qubo import energy, ising


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+"\n")


def seal(output):
    root = Path(__file__).resolve().parents[1]
    sources = {}
    for source in sorted((root/"catering").rglob("*.py")):
        name = str(source.relative_to(root))
        sources[name] = hashlib.sha256(source.read_bytes()).hexdigest()
        target = output/"source_snapshot"/name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    files = {str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(output.rglob("*")) if p.is_file() and p != output/"manifest.json"}
    save(output/"manifest.json", dict(schema_version="catering-paired-manifest.v1", files=files, sources=sources))


def result_summary(bundle, result):
    valid, shots = [], 0
    for sample in result["samples"]:
        checked = decode(bundle, sample["bits"])
        if int(sample["reported_energy"]) != energy(bundle, sample["bits"]):
            raise AssertionError("Reference sample energy mismatch")
        if checked["valid"]:
            valid.append(checked["check"]["metrics"])
            shots += sample["count"]
    return dict(status=result["status"], reference=result.get("reference"),
                raw_returns=len(result["samples"]), valid_returns=len(valid), valid_shots=shots,
                best_metrics=min(valid, key=lambda m:tuple(m[k] for k in ("U","W","B","R"))) if valid else None,
                timings=result["timings"])


def build(output, customers=6, seed=2026, max_qubits=35, scale_widths=(128,256), seconds=3):
    output = Path(output)
    if output.exists():
        raise ValueError("Fresh release directory required")
    output.mkdir(parents=True)
    started = time.monotonic()
    save(output/"experiment-plan.json", dict(customers=customers, seed=seed, scenarios=["S0","S1","S2","S3"],
         max_quantum_qubits=max_qubits, scale_widths=list(scale_widths), reference_seconds=seconds,
         selection="Seeded empty-incumbent local pair proposals; nested stratified scale enrichment; no reference teacher",
         status="Declared before references; outputs are a foundation release, not a final quantum-performance campaign"))
    instance = meal_fixture(customers)
    save(output/"instance.json", instance)
    rows = []
    for scenario in ("S0","S1","S2","S3"):
        directory = output/scenario
        state = snapshot(instance, scenario)
        save(directory/"snapshot.json", state)
        before = time.monotonic()
        programs = enumerate_options(instance, state)
        generation_s = time.monotonic()-before
        domain_sha = digest([p["id"] for p in programs])
        anchors = len({min(p["allocation_order"]) for p in programs})
        if max_qubits < 2*anchors:
            raise ValueError("All-anchor quantum fixture exceeds its declared cap")
        selected = portfolio(programs, [], min(7,max_qubits-2*anchors), np.random.default_rng(seed), instance, state)
        quantum = compile_meal_blocks(instance, state, selected, parent_domain_sha256=domain_sha)
        sector = sector_data(quantum)
        exact = decode(quantum, sector_bits(quantum, sector, int(sector["energy"].argmin())))
        if not exact["valid"]:
            raise AssertionError("Invalid sector ground state")
        # Check independent literal evaluation and 4E Ising on declared sampled
        # sector rows, including the minimum, rather than trusting the vectorizer.
        zmodel = ising(quantum)
        for index in sorted(set(np.linspace(0,sector["states"]-1,min(32,sector["states"]),dtype=int).tolist()+[int(sector["energy"].argmin())])):
            bits = sector_bits(quantum, sector, index)
            literal = energy(quantum, bits)
            spins = [1-2*b for b in bits]
            spin_energy = int(zmodel["constant"])+sum(int(c)*z for c,z in zip(zmodel["linear"],spins))
            spin_energy += sum(int(t["value"])*spins[t["i"]]*spins[t["j"]] for t in zmodel["quadratic"])
            if literal != int(sector["energy"][index]) or spin_energy != 4*literal:
                raise AssertionError("Literal/sector/Ising disagreement")
        save(directory/"quantum-sector-reference.json", dict(states=sector["states"],
             feasible_states=int(sector["valid"].sum()), ground=exact, status="OPTIMAL in offered quantum portfolio"))
        variants = [("quantum",quantum)]
        # Predeclare a nested donor set. Scale pools retain every quantum choice.
        donors = stratified_pool(programs, min(len(programs),max(scale_widths)))
        chosen = {p["id"]:p for p in selected}
        for width in scale_widths:
            target = width-anchors
            if target < len(chosen):
                raise ValueError("Scale widths must increase and contain the quantum pool")
            for program in donors:
                if len(chosen) >= target:
                    break
                chosen[program["id"]] = program
            bundle = compile_meal_blocks(instance,state,sorted(chosen.values(),key=lambda p:p["id"]),parent_domain_sha256=domain_sha)
            variants.append((f"scale-{width}",bundle))
        raw = solve_native(instance,state,dict(wall_time_limit_s=seconds),dict(workers=4,seed=seed))
        save(directory/"raw-reference.json",raw)
        row = dict(scenario=scenario, common_prefix_sha256=state["common_prefix_sha256"],
                   generation_s=generation_s, full_local_programs=len(programs), full_local_domain_sha256=domain_sha,
                   raw_reference_status=raw["reference_status"], raw_reference_metrics=(raw["check"] or {}).get("metrics"),
                   variants=[])
        previous_ids = set()
        for name,bundle in variants:
            ids = {p["id"] for p in bundle["options"]}
            if not previous_ids <= ids:
                raise AssertionError("Scale enrichment dropped offered choices")
            previous_ids = ids
            save(directory/(name+"-qubo.json"),bundle)
            save(directory/(name+"-ising.json"),ising(bundle))
            load_bundle(directory/(name+"-qubo.json"))
            witness = [0]*bundle["size"]["binary_variables"]
            for group in bundle["onehot_groups"]:
                witness[group["idle_index"]] = 1
            checked = decode(bundle,witness)
            if not checked["valid"]:
                raise AssertionError("All-idle continuation is invalid")
            save(directory/(name+"-witness.json"),dict(bundle_sha256=bundle["bundle_sha256"],
                 kind="Known all-idle witness, not a solver result",bits=witness,decoded=checked))
            cp = solve_bundle(bundle,seconds=seconds,seed=seed)
            sa = solve_qubo(bundle,dict(wall_time_limit_s=0.25),dict(seed=seed,restarts=4,sweeps=100))
            save(directory/(name+"-reference.json"),cp)
            save(directory/(name+"-sa.json"),sa)
            if name == "quantum" and cp["reference"]["status"] == "OPTIMAL":
                if int(cp["reference"]["objective"]) != int(sector["energy"].min()):
                    raise AssertionError("Independent program CP and sector enumeration disagree")
            row["variants"].append(dict(name=name,bundle_sha256=bundle["bundle_sha256"],size=bundle["size"],
                 density=2*bundle["size"]["couplers"]/max(1,bundle["size"]["binary_variables"]*(bundle["size"]["binary_variables"]-1)),
                 encoded_cp=result_summary(bundle,cp),sa=result_summary(bundle,sa),
                 scope="Offered program restriction of the full physical grid; nested across these widths"))
        rows.append(row)
        print(json.dumps(dict(scenario=scenario,quantum_bits=quantum["size"]["binary_variables"],
              domain=len(programs),raw=row["raw_reference_metrics"],offered=[v["encoded_cp"]["best_metrics"] for v in row["variants"]])),flush=True)
    if len({r["common_prefix_sha256"] for r in rows}) != 1:
        raise AssertionError("Scenario executed prefixes differ")
    report = dict(schema_version="catering-paired-foundation.v3",profile_id=instance["profile_id"],rows=rows,
                  all_checks_passed=True,total_s=time.monotonic()-started,physical_qpu_calls=0,veloxq_calls=0,
                  environment=dict(python=platform.python_version(),numpy=np.__version__,ortools=importlib.metadata.version("ortools")),
                  limitations=["Option pools are restrictions, not complete or lossless encodings of the full raw grid",
                               "Known witness is not an optimizer result; cold SA is unrepaired and may be invalid",
                               "Raw reference timeouts do not prove hardness or a global optimality gap",
                               "No quantum method or VeloxQ was executed by this release builder",
                               "Fixed recovery-clean policy; aggregate capacities, money and interrupted cooking disabled"])
    save(output/"report.json",report)
    seal(output)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--customers",type=int,default=6)
    parser.add_argument("--reference-seconds",type=float,default=3)
    args = parser.parse_args()
    build(args.output,customers=args.customers,seconds=args.reference_seconds)
