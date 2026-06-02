#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="${SANA_OLLAMA_INSTALL_DIR:-$HOME/.local/ollama}"
VERSION_PARAM="${SANA_OLLAMA_VERSION:+?version=$SANA_OLLAMA_VERSION}"

case "$(uname -m)" in
  x86_64)
    ARCH="amd64"
    ;;
  aarch64|arm64)
    ARCH="arm64"
    ;;
  *)
    echo "Unsupported architecture: $(uname -m)" >&2
    exit 1
    ;;
esac

DOWNLOAD_URL="https://ollama.com/download/ollama-linux-${ARCH}.tgz${VERSION_PARAM}"
TMP_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

mkdir -p "$INSTALL_DIR"

echo "Installing Ollama user-local runtime to: $INSTALL_DIR"
echo "Download URL: $DOWNLOAD_URL"
curl --fail --show-error --location "$DOWNLOAD_URL" -o "$TMP_DIR/ollama.tgz"
tar -xzf "$TMP_DIR/ollama.tgz" -C "$INSTALL_DIR"

if [ ! -x "$INSTALL_DIR/bin/ollama" ]; then
  echo "Install failed: $INSTALL_DIR/bin/ollama was not created." >&2
  exit 1
fi

"$INSTALL_DIR/bin/ollama" --version
echo "Add to PATH for this shell:"
echo "export PATH=\"$INSTALL_DIR/bin:\$PATH\""
