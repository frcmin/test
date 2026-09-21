#!/usr/bin/env bash
# Clone Camoufox (if needed) and apply the NexoBrowser overlay.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLONE="${ROOT}/upstream-camoufox"
OVERLAY="${ROOT}/nexo-browser/overlay"
CAMOUFOX_URL="${CAMOUFOX_URL:-https://github.com/daijro/camoufox.git}"

if [[ ! -d "${CLONE}/.git" ]]; then
  echo "==> Cloning Camoufox into ${CLONE}"
  git clone --depth 1 "${CAMOUFOX_URL}" "${CLONE}"
else
  echo "==> Using existing clone at ${CLONE}"
fi

echo "==> Applying NexoBrowser overlay"
rsync -a "${OVERLAY}/" "${CLONE}/"

echo "==> Upstream HEAD: $(git -C "${CLONE}" rev-parse HEAD)"
echo "==> Overlay applied."
