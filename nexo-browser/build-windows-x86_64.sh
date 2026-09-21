#!/usr/bin/env bash
# Cross-compile NexoBrowser (Camoufox) for Windows x86_64 from Linux.
# Prefers Docker when the daemon is available; otherwise uses make + multibuild.py.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLONE="${ROOT}/upstream-camoufox"
DIST_HOST="${ROOT}/nexo-browser/dist"
LOG="${ROOT}/nexo-browser/build-windows-x86_64.log"

# Cursor sandbox env vars contain syntax that breaks mozconfig parsing
# (`assert not in_variable`). Drop them before mach/configure.
while IFS= read -r k; do
  case "$k" in
    CURSOR_*|__CURSOR*) unset "$k" || true ;;
  esac
done < <(compgen -e)

mkdir -p "${DIST_HOST}"
exec > >(tee -a "${LOG}") 2>&1

echo "==> $(date -u +%Y-%m-%dT%H:%M:%SZ) starting Windows x86_64 build"
echo "==> Camoufox pin: v152.0.4-beta.30"

bash "${ROOT}/nexo-browser/apply.sh"
cd "${CLONE}"

# Swap helps the libxul link on small VMs, but many cloud pods disallow it.
if ! swapon --show | grep -q .; then
  echo "==> Attempting 32G swap (optional)"
  if sudo fallocate -l 32G /swapfile 2>/dev/null || sudo dd if=/dev/zero of=/swapfile bs=1M count=32768; then
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile || true
    if ! sudo swapon /swapfile; then
      echo "==> Swap not permitted in this environment; continuing without it"
      sudo rm -f /swapfile
    fi
  fi
fi
free -h
df -h /

export BUILD_TARGET=windows,x86_64
export MOZ_MAKE_FLAGS="${MOZ_MAKE_FLAGS:--j2}"
export CARGO_BUILD_JOBS="${CARGO_BUILD_JOBS:-2}"
export MACH_BUILD_PYTHON_NATIVE_PACKAGE_SOURCE="${MACH_BUILD_PYTHON_NATIVE_PACKAGE_SOURCE:-system}"
export DISPLAY="${DISPLAY:-:1}"
export WINEDEBUG="-all"
export RUSTUP_HOME="${RUSTUP_HOME:-/usr/local/rustup}"
export CARGO_HOME="${CARGO_HOME:-/usr/local/cargo}"
export WINEPREFIX="${WINEPREFIX:-${HOME}/.mozbuild/wineprefix}"
# rustup env if present
# shellcheck disable=SC1091
[[ -f "${HOME}/.cargo/env" ]] && . "${HOME}/.cargo/env"
[[ -f /usr/local/cargo/env ]] && . /usr/local/cargo/env
export PATH="${HOME}/.cargo/bin:/usr/local/cargo/bin:${HOME}/.mozbuild/wine/bin:${PATH}"
if command -v rustup >/dev/null 2>&1; then
  rustup default stable || true
  rustup target add x86_64-pc-windows-msvc || true
fi

if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  echo "==> Docker available: using camoufox-builder"
  docker build -t camoufox-builder .
  mkdir -p "${CLONE}/dist"
  docker run --rm \
    -e BUILD_TARGET=windows,x86_64 \
    -v "${CLONE}/dist:/app/dist" \
    camoufox-builder --target windows --arch x86_64
else
  echo "==> Docker not available; native cross-compile"
  bash scripts/install-deps.sh
  rustup target add x86_64-pc-windows-msvc || true
  make bootstrap
  bash scripts/install-clang-cl-wrapper.sh
  python3 multibuild.py --target windows --arch x86_64
fi

echo "==> Build finished $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "==> Dist contents:"
ls -lh dist "${CLONE}"/*.zip 2>/dev/null || true
mkdir -p "${DIST_HOST}"
shopt -s nullglob
for zip in dist/NexoBrowser-*-win.x86_64.zip NexoBrowser-*-win.x86_64.zip; do
  cp -v "${zip}" "${DIST_HOST}/"
done
ls -lh "${DIST_HOST}"
