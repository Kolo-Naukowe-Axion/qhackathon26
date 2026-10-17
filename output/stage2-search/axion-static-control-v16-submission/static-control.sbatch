#!/bin/bash
#SBATCH --account=hpc-iwowoj-1781179048
#SBATCH --qos=hpc-iwowoj-1781179048
#SBATCH --partition=bem2-cpu-short
#SBATCH --cpus-per-task=32
#SBATCH --mem=32G
#SBATCH --time=00:30:00
#SBATCH --array=0-1%2
#SBATCH --job-name=qh26-static-control
#SBATCH --chdir=/home/iwosmu/qh26-stage2-20261016
#SBATCH --output=/home/iwosmu/qh26-stage2-20261016/qh26-static-control-%A-%a.log
set -euo pipefail
TASK_ROOT='/home/iwosmu/qh26-stage2-20261016'
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cd "$TASK_ROOT/snapshots/v16-static-control-grid"
"$TASK_ROOT/.venv/bin/python" - <<'VERIFY'
import hashlib,json
from pathlib import Path
m=json.loads(Path('manifest.json').read_text())
for name,expected in m['files'].items():
    if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=expected:raise RuntimeError('Frozen source mismatch: '+name)
print(json.dumps({'manifest_sha256':hashlib.sha256(Path('manifest.json').read_bytes()).hexdigest(),'core_identity_sha256':m['core_identity_sha256']}),flush=True)
VERIFY
if [ "$SLURM_ARRAY_TASK_ID" = 0 ]; then
  TASKS="$TASK_ROOT/submissions/v16-static-control-grid/static-control-n12-n16-train32-tasks.json"
else
  TASKS="$TASK_ROOT/submissions/v16-static-control-grid/static-control-n24-train32-tasks.json"
fi
"$TASK_ROOT/.venv/bin/python" -m stage2.static_control --tasks "$TASKS" --workers 32 --max-seconds 1740 --output "$TASK_ROOT/results/static-control-v16-$SLURM_ARRAY_JOB_ID-$SLURM_ARRAY_TASK_ID"
