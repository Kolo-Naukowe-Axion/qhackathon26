"""Run, independently check, and save a fully attributed Stage 2 experiment."""
import argparse
import hashlib
import json
from pathlib import Path
import time

from .engine import run
from .spec import build
from .check import check_trace

ROOT=Path(__file__).resolve().parents[1]


def source_hashes():
    files=sorted((ROOT/"stage2").glob("*.py"))
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def execute(config,weights,output=None):
    started=time.perf_counter();sources=source_hashes();instance=build(**config)
    trace=run(instance,weights);checked=check_trace(trace)
    trace["validation"]=dict(checked,status="passed" if checked["valid"] else "failed")
    trace["provenance"].update(source_sha256=sources,parameters=config,weights=weights,
        instance_sha256=hashlib.sha256(json.dumps(instance,sort_keys=True).encode()).hexdigest())
    trace["provenance"]["wall_seconds"]=time.perf_counter()-started
    if source_hashes()!=sources:raise RuntimeError("Source changed while run was in progress; discard this run")
    if output:
        output=Path(output);output.mkdir(parents=True,exist_ok=True)
        (output/"trace.json").write_text(json.dumps(trace,indent=2)+"\n")
        (output/"check.json").write_text(json.dumps(checked,indent=2)+"\n")
        (output/"summary.json").write_text(json.dumps(dict(metrics=trace["metrics"],validation=checked,
            provenance=trace["provenance"]),indent=2)+"\n")
    return trace


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--orders",type=int,default=24);p.add_argument("--horizon",type=int)
    p.add_argument("--profile",choices=("full","coarse"),default="full")
    p.add_argument("--seed",type=int,default=0);p.add_argument("--wip",type=int,default=3)
    p.add_argument("--mode",choices=("eco","standard","turbo"),default="standard")
    p.add_argument("--selector",choices=("priority","greedy","exact","sa","qaoa","uniform","exact_random_tie"),default="priority")
    p.add_argument("--lease",action="store_true");p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();config=dict(orders=a.orders,horizon=a.horizon,seed=a.seed,profile=a.profile)
    weights=dict(wip_limit=a.wip,mode=a.mode,selector=a.selector,lease_calibration=a.lease)
    t=execute(config,weights,a.output)
    print(json.dumps(dict(metrics=t["metrics"],valid=t["validation"]["valid"],issues=t["validation"]["issues"][:5],
        wall_seconds=t["provenance"]["wall_seconds"],output=str(a.output)),indent=2))


if __name__=="__main__":main()
