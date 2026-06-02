#!/usr/bin/env bash
set -euo pipefail

MODEL="${1:-${SANA_LLM_MODEL:-llama3.1:8b}}"
INSTALL_DIR="${SANA_OLLAMA_INSTALL_DIR:-$HOME/.local/ollama}"
OLLAMA_BIN="${SANA_OLLAMA_BIN:-$INSTALL_DIR/bin/ollama}"

if [ ! -x "$OLLAMA_BIN" ]; then
  echo "Ollama binary not found: $OLLAMA_BIN" >&2
  echo "Run ./scripts/ollama_user_install.sh first." >&2
  exit 1
fi

export OLLAMA_HOST="${OLLAMA_HOST:-127.0.0.1:11434}"
export OLLAMA_MODELS="${OLLAMA_MODELS:-$HOME/.ollama/models}"
export PATH="$INSTALL_DIR/bin:$PATH"

echo "Pulling Ollama model: $MODEL"
echo "OLLAMA_HOST=$OLLAMA_HOST"
echo "OLLAMA_MODELS=$OLLAMA_MODELS"
"$OLLAMA_BIN" pull "$MODEL"
