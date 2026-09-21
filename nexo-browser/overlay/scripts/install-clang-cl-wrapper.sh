#!/usr/bin/env bash
# Install a clang-cl wrapper that rewrites Unix source paths for Linux-hosted
# Windows cross compiles. Safe to run repeatedly; does not replace the real
# compiler more than once.
set -euo pipefail

CLANG_BIN="${CLANG_BIN:-${HOME}/.mozbuild/clang/bin}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
WRAPPER="${ROOT}/clang-cl-unix-wrapper.sh"

if [[ ! -x "${CLANG_BIN}/clang-cl" && ! -x "${CLANG_BIN}/clang-cl.real" ]]; then
  echo "clang-cl not found under ${CLANG_BIN}; skip wrapper (bootstrap first)"
  exit 0
fi

if [[ ! -f "${CLANG_BIN}/clang-cl.real" ]]; then
  mv "${CLANG_BIN}/clang-cl" "${CLANG_BIN}/clang-cl.real"
fi

install -m 0755 "${WRAPPER}" "${CLANG_BIN}/clang-cl"
# Keep the wrapper's companion binary next to it (dirname of argv0).
if [[ ! -x "${CLANG_BIN}/clang-cl.real" ]]; then
  echo "missing ${CLANG_BIN}/clang-cl.real" >&2
  exit 1
fi

echo "Installed clang-cl Unix-path wrapper -> ${CLANG_BIN}/clang-cl"
echo "Real compiler: ${CLANG_BIN}/clang-cl.real"
