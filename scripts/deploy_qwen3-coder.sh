#!/bin/bash
#SBATCH --job-name=tool
#SBATCH --account=rrg-pynie
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=500G  
#SBATCH --gres=gpu:h100:2
#SBATCH --output=logs/%x-%A.out
#SBATCH --error=logs/%x-%A.err

cd ~/yinx/arxiv-paper-agent
source .venv/bin/activate

TP=$(nvidia-smi --list-gpus | wc -l)

MODEL_PATH="/home/yinx/yinx/scratch/yinx/custom_models/Qwen3-Coder-30B-A3B-Instruct"
PORT=8000
HOST="127.0.0.1"

python -m vllm.entrypoints.openai.api_server \
	--model ${MODEL_PATH} \
	--port ${PORT} \
	--host ${HOST} \
	--tensor-parallel-size ${TP} \
	--gpu-memory-utilization 0.95 \
	--max-model-len 131072 \
	--enable-auto-tool-choice \
	--tool-call-parser qwen3_xml