#!/usr/bin/env python3
"""Regression tests for Textoria text cleaning."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from textoria_clean_text import clean_cc_text  # noqa: E402


class TextCleaningTest(unittest.TestCase):
    def test_double_quotes_are_normalized_to_corner_quotes(self) -> None:
        cases = {
            '賈政因問:"跟寶玉的是誰?"': "賈政因問：「跟寶玉的是誰？」",
            "賈政因問:“跟寶玉的是誰？”": "賈政因問：「跟寶玉的是誰？」",
        }

        for source, expected in cases.items():
            with self.subTest(source=source):
                cleaned, report = clean_cc_text(source)
                self.assertEqual(cleaned.strip(), expected)
                self.assertIn("convert_curly_double_quotes", report["rules_applied"])


if __name__ == "__main__":
    unittest.main()
