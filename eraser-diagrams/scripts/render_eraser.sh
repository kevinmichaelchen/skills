#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: $0 INPUT.json OUTPUT.{png|html|webp} [SCALE]" >&2
  exit 2
}

[[ $# -eq 2 || $# -eq 3 ]] || usage

input=$1
output=$2
scale=${3:-2}

[[ -f "$input" ]] || { echo "input file not found: $input" >&2; exit 2; }
[[ "$scale" =~ ^[1-9][0-9]*([.][0-9]+)?$ ]] || { echo "scale must be positive: $scale" >&2; exit 2; }

if command -v eraser-diagrams >/dev/null 2>&1; then
  cli=(eraser-diagrams)
elif command -v npx >/dev/null 2>&1; then
  cli=(npx --yes @eraserlabs/diagrams-cli@0.1.0)
else
  echo "eraser-diagrams or npx is required" >&2
  exit 2
fi

"${cli[@]}" validate "$input" --fail-on-warning

output_dir=$(dirname "$output")
mkdir -p "$output_dir"

case "$output" in
  *.png)
    "${cli[@]}" render "$input" --out "$output" --format png --scale "$scale" --fail-on-warning
    ;;
  *.html)
    "${cli[@]}" render "$input" --out "$output" --format html --fail-on-warning
    ;;
  *.webp)
    temp_dir=$(mktemp -d "${TMPDIR:-/tmp}/eraser-diagrams.XXXXXX")
    trap 'rm -rf "$temp_dir"' EXIT
    temp_png="$temp_dir/render.png"
    "${cli[@]}" render "$input" --out "$temp_png" --format png --scale "$scale" --fail-on-warning
    if command -v cwebp >/dev/null 2>&1; then
      cwebp -quiet -q 90 "$temp_png" -o "$output"
    elif command -v magick >/dev/null 2>&1; then
      magick "$temp_png" -quality 90 "$output"
    else
      echo "WebP output requires cwebp or ImageMagick" >&2
      exit 2
    fi
    ;;
  *)
    echo "output extension must be .png, .html, or .webp" >&2
    exit 2
    ;;
esac

echo "wrote $output" >&2
