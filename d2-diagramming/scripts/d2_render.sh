#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'USAGE'
usage: d2_render.sh [options] input.d2 output.{svg,png,pdf,pptx,gif,txt}

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

case "${output##*.}" in
  svg) echo "rendering SVG; use browser/web-context embedding for Markdown and interactivity" >&2 ;;
  png) echo "rendering PNG; requires Playwright/headless browser dependencies" >&2 ;;
  pdf) echo "rendering PDF; links can work, SVG animation will not" >&2 ;;
  pptx) echo "rendering PPTX; output is view-only, not editable PowerPoint objects" >&2 ;;
  gif) echo "rendering GIF; best for short compositions" >&2 ;;
  txt) echo "rendering ASCII; keep diagrams simple and prefer ELK/TALA" >&2 ;;
  *) echo "unknown output extension: ${output##*.}" >&2 ;;
esac

d2 "${args[@]}" "$input" "$output"
