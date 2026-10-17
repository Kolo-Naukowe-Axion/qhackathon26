from concurrent.futures import ProcessPoolExecutor
import json,multiprocessing,tempfile
from pathlib import Path
from stage2.schedule_neighborhood_audit import *

def main():
 checkpoint=Path('/home/iwosmu/qh26-stage2-20261016/submissions/v21p1-oracle-audit/strong-cem6-2026.json')
 artifact=load_checkpoint(checkpoint);contexts,tasks=declare(artifact)
 with tempfile.TemporaryDirectory() as tmp,ProcessPoolExecutor(max_workers=1,mp_context=multiprocessing.get_context('spawn')) as pool:
  task=next(t for t in tasks if t['retain_trace']);task.update(checkpoint=str(checkpoint),source_hashes=hashes(),output=tmp)
  row=pool.submit(simulate,task).result()
  print(json.dumps(dict(valid=row['valid'],metrics=row.get('metrics'),identity_audit=row.get('identity_audit'),decode_mismatches=row.get('decode_mismatches'),source_hashes=hashes(),error=row.get('error'))))
  if not row['valid']:raise RuntimeError(row)
if __name__=='__main__':main()
