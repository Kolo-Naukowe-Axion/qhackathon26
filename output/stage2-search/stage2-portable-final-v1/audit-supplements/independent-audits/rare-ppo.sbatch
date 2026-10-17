#!/bin/bash
#SBATCH --account=hpc-iwowoj-1781179048
#SBATCH --qos=hpc-iwowoj-1781179048
#SBATCH --partition=bem2-cpu-short
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:02:00
#SBATCH --job-name=qh26-audit-rare-ppo
#SBATCH --output=/home/iwosmu/qh26-stage2-20261016/results/postfreeze-rare-ppo-10062/slurm-%j.log
set -euo pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cd /home/iwosmu/qh26-stage2-20261016/snapshots/v20-final-current
/home/iwosmu/qh26-stage2-20261016/.venv/bin/python /home/iwosmu/qh26-stage2-20261016/overlays/postfreeze-rare-ppo-10062/audit_rare_ppo.py execute --folder /home/iwosmu/qh26-stage2-20261016/results/postfreeze-rare-ppo-10062
