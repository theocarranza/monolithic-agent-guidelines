#!/usr/bin/env bash
# User-scoped installer. Native hook trust and persistent guidance are separate.
set -euo pipefail
VERSION="v1.4.0"
REPOSITORY="https://github.com/theocarranza/monolithic-agent-guidelines.git"
PYTHON_BIN="${PYTHON:-python3}"
command -v "$PYTHON_BIN" >/dev/null || { echo 'Python 3.9+ is required.' >&2; exit 1; }
"$PYTHON_BIN" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,9) else "Python 3.9+ is required")'
SCRIPT_DIRECTORY="$(cd -- "$(dirname -- "${BASH_SOURCE[0]:-/dev/stdin}")" && pwd)"
if [[ -f "$SCRIPT_DIRECTORY/scripts/install_hosts.py" ]]; then
  exec "$PYTHON_BIN" "$SCRIPT_DIRECTORY/scripts/install_hosts.py" "$@"
fi
command -v git >/dev/null || { echo 'Git is required for the pinned bootstrap checkout.' >&2; exit 1; }
CHECKOUT="${XDG_DATA_HOME:-$HOME/.local/share}/monolithic-agent-guidelines/bootstrap/$VERSION"
if [[ -L "$CHECKOUT" ]]; then
  echo 'Refusing a symlink bootstrap checkout.' >&2; exit 1
fi
if [[ ! -e "$CHECKOUT" ]]; then
  mkdir -p -- "$(dirname -- "$CHECKOUT")"
  git clone --depth 1 --branch "$VERSION" -- "$REPOSITORY" "$CHECKOUT"
else
  [[ "$(git -C "$CHECKOUT" config --get remote.origin.url)" == "$REPOSITORY" ]] || { echo 'Bootstrap checkout has another origin.' >&2; exit 1; }
  [[ "$(git -C "$CHECKOUT" describe --tags --exact-match HEAD)" == "$VERSION" ]] || { echo 'Bootstrap checkout has another version.' >&2; exit 1; }
  [[ -z "$(git -C "$CHECKOUT" status --porcelain)" ]] || { echo 'Bootstrap checkout has local changes; preserve/reconcile them manually.' >&2; exit 1; }
fi
exec "$PYTHON_BIN" "$CHECKOUT/scripts/install_hosts.py" "$@"
