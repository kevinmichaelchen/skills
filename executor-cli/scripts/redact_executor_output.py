#!/usr/bin/env python3
"""Redact credential-bearing Executor CLI output before it reaches a transcript."""

from __future__ import annotations

import re
import sys


SENSITIVE_JSON_FIELD = re.compile(
    r'(?i)(["\']?(?:access[_-]?token|refresh[_-]?token|id[_-]?token|'
    r'bearer[_-]?token|media[_-]?token|oauth[_-]?state|state)["\']?\s*[:=]\s*)'
    r'(["\']?)[^\s,}\]"\']+\2'
)
BEARER = re.compile(r'(?i)(\bbearer\s+)[A-Za-z0-9._~+/%=-]+')
SENSITIVE_QUERY_URL = re.compile(
    r'(?i)https?://[^\s"\']+[?&](?:[^\s"\']*(?:access[_-]?token|refresh[_-]?token|'
    r'id[_-]?token|token|code|state)=)[^\s"\']*'
)


def redact(text: str) -> str:
    """Replace whole sensitive URLs and individual credential values."""
    text = SENSITIVE_QUERY_URL.sub("[REDACTED_SENSITIVE_URL]", text)
    text = BEARER.sub(r"\1[REDACTED]", text)
    return SENSITIVE_JSON_FIELD.sub(r"\1[REDACTED]", text)


if __name__ == "__main__":
    sys.stdout.write(redact(sys.stdin.read()))
