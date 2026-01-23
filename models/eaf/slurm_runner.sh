#!/usr/bin/bash
#SBATCH --job-name=eaf_sim
#SBATCH -a 942-10000
# #SBATCH --gres=gpu:2
#SBATCH -c 1
#SBATCH --mem=2G
#SBATCH --output=logs/eaf_%A_%a.out
#SBATCH --error=logs/eaf_%A_%a.err
# #SBATCH --partition=ivc

source ~/.zshrc

source ../../.venv/bin/activate
SIM_ID=$SLURM_ARRAY_TASK_ID
SIM_MAX=$SLURM_ARRAY_TASK_MAX
echo "Starting simulation $SIM_ID of $SIM_MAX"
python -u run_simulation.py  --samples $SIM_MAX --sample $SIM_ID





#[2026-01-22T16:46:02.003] Node configuration differs from hardware: CPUs=20:24(hw) Boards=1:1(hw) SocketsPerBoard=20:1(hw) CoresPerSocket=1:12(hw) ThreadsPerCore=1:2(hw)