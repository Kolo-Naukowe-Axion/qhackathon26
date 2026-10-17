"""Restore compressed VeloxQ-track evidence without Node (Python standard library only).

JSON assets: entries of output/COMPRESSED_EVIDENCE.json whose raw path is under
output/catering-methods/veloxq/; each is decompressed and checked against the
recorded size and SHA256. HDF5 assets: every <name>.h5.gz under that directory is
decompressed beside itself. Existing files are never overwritten.

    python3 scripts/restore_veloxq_evidence.py
"""
import gzip
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCOPE = "output/catering-methods/veloxq/"


def main():
    manifest = json.loads((ROOT/"output/COMPRESSED_EVIDENCE.json").read_text())
    restored = 0
    for entry in manifest["files"]:
        if not entry["path"].startswith(SCOPE):
            continue
        target = ROOT/entry["path"]
        if target.exists():
            continue
        data = gzip.decompress((ROOT/entry["gzip_path"]).read_bytes())
        if len(data) != entry["raw_bytes"] or hashlib.sha256(data).hexdigest() != entry["raw_sha256"]:
            raise SystemExit(f"SHA256 mismatch for {entry['path']}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        restored += 1
    for packed in sorted((ROOT/SCOPE).rglob("*.h5.gz")):
        target = packed.with_suffix("")
        if not target.exists():
            with gzip.open(packed, "rb") as source, open(target, "xb") as out:
                shutil.copyfileobj(source, out)
            restored += 1
    print(f"restored {restored} files")


if __name__ == "__main__":
    main()
