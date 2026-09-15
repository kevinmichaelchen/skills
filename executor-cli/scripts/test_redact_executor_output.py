#!/usr/bin/env python3
"""Minimal regression coverage for Executor CLI output redaction."""

import unittest

from redact_executor_output import redact


class RedactExecutorOutputTests(unittest.TestCase):
    def test_redacts_sensitive_urls_and_tokens(self):
        output = (
            'open https://executor.example/callback?state=private&code=secret\n'
            'Authorization: Bearer abc.def-123\n'
            '{"media_token":"download-secret", "state":"oauth-state", '
            '"attachment":{"url":"https://files.example/get?media_token=attachment-secret"}}\n'
        )

        redacted = redact(output)

        self.assertNotIn("private", redacted)
        self.assertNotIn("secret", redacted)
        self.assertNotIn("abc.def-123", redacted)
        self.assertNotIn("oauth-state", redacted)
        self.assertNotIn("attachment-secret", redacted)
        self.assertIn("[REDACTED_SENSITIVE_URL]", redacted)
        self.assertEqual(redacted.count("[REDACTED_SENSITIVE_URL]"), 2)
        self.assertEqual(redacted.count("[REDACTED]"), 3)

    def test_preserves_non_sensitive_diagnostics(self):
        self.assertEqual(redact("connection refresh failed\n"), "connection refresh failed\n")


if __name__ == "__main__":
    unittest.main()
