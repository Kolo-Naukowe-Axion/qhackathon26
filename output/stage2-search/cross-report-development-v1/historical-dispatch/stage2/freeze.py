"""Create immutable, self-contained source snapshots for remote comparisons."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tarfile
import time

ROOT=Path(__file__).resolve().parents[1]
CORE=("__init__.py","engine.py","spec.py","check.py","dispatch.py","qubo.py",
      "quantum.py","run.py","tournament.py","learning.py","bounds.py")


def freeze(destination,extra=(),base_snapshot=None):
    destination=Path(destination)
    if destination.exists():raise ValueError("Snapshot already exists; preserve its evidence")
    base=Path(base_snapshot) if base_snapshot else ROOT
    sources={f"stage2/{name}":base/"stage2"/name for name in CORE}
    sources["instances/stage2/metaltech_pressure.json"]=base/"instances/stage2/metaltech_pressure.json"
    sources.update({f"stage2/{name}":ROOT/"stage2"/name for name in extra})
    data={name:p.read_bytes() for name,p in sources.items()}
    if any(p.read_bytes()!=data[name] for name,p in sources.items()):raise RuntimeError("Source changed during capture; retry")
    if base_snapshot:
        previous=json.loads((base/"manifest.json").read_text())
        for name in [f"stage2/{n}" for n in CORE]+["instances/stage2/metaltech_pressure.json"]:
            if hashlib.sha256((base/name).read_bytes()).hexdigest()!=previous["files"][name]:
                raise RuntimeError(f"Base snapshot was altered: {name}")
    hashes={name:hashlib.sha256(content).hexdigest() for name,content in data.items()}
    manifest=dict(schema="stage2-source-snapshot.v1",created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
        files=hashes,core_identity_sha256=hashlib.sha256(json.dumps({k:v for k,v in hashes.items() if k in
        [f"stage2/{n}" for n in CORE[:7]]},sort_keys=True).encode()).hexdigest())
    if base_snapshot:
        manifest["base_snapshot"]=str(base.resolve())
        manifest["base_manifest_sha256"]=hashlib.sha256((base/"manifest.json").read_bytes()).hexdigest()
        manifest["overlay_files"]=[f"stage2/{name}" for name in extra]
    destination.mkdir(parents=True)
    for name,content in data.items():
        target=destination/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(content)
    (destination/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    archive=destination.with_suffix(".tar.gz")
    with tarfile.open(archive,"w:gz") as tf:
        for p in sorted(destination.rglob("*")):
            if p.is_file():tf.add(p,arcname=str(p.relative_to(destination)),recursive=False)
    return dict(path=str(destination),archive=str(archive),**manifest)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("destination",type=Path);p.add_argument("--extra",action="append",default=[])
    p.add_argument("--base-snapshot",type=Path,help="Use a verified frozen physical core and current extra algorithm files")
    a=p.parse_args();print(json.dumps(freeze(a.destination,a.extra,a.base_snapshot),indent=2))
