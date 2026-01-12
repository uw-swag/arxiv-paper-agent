#!/bin/bash
#SBATCH --job-name=tool
#SBATCH --account=rrg-pynie
#SBATCH --time=20:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=24
#SBATCH --mem=500G  
#SBATCH --gres=gpu:h100:4
#SBATCH --output=logs/%x-%A.out
#SBATCH --error=logs/%x-%A.err

cd ~/yinx/arxiv-paper-agent
source .venv/bin/activate

TP=$(nvidia-smi --list-gpus | wc -l)

MODEL_PATH="/home/yinx/yinx/scratch/yinx/custom_models/MiniMax-M2.1"
MAX_MODEL_LEN=131072
TOOL_CALL_PARSER="minimax_m2"
REASONING_PARSER="minimax_m2"
PORT=8000
HOST="127.0.0.1"

# vllm serve ${MODEL_PATH} \
# 	--trust-remote-code \
#     --port ${PORT} \
#     --host ${HOST} \
#     --tensor-parallel-size ${TP} \
# 	--kv-cache-dtype fp8_e4m3 \
# 	--quantization fp8 \
#     --gpu-memory-utilization 0.9 \
#     --max-model-len ${MAX_MODEL_LEN} \
#     --enable-auto-tool-choice \
#     --served-model-name "MiniMax-M2.1" \
#     --tool-call-parser ${TOOL_CALL_PARSER} \
#     --reasoning-parser ${REASONING_PARSER}

SAFETENSORS_FAST_GPU=1 vllm serve ${MODEL_PATH} \
	--trust-remote-code \
    --port ${PORT} \
    --host ${HOST} \
    --tensor-parallel-size ${TP} \
    --gpu-memory-utilization 0.9 \
    --max-model-len ${MAX_MODEL_LEN} \
    --enable-auto-tool-choice \
    --served-model-name "MiniMax-M2.1" \
    --tool-call-parser ${TOOL_CALL_PARSER} \
    --reasoning-parser ${REASONING_PARSER}