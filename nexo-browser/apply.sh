#!/usr/bin/env bash
# Clone Camoufox at the pinned tag and apply the NexoBrowser overlay.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLONE="${ROOT}/upstream-camoufox"
OVERLAY="${ROOT}/nexo-browser/overlay"
CAMOUFOX_URL="${CAMOUFOX_URL:-https://github.com/daijro/camoufox.git}"
# User pin: build from this GitHub tag only.
CAMOUFOX_REF="${CAMOUFOX_REF:-v152.0.4-beta.30}"

clone_pinned() {
  echo "==> Cloning Camoufox ${CAMOUFOX_REF} into ${CLONE}"
  git clone --depth 1 --branch "${CAMOUFOX_REF}" "${CAMOUFOX_URL}" "${CLONE}"
}

if [[ ! -d "${CLONE}/.git" ]]; then
  clone_pinned
else
  current="$(git -C "${CLONE}" describe --tags --always 2>/dev/null || true)"
  head="$(git -C "${CLONE}" rev-parse HEAD)"
  echo "==> Existing clone at ${CLONE} (${current} / ${head})"
  if [[ "${current}" != "${CAMOUFOX_REF}" ]]; then
    echo "==> Retargeting clone to ${CAMOUFOX_REF}"
    rm -rf "${CLONE}"
    clone_pinned
  fi
fi

echo "==> Applying NexoBrowser overlay"
rsync -a "${OVERLAY}/" "${CLONE}/"

if [[ -x "${CLONE}/scripts/install-clang-cl-wrapper.sh" ]]; then
  bash "${CLONE}/scripts/install-clang-cl-wrapper.sh" || true
fi

echo "==> Upstream HEAD: $(git -C "${CLONE}" rev-parse HEAD)"
echo "==> Upstream tag:  $(git -C "${CLONE}" describe --tags --always)"
echo "==> Overlay applied."
