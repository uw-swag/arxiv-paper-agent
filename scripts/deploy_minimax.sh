#!/bin/bash
#SBATCH --job-name=deploy_minimax
#SBATCH --account=<account-name>
#SBATCH --time=20:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=500G  
#SBATCH --gres=gpu:h100:4
#SBATCH --output=logs/%x-%A.out
#SBATCH --error=logs/%x-%A.err

cd <project-directory>
source .venv/bin/activate

TP=$(nvidia-smi --list-gpus | wc -l)

MODEL_PATH="MiniMaxAI/MiniMax-M2.1"
MAX_MODEL_LEN=131072
TOOL_CALL_PARSER="minimax_m2"
REASONING_PARSER="minimax_m2"
PORT=8000
HOST="127.0.0.1"

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
    --reasoning-parser ${REASONING_PARSER} &

VLLM_PID=$!

# Wait for vLLM server to be ready
echo "Waiting for vLLM server to be ready on ${HOST}:${PORT}..."
while ! curl -s "http://${HOST}:${PORT}/health" > /dev/null 2>&1; do
    if ! kill -0 $VLLM_PID 2>/dev/null; then
        echo "vLLM server process died"
        exit 1
    fi
    sleep 5
done
echo "vLLM server is ready!"

# Run main.py
python main.py

# Keep vLLM server running until main.py completes, then cleanup
kill $VLLM_PID 2>/dev/null
wait $VLLM_PID 2>/dev/null