#!/usr/bin/env bash
set -euo pipefail

intent="${1:-general}"
base="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

common=(
  "$base/references/diagram-design.md"
  "$base/references/syntax-core.md"
)

case "$intent" in
  general|basic|architecture)
    extra=("$base/references/layout-engines.md" "$base/references/styling-themes.md")
    ;;
  c4|model|models|views|model-view)
    extra=("$base/references/modularity-imports.md" "$base/references/c4-model.md" "$base/references/layout-engines.md")
    ;;
  import|imports|modular|refactor|template)
    extra=("$base/references/modularity-imports.md")
    ;;
  composition|animation|animated|layers|scenarios|steps|pptx|presentation)
    extra=("$base/references/composition-animation.md" "$base/references/exports-embedding.md")
    ;;
  sequence|erd|sql|uml|grid|table|markdown|text)
    extra=("$base/references/diagram-types.md" "$base/references/layout-engines.md")
    ;;
  style|theme|themes|icons|fonts|sketch|dark)
    extra=("$base/references/styling-themes.md")
    ;;
  export|exports|svg|png|pdf|gif|ascii|embedding|embed)
    extra=("$base/references/exports-embedding.md" "$base/references/troubleshooting.md")
    ;;
  cli|tooling|oracle|api|editor)
    extra=("$base/references/cli-tooling.md")
    ;;
  troubleshoot|debug|fix|render)
    extra=("$base/references/troubleshooting.md" "$base/references/layout-engines.md" "$base/references/exports-embedding.md")
    ;;
  sources|map|docs)
    extra=("$base/references/source-doc-map.md")
    ;;
  *)
    extra=("$base/references/layout-engines.md" "$base/references/troubleshooting.md")
    ;;
esac

printf '%s\n' "${common[@]}" "${extra[@]}"
