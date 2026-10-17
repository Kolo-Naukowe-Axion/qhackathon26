"""Restore the three oversized GitHub release assets after downloading them."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--downloads',type=Path,required=True)
    args=parser.parse_args()
    manifest=json.loads((ROOT/'output/stage2-search/REMOTE_ARTIFACTS.json').read_text())
    for asset in manifest['assets']:
        source=args.downloads/asset['asset']
        if source.stat().st_size!=asset['bytes'] or hashlib.file_digest(source.open('rb'),'sha256').hexdigest()!=asset['sha256']:
            raise ValueError(f"Size or digest mismatch: {asset['asset']}")
        target=ROOT/asset['path']
        target.parent.mkdir(parents=True,exist_ok=True)
        if source.resolve()!=target.resolve():
            shutil.copyfile(source,target)
        print(f"Verified {asset['path']}")

if __name__=='__main__':
    main()
