#!/usr/bin/env bash
# clang-cl (CL driver mode) treats arguments that start with '/' as options.
# On Linux that swallows Unix source paths such as /workspace/.../foo.c
# ("clang-cl: error: no input files"). Rewrite those inputs to cwd-relative
# paths so a Windows MSVC cross-compile on Linux can see its sources.
set -euo pipefail

REAL="${NEXO_REAL_CLANG_CL:-$(dirname "$0")/clang-cl.real}"
args=()
for a in "$@"; do
  case "$a" in
    /*.c|/*.cc|/*.cpp|/*.cxx|/*.C|/*.m|/*.mm|/*.s|/*.S|/*.asm|/*.rc)
      if [[ -f "$a" ]]; then
        args+=("$(realpath --relative-to=. -- "$a")")
      else
        args+=("$a")
      fi
      ;;
    *)
      args+=("$a")
      ;;
  esac
done

if [[ -n "${NEXO_CLANGCL_WRAP_LOG:-}" ]]; then
  printf '%s\n' "cwd=$(pwd)" "real=$REAL" "${args[*]}" >>"$NEXO_CLANGCL_WRAP_LOG"
fi

# argv0 must look like clang-cl so the clang driver stays in CL mode
# (clang-cl.real is a symlink to clang).
exec -a clang-cl "$REAL" "${args[@]}"
