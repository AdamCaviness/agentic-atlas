#!/usr/bin/env bash
# Thin launcher for the agentic-atlas engine in this repo.
#
# The skill lives at skills/run/ inside the engine's own repo, so the engine is
# the repo root two levels up from this script. The launcher resolves it,
# ensures a runnable interpreter with the engine's deps, then forwards every
# argument to the engine unchanged. The /agentic-atlas:run skill calls it as:
#
#   bash atlas.sh questions <target>
#   bash atlas.sh profile  <target> --answers - --format json
#
# All bootstrap chatter is written to stderr, so the engine's stdout (JSON or a
# report) can be piped or captured cleanly. The engine itself is deterministic
# and needs no API key; this script only makes it runnable.

set -euo pipefail

log() { printf '%s\n' "atlas.sh: $*" >&2; }
die() { log "$*"; exit 1; }

# --- Resolve this script's real directory, following symlinks -----------------
# Skills are distributed by symlinking the skill directory (Codex, manual
# installs), so $0 may be a symlink. The engine lives relative to the *real*
# file, not the symlink, so resolve the chain before walking up.
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [ "${SOURCE#/}" = "$SOURCE" ] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"

# --- Locate the engine --------------------------------------------------------
# AGENTIC_ATLAS_ENGINE overrides discovery (useful for testing against a checkout
# elsewhere). Otherwise the engine is the repo root two levels up from this
# script (skills/run/atlas.sh -> repo root), holding both pyproject.toml and the
# agentic_atlas package.
ENGINE="${AGENTIC_ATLAS_ENGINE:-}"
if [ -z "$ENGINE" ]; then
  ENGINE="$(cd "$SCRIPT_DIR/../.." >/dev/null 2>&1 && pwd)"
fi
{ [ -n "$ENGINE" ] && [ -f "$ENGINE/pyproject.toml" ] && [ -f "$ENGINE/agentic_atlas/__init__.py" ]; } \
  || die "could not find the agentic-atlas engine at $ENGINE (expected pyproject.toml and agentic_atlas/__init__.py). Set AGENTIC_ATLAS_ENGINE to the engine repo root."

# The repo root is the engine root. The skill's --save step resolves it here so profile
# artifacts land in the agentic-atlas checkout, not the target project or the current
# directory.
REPO_ROOT="$ENGINE"
if [ "${1:-}" = "--repo-root" ]; then
  printf '%s\n' "$REPO_ROOT"
  exit 0
fi

VENV="$ENGINE/.venv"
ATLAS="$VENV/bin/agentic-atlas"
PY="$VENV/bin/python"

# --- Pick a system interpreter for bootstrapping ------------------------------
# The engine requires Python >= 3.11. Only used to CREATE the venv; once the
# venv exists this is not consulted again.
find_python() {
  for cand in python3.13 python3.12 python3.11 python3 python; do
    if command -v "$cand" >/dev/null 2>&1; then
      if "$cand" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 11) else 1)' 2>/dev/null; then
        command -v "$cand"
        return 0
      fi
    fi
  done
  return 1
}

venv_ok() {
  # A venv is usable only if the console script exists and the interpreter can
  # import the engine and its two runtime deps. This catches a half-built or
  # dependency-missing venv, not just an absent one.
  [ -x "$ATLAS" ] && [ -x "$PY" ] \
    && "$PY" -c 'import agentic_atlas, yaml, jsonschema' >/dev/null 2>&1
}

if ! venv_ok; then
  # Build (or rebuild) the engine venv. Remove a broken one first so the rebuild
  # starts clean. The editable install pulls the two runtime deps and creates the
  # agentic-atlas console script, which is all the skill needs (no dev extras).
  log "bootstrapping engine venv at $VENV (first run)"
  [ -e "$VENV" ] && rm -rf "$VENV"
  sys_py="$(find_python)" || die "need Python >= 3.11 on PATH to build the engine venv"
  "$sys_py" -m venv "$VENV" 1>&2
  "$PY" -m pip install -q --upgrade pip 1>&2
  "$PY" -m pip install -q -e "$ENGINE" 1>&2
  venv_ok || die "engine venv is still not runnable after bootstrap"
fi

exec "$ATLAS" "$@"
