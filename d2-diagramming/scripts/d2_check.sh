#!/usr/bin/env bash
set -euo pipefail

if ! command -v d2 >/dev/null 2>&1; then
  echo "d2 CLI not found on PATH" >&2
  exit 127
fi

if [ "$#" -eq 0 ]; then
  echo "usage: $0 <file.d2>..." >&2
  exit 2
fi

echo "d2: $(d2 --version 2>&1 | head -n 1)"
echo "available layouts:"
d2 layout 2>/dev/null || true

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

for file in "$@"; do
  if [ ! -f "$file" ]; then
    echo "missing file: $file" >&2
    exit 1
  fi

  echo "formatting $file"
  d2 fmt "$file"

  out="$tmpdir/$(basename "${file%.d2}").svg"
  echo "compiling $file -> $out"
  d2 "$file" "$out"
done

echo "ok"
