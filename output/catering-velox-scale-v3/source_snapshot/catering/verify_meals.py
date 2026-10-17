"""Independently recheck retained paired-meal evidence, never submit a job."""
import argparse
import hashlib
import json
from pathlib import Path

from .contracts import load_bundle
from .decode import decode
from .check import check_plan
from .qubo import energy


def verify_manifest(directory):
    directory=Path(directory)
    manifest=json.loads((directory/"manifest.json").read_text())
    for name,expected in manifest["files"].items():
        target=directory/name
        if hashlib.sha256(target.read_bytes()).hexdigest()!=expected:
            raise AssertionError("Artifact hash mismatch: "+str(target))
    for name,expected in manifest.get("sources",{}).items():
        target=directory/"source_snapshot"/name
        if not target.exists():
            # V2 retained hashes identify an historical source revision; never
            # require current sources to remain identical forever.
            continue
        if hashlib.sha256(target.read_bytes()).hexdigest()!=expected:
            raise AssertionError("Source snapshot hash mismatch: "+str(target))
    return len(manifest["files"])


def verify_samples(bundle,payload):
    if payload.get("bundle_sha256",bundle["bundle_sha256"])!=bundle["bundle_sha256"]:
        raise AssertionError("Samples identify a different QUBO")
    count=valid=0
    best=None
    for sample in payload["samples"]:
        if type(sample["count"]) is not int or sample["count"]<1:
            raise AssertionError("Invalid sample frequency")
        value=energy(bundle,sample["bits"])
        if value!=int(sample["reported_energy"]):
            raise AssertionError("Sample literal energy mismatch")
        checked=decode(bundle,sample["bits"])
        count+=sample["count"]
        if checked["valid"]:
            valid+=sample["count"]
            score=tuple(checked["check"]["metrics"][k] for k in ("U","W","B","R"))
            if best is None or score<best:best=score
    if "shots" in payload and count!=payload["shots"]:
        raise AssertionError("Shot count mismatch")
    if "valid_shots" in payload and valid!=payload["valid_shots"]:
        raise AssertionError("Valid-shot count mismatch")
    return dict(returns=len(payload["samples"]),shots=count,valid_shots=valid,best=best)


def verify_release(directory):
    directory=Path(directory);files=verify_manifest(directory)
    bundles=returns=shots=0
    for path in sorted(directory.rglob("*-qubo.json")):
        if "source_snapshot" in path.parts:continue
        bundle=load_bundle(path);bundles+=1
        stem=path.name[:-len("-qubo.json")]
        for suffix in ("-reference.json","-sa.json"):
            target=path.with_name(stem+suffix)
            if target.exists():
                checked=verify_samples(bundle,json.loads(target.read_text()))
                returns+=checked["returns"];shots+=checked["shots"]
    for path in sorted(directory.glob("*/step-*/qubo.json")):
        bundle=load_bundle(path);bundles+=1
        result=verify_samples(bundle,json.loads((path.parent/"samples.json").read_text()))
        returns+=result["returns"];shots+=result["shots"]
        controls=json.loads((path.parent/"controls.json").read_text())
        for payload in controls.values():
            checked=verify_samples(bundle,payload);returns+=checked["returns"];shots+=checked["shots"]
        row=json.loads((path.parent/"summary.json").read_text())
        before=tuple(row["before_metrics"][k] for k in ("U","W","B","R"))
        after=tuple(row["after_metrics"][k] for k in ("U","W","B","R"))
        expected=min(before,result["best"]) if result["best"] is not None else before
        if after!=expected or row["accepted"]!=(after<before):
            raise AssertionError("Controller update differs from actual raw samples")
        warm=json.loads((path.parent/"warm-start.json").read_text())
        ids={p["id"] for p in bundle["options"]}
        if not set(warm["incumbent_program_ids"])<=ids:
            raise AssertionError("Warm-start incumbent missing from offered domain")
    # Complete-cell circuits share the same root QUBO.
    root_bundle=directory/"quantum-qubo.json"
    if root_bundle.exists():
        bundle=load_bundle(root_bundle)
        for path in sorted(directory.glob("p*-seed-*/samples.json")):
            checked=verify_samples(bundle,json.loads(path.read_text()));returns+=checked["returns"];shots+=checked["shots"]
            for payload in json.loads((path.parent/"controls.json").read_text()).values():
                checked=verify_samples(bundle,payload);returns+=checked["returns"];shots+=checked["shots"]
    plans=0
    for path in directory.glob("*/quantum-plan.json"):
        payload=json.loads(path.read_text())
        instance=json.loads((path.parent/"instance.json").read_text())
        state=json.loads((path.parent/"snapshot.json").read_text())
        checked=check_plan(instance,state,payload["plan"])
        if not checked["valid"] or checked["metrics"]!=payload["check"]["metrics"]:
            raise AssertionError("Final physical plan changed")
        plans+=1
    return dict(directory=str(directory),files_hashed=files,bundles=bundles,
                returned_bitstrings_checked=returns,shots_recounted=shots,final_plans_checked=plans,valid=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directories",nargs="+",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise ValueError("Fresh verification output required")
    rows=[]
    for directory in args.directories:
        row=verify_release(directory);rows.append(row);print(json.dumps(row),flush=True)
    args.output.write_text(json.dumps(dict(all_valid=True,rows=rows,physical_qpu_calls=0,veloxq_calls=0),indent=2)+"\n")
