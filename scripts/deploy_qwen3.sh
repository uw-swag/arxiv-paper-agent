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

python -m vllm.entrypoints.openai.api_server \
	--model /home/yinx/yinx/scratch/yinx/custom_models/Qwen3-235B-A22B-Instruct-2507-FP8 \
	--port 8000 \
	--host 127.0.0.1 \
	--tensor-parallel-size ${TP} \
	--gpu-memory-utilization 0.95 \
	--max-model-len 65536 \
	--enable-auto-tool-choice \
	--tool-call-parser qwen3_xml