#!/bin/bash


# module load apptainer
# apptainer pull ngrok.sif docker://ngrok/ngrok:latest

export NGROK_AUTHTOKEN=""

set -euo pipefail
module load apptainer

# Put writable state here (job-local is best if you're in Slurm; fallback to scratch)
STATEDIR="/scratch/yinx/ngrok-varlib"
mkdir -p "$STATEDIR"
chmod 700 "$STATEDIR"

# Require the token to be provided from the environment, but don't print it
: "${NGROK_AUTHTOKEN:?Please export NGROK_AUTHTOKEN before running.}"

# Write the config file the container expects
cat > "$STATEDIR/ngrok.yml" <<EOF
version: "2"
authtoken: ${NGROK_AUTHTOKEN}
EOF
chmod 600 "$STATEDIR/ngrok.yml"

# Run ngrok (container expects /var/lib/ngrok/ngrok.yml)
apptainer run -C -W "/scratch/yinx" \
  -B "$STATEDIR:/var/lib/ngrok" \
  ngrok.sif http 8000
