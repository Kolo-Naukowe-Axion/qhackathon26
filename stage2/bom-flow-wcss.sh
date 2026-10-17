#!/bin/bash
#SBATCH --account=hpc-iwowoj-1781179048
#SBATCH --qos=hpc-iwowoj-1781179048
#SBATCH --partition=bem2-cpu-short
#SBATCH --cpus-per-task=32
#SBATCH --mem=48G
#SBATCH --time=00:30:00
#SBATCH --job-name=qh26-stage2-bom-flow
#SBATCH --output=qh26-stage2-bom-flow-%j.log
set -euo pipefail
TASK_ROOT="$HOME/qh26-stage2-20261016"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cd "$TASK_ROOT/snapshots/v14-bom-flow"
"$TASK_ROOT/.venv/bin/python" -m stage2.bom_probe \
 --tasks "$TASK_ROOT/bom-strong-recovery-paired-train32-tasks.json" --workers 32 \
 --output "$TASK_ROOT/results/bom-flow-$SLURM_JOB_ID"
