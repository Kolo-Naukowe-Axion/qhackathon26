#!/bin/bash
#SBATCH --account=hpc-iwowoj-1781179048
#SBATCH --qos=hpc-iwowoj-1781179048
#SBATCH --partition=bem2-cpu-short
#SBATCH --cpus-per-task=32
#SBATCH --mem=48G
#SBATCH --time=00:20:00
#SBATCH --job-name=qh26-stage2-completion
#SBATCH --chdir=/home/iwosmu/qh26-stage2-20261016
#SBATCH --output=/home/iwosmu/qh26-stage2-20261016/qh26-stage2-completion-%j.log
set -euo pipefail
TASK_ROOT='/home/iwosmu/qh26-stage2-20261016'
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cd "$TASK_ROOT/snapshots/v15-completion"
"$TASK_ROOT/.venv/bin/python" - <<'VERIFY'
import hashlib,json
from pathlib import Path
manifest=json.loads(Path('manifest.json').read_text())
for name,expected in manifest['files'].items():
    if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=expected:raise RuntimeError('Frozen source drift: '+name)
print(json.dumps({'verified_manifest_sha256':hashlib.sha256(Path('manifest.json').read_bytes()).hexdigest(),'core_identity_sha256':manifest['core_identity_sha256']}),flush=True)
VERIFY
"$TASK_ROOT/.venv/bin/python" -m stage2.completion_policy --tasks "$TASK_ROOT/submissions/v15-completion/completion-value-paired-train32-tasks.json" --output "$TASK_ROOT/results/completion-v15-$SLURM_JOB_ID" --workers 32
