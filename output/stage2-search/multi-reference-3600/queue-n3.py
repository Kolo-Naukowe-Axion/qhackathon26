"""Wait for the n3 full-600 capture, then use its freed single CPU slot."""
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
capture=ROOT/'output/stage2-search/multi-reference-600/n3/summary.json'
while True:
    if capture.exists():
        try:rows=json.loads(capture.read_text())
        except json.JSONDecodeError:
            time.sleep(1);continue
        if any(row['attendance']=='full'for row in rows):break
    time.sleep(10)
command=[sys.executable,str(ROOT/'output/stage2-search/multi-reference-600/run.py'),
    '--pumps','3','--attendance','automatic','--wall-limit','3600','--deterministic-limit','3600',
    '--incumbent-trace',str(ROOT/'output/stage2-search/multi-reference-600/n3/automatic/cp-trace.json'),
    '--output',str(ROOT/'output/stage2-search/multi-reference-3600/n3')]
print('n3 full-600 capture retained; starting one-worker automatic fresh search.',flush=True)
raise SystemExit(subprocess.call(command,cwd=ROOT))
