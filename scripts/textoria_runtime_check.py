#!/usr/bin/env python3
"""Check Textoria's local Python runtime dependencies."""

from __future__ import annotations

import importlib.util
import json
import sqlite3
import sys


REQUIRED_PACKAGES = ["charset_normalizer", "bs4", "jinja2", "markdown_it", "pypinyin"]


def check_runtime() -> dict:
    missing = [name for name in REQUIRED_PACKAGES if importlib.util.find_spec(name) is None]
    fts5 = True
    try:
        con = sqlite3.connect(":memory:")
        con.execute("CREATE VIRTUAL TABLE test_fts USING fts5(text)")
        con.close()
    except sqlite3.Error:
        fts5 = False
    return {
        "python": sys.version.split()[0],
        "python_ok": sys.version_info >= (3, 10),
        "sqlite_fts5": fts5,
        "required_packages": REQUIRED_PACKAGES,
        "missing_packages": missing,
        "ready": sys.version_info >= (3, 10) and fts5 and not missing,
    }


def main() -> int:
    result = check_runtime()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
