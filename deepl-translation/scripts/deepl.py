#!/usr/bin/env python3
"""Small, dependency-free DeepL text translation CLI."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


FREE_API_URL = "https://api-free.deepl.com"
PRO_API_URL = "https://api.deepl.com"
RETRYABLE_STATUS = {429, 500, 502, 503, 504}
ALLOWED_API_HOSTS = {
    "api.deepl.com",
    "api-free.deepl.com",
    "api-jp.deepl.com",
    "api-us.deepl.com",
}


class DeepLError(RuntimeError):
    pass


def parse_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value[:1] == value[-1:] and value[:1] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def credentials(args: argparse.Namespace) -> tuple[str, str]:
    dotenv = parse_dotenv(Path(args.env_file)) if args.env_file else {}
    key = os.environ.get("DEEPL_API_KEY") or dotenv.get("DEEPL_API_KEY")
    if not key:
        raise DeepLError(
            "DEEPL_API_KEY is missing; set it in the environment or pass --env-file."
        )
    configured_url = (
        args.api_url
        or os.environ.get("DEEPL_API_URL")
        or dotenv.get("DEEPL_API_URL")
    )
    api_url = configured_url or (FREE_API_URL if key.endswith(":fx") else PRO_API_URL)
    parsed_url = urllib.parse.urlparse(api_url)
    if (
        parsed_url.scheme != "https"
        or parsed_url.hostname not in ALLOWED_API_HOSTS
        or parsed_url.username
        or parsed_url.password
        or parsed_url.path not in {"", "/"}
        or parsed_url.query
        or parsed_url.fragment
    ):
        raise DeepLError(
            "The API URL must be an HTTPS base URL on a documented DeepL host."
        )
    return key, api_url.rstrip("/")


def request_json(
    method: str,
    url: str,
    key: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "Authorization": f"DeepL-Auth-Key {key}",
            "Content-Type": "application/json",
            "User-Agent": "deepl-translation-skill/1.0",
        },
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            if error.code in RETRYABLE_STATUS and attempt < 3:
                time.sleep(2**attempt)
                continue
            try:
                message = json.loads(detail).get("message", detail)
            except json.JSONDecodeError:
                message = detail
            raise DeepLError(f"DeepL returned HTTP {error.code}: {message}") from None
        except urllib.error.URLError as error:
            if attempt < 3:
                time.sleep(2**attempt)
                continue
            raise DeepLError(f"Could not reach DeepL: {error.reason}") from None
    raise DeepLError("DeepL request failed after retries.")


def read_texts(args: argparse.Namespace) -> list[str]:
    sources = sum(bool(value) for value in (args.text, args.file))
    if sources > 1:
        raise DeepLError("Use either --text or --file, not both.")
    if args.text:
        return args.text
    if args.file:
        return [Path(args.file).read_text(encoding="utf-8")]
    if sys.stdin.isatty():
        raise DeepLError("Provide --text, --file, or text on standard input.")
    return [sys.stdin.read()]


def read_optional_text(value: str | None, file_path: str | None) -> str | None:
    if value and file_path:
        raise DeepLError("Use either inline context or a context file, not both.")
    if file_path:
        return Path(file_path).read_text(encoding="utf-8")
    return value


def protect_texts(
    texts: list[str], protected: list[str]
) -> tuple[list[str], dict[str, str], list[set[str]]]:
    literals = sorted(
        {literal for literal in protected if literal},
        key=lambda literal: (-len(literal), literal),
    )
    literal_to_token = {
        literal: f"__DEEPL_KEEP_{index:04d}__"
        for index, literal in enumerate(literals)
    }
    token_to_literal = {token: literal for literal, token in literal_to_token.items()}
    if not literals:
        return list(texts), token_to_literal, [set() for _ in texts]

    pattern = re.compile("|".join(re.escape(literal) for literal in literals))
    result: list[str] = []
    expected_tokens: list[set[str]] = []
    for text in texts:
        replaced = pattern.sub(lambda match: literal_to_token[match.group(0)], text)
        result.append(replaced)
        expected_tokens.append(
            {token for token in token_to_literal if token in replaced}
        )
    return result, token_to_literal, expected_tokens


def restore_text(
    text: str, mapping: dict[str, str], expected_tokens: set[str]
) -> str:
    restored = text
    for token in expected_tokens:
        if token not in restored:
            raise DeepLError(f"DeepL changed protected placeholder {token}.")
        restored = restored.replace(token, mapping[token])
    return restored


def output_result(args: argparse.Namespace, response: dict[str, Any]) -> None:
    if args.json:
        rendered = json.dumps(response, ensure_ascii=False, indent=2) + "\n"
    else:
        rendered = "\n".join(item["text"] for item in response["translations"]) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)


def usage(args: argparse.Namespace) -> None:
    key, api_url = credentials(args)
    response = request_json("GET", f"{api_url}/v2/usage", key)
    count = response.get("character_count")
    limit = response.get("character_limit")
    if args.json or count is None or limit is None:
        print(json.dumps(response, ensure_ascii=False, indent=2))
        return
    remaining = max(0, limit - count)
    percent = (count / limit * 100) if limit else 0
    print(f"{count:,} / {limit:,} characters used ({percent:.1f}%); {remaining:,} remaining")


def translate(args: argparse.Namespace) -> None:
    texts = read_texts(args)
    protected_texts, mapping, expected_tokens = protect_texts(texts, args.protect)
    context = read_optional_text(args.context, args.context_file)
    if not all(text for text in texts):
        raise DeepLError("Translation input must not be empty.")
    if len(args.instruction) > 10:
        raise DeepLError("DeepL accepts at most ten custom instructions per request.")
    if any(len(instruction) > 300 for instruction in args.instruction):
        raise DeepLError("Each custom instruction must be at most 300 characters.")
    source_characters = sum(len(text) for text in texts)
    estimated_characters = sum(len(text) for text in protected_texts)
    used_protected_tokens = {
        token for tokens in expected_tokens for token in tokens
    }

    payload: dict[str, Any] = {
        "text": protected_texts,
        "target_lang": args.target.upper(),
        "show_billed_characters": True,
        "preserve_formatting": args.preserve_formatting,
    }
    optional = {
        "source_lang": args.source.upper() if args.source else None,
        "context": context,
        "formality": args.formality,
        "model_type": args.model,
        "glossary_id": args.glossary_id,
        "style_id": args.style_id,
        "custom_instructions": args.instruction or None,
    }
    payload.update({key: value for key, value in optional.items() if value is not None})

    if args.dry_run:
        print(
            json.dumps(
                {
                    "target_lang": payload["target_lang"],
                    "source_lang": payload.get("source_lang"),
                    "text_segments": len(texts),
                    "source_characters": source_characters,
                    "estimated_billed_characters": estimated_characters,
                    "protection_character_overhead": (
                        estimated_characters - source_characters
                    ),
                    "protected_literals": len(used_protected_tokens),
                    "has_context": bool(context),
                    "custom_instruction_count": len(args.instruction),
                },
                indent=2,
            )
        )
        return

    key, api_url = credentials(args)
    response = request_json("POST", f"{api_url}/v2/translate", key, payload)
    translations = response.get("translations")
    if not isinstance(translations, list) or len(translations) != len(texts):
        raise DeepLError("DeepL returned an unexpected translation count.")
    for item, tokens in zip(translations, expected_tokens, strict=True):
        item["text"] = restore_text(item["text"], mapping, tokens)
    output_result(args, response)


def add_common_auth(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--env-file", help="Read DEEPL_API_KEY and DEEPL_API_URL here")
    parser.add_argument("--api-url", help="Override the DeepL API base URL")
    parser.add_argument("--json", action="store_true", help="Print structured JSON")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    usage_parser = commands.add_parser("usage", help="Show account character usage")
    add_common_auth(usage_parser)
    usage_parser.set_defaults(run=usage)

    translate_parser = commands.add_parser("translate", help="Translate text")
    add_common_auth(translate_parser)
    translate_parser.add_argument("--target", required=True, help="Target language code")
    translate_parser.add_argument("--source", help="Known source language code")
    translate_parser.add_argument(
        "--text", action="append", help="Text segment; repeat for multiple segments"
    )
    translate_parser.add_argument("--file", help="UTF-8 input file")
    translate_parser.add_argument("--output", help="Write output to this file")
    translate_parser.add_argument("--context", help="Surrounding prose for ambiguity")
    translate_parser.add_argument("--context-file", help="UTF-8 context file")
    translate_parser.add_argument(
        "--formality",
        choices=["default", "more", "less", "prefer_more", "prefer_less"],
    )
    translate_parser.add_argument(
        "--model",
        choices=[
            "quality_optimized",
            "prefer_quality_optimized",
            "latency_optimized",
        ],
    )
    translate_parser.add_argument(
        "--instruction",
        action="append",
        default=[],
        help="Custom instruction; repeat up to ten times",
    )
    translate_parser.add_argument("--glossary-id")
    translate_parser.add_argument("--style-id")
    translate_parser.add_argument(
        "--protect",
        action="append",
        default=[],
        help="Literal that must remain unchanged; repeat as needed",
    )
    translate_parser.add_argument("--preserve-formatting", action="store_true")
    translate_parser.add_argument("--dry-run", action="store_true")
    translate_parser.set_defaults(run=translate)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.run(args)
    except (DeepLError, OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
