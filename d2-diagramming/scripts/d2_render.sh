#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'USAGE'
usage: d2_render.sh [options] input.d2 output.{svg,webp,png,pdf,pptx,gif,txt}

options:
  --layout ENGINE
  --theme ID
  --dark-theme ID
  --sketch
  --animate-interval MS
  --ascii-mode MODE
  --font-regular PATH
  --font-italic PATH
  --font-bold PATH
  --font-semibold PATH
USAGE
}

if ! command -v d2 >/dev/null 2>&1; then
  echo "d2 CLI not found on PATH" >&2
  exit 127
fi

args=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --layout|--theme|--dark-theme|--animate-interval|--ascii-mode|--font-regular|--font-italic|--font-bold|--font-semibold)
      [ "$#" -ge 2 ] || { usage; exit 2; }
      args+=("$1" "$2")
      shift 2
      ;;
    --sketch)
      args+=("$1")
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    -*)
      echo "unknown option: $1" >&2
      usage
      exit 2
      ;;
    *)
      break
      ;;
  esac
done

[ "$#" -eq 2 ] || { usage; exit 2; }
input="$1"
output="$2"
extension="${output##*.}"

render_d2() {
  destination="$1"
  if [ "${#args[@]}" -gt 0 ]; then
    d2 "${args[@]}" "$input" "$destination"
  else
    d2 "$input" "$destination"
  fi
}

case "$extension" in
  svg) echo "rendering SVG; use browser/web-context embedding for Markdown and interactivity" >&2 ;;
  webp) echo "rendering optimized WEBP through a temporary PNG; requires cwebp or ImageMagick" >&2 ;;
  png) echo "rendering PNG; requires Playwright/headless browser dependencies" >&2 ;;
  pdf) echo "rendering PDF; links can work, SVG animation will not" >&2 ;;
  pptx) echo "rendering PPTX; output is view-only, not editable PowerPoint objects" >&2 ;;
  gif) echo "rendering GIF; best for short compositions" >&2 ;;
  txt) echo "rendering ASCII; keep diagrams simple and prefer ELK/TALA" >&2 ;;
  *) echo "unknown output extension: ${output##*.}" >&2 ;;
esac

if [ "$extension" = "webp" ]; then
  temporary_dir="$(mktemp -d)"
  trap 'rm -rf "$temporary_dir"' EXIT
  temporary_png="$temporary_dir/render.png"
  render_d2 "$temporary_png"
  if command -v cwebp >/dev/null 2>&1; then
    cwebp -quiet -q 88 "$temporary_png" -o "$output"
  elif command -v magick >/dev/null 2>&1; then
    magick "$temporary_png" -quality 88 "$output"
  else
    echo "WEBP conversion requires cwebp or ImageMagick; PNG remains only in the temporary directory" >&2
    exit 127
  fi
else
  render_d2 "$output"
fi
