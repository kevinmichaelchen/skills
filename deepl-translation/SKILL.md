---
name: deepl-translation
description: Translate, localize, review, or improve text with the DeepL API while preserving facts, terminology, formatting, and locale variants. Use when Codex needs DeepL-powered text translation, comparison against an existing translation, quota inspection, formal or informal language control, contextual translation, custom instructions, glossaries, or reproducible translation from files or standard input.
---

# DeepL Translation

Use DeepL as a translation candidate generator, not as an authority on facts. Preserve the source meaning and review every result before replacing user-facing content.

## Workflow

1. Identify the target locale, audience, tone, and content format. Prefer an explicit regional target such as `EN-GB`, `PT-PT`, or `PT-BR` when it matters.
2. Locate `DEEPL_API_KEY` in the environment or a local `.env`. Never print, commit, interpolate into a URL, or expose the key to client-side code.
3. Check quota before a large job:

   ```sh
   python3 scripts/deepl.py usage --env-file .env
   ```

4. Translate a representative sample before spending quota on the full corpus. Compare it with the current human or machine translation for meaning, idiom, brevity, terminology, factual fidelity, and formatting.
5. Translate the full content only when the sample is useful. Provide `--source` when known, related prose as `--context`, and `--protect` for names, locations, dates, metrics, product names, code identifiers, and other literals that must survive unchanged.
6. Review the output. Reject hallucinated facts, changed degrees or titles, shifted narrative person, inconsistent terminology, and locale drift. DeepL may improve prose without being safe to accept wholesale.
7. Run the project's normal rendering, linting, or document checks after integrating a translation.

## CLI

The bundled `scripts/deepl.py` uses only the Python standard library. It selects the Free endpoint for keys ending in `:fx`, otherwise the Pro endpoint. Use `DEEPL_API_URL` or `--api-url` only to select another documented DeepL regional endpoint; the script rejects non-DeepL hosts to prevent credential disclosure.

Translate a string:

```sh
python3 scripts/deepl.py translate \
  --source EN --target DE \
  --formality prefer_more \
  --model prefer_quality_optimized \
  --text "Built a resilient deployment platform."
```

Translate a file or standard input:

```sh
python3 scripts/deepl.py translate --source EN --target PT-PT \
  --file content.txt --output translated.txt

printf '%s\n' "Hello" | python3 scripts/deepl.py translate --target FR
```

Supply genuine surrounding prose with `--context` or `--context-file`; context is not an instruction channel. Use repeatable `--instruction` options for supported target languages and `--glossary-id` for established terminology.

Protect immutable literals:

```sh
python3 scripts/deepl.py translate --source EN --target ES \
  --protect "Bethesda, MD" \
  --protect "95%" \
  --text "Reduced latency by 95% while working in Bethesda, MD."
```

Use `--json` when downstream code needs detected languages, billed characters, or model metadata. Use `--dry-run` to inspect the request summary without contacting DeepL. Protection placeholders can increase the submitted character count, so the dry run reports original characters and estimated protection overhead separately.

## Quality Guardrails

- Treat names, employers, locations, dates, credentials, links, numbers, units, and technical identifiers as protected data.
- Do not ask `context` to enforce tone or rules. DeepL documents it as surrounding content for ambiguity; use formality, glossaries, style rules, or custom instructions instead.
- Keep related sentences together or provide shared context. Items in a multi-text request are translated independently.
- Prefer `prefer_quality_optimized` when quality matters and fallback is acceptable.
- Prefer `prefer_more` or `prefer_less` over strict formality modes when translating across targets with uneven feature support.
- Cache accepted results for repeatable workloads; retranslating unchanged source text consumes quota again.
- Never claim native-speaker quality from API output alone. For consequential publication, obtain fluent review when possible.

## API References

- Authentication and endpoints: https://developers.deepl.com/docs/getting-started/auth
- Text translation parameters: https://developers.deepl.com/api-reference/translate/request-translation
- Context guidance: https://developers.deepl.com/docs/learning-how-tos/examples-and-guides/how-to-use-context-parameter
- Usage and limits: https://developers.deepl.com/api-reference/usage-and-quota/check-usage-and-limits
