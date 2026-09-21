#!/usr/bin/env python3
"""Textoria output validation stage."""

from __future__ import annotations

import sqlite3
import zipfile
from pathlib import Path

from textoria_common import BuildPaths, write_json, write_stage_report


def validate_outputs(paths: BuildPaths, db_path: Path, include_epub: bool = False) -> dict:
    errors = []
    required = [
        paths.clean / "cleaned_text.md",
        paths.intermediate / "structure_preview.md",
        paths.intermediate / "division_review.md",
        paths.csv / "divisions.csv",
        paths.json / "divisions.json",
        db_path,
        paths.site / "index.html",
        paths.site / "read.html",
        paths.site / "search.html",
        paths.site / "assets" / "css" / "style.css",
        paths.site / "assets" / "js" / "reader.js",
        paths.site / "assets" / "js" / "search.js",
        paths.site / "data" / "search_index.json",
    ]
    for path in required:
        if not path.exists():
            errors.append(f"missing required file: {path}")

    counts = {}
    if db_path.exists():
        con = sqlite3.connect(db_path)
        try:
            for table in ("collections", "documents", "divisions", "paragraphs", "sentences", "tokens", "paragraphs_fts"):
                counts[table] = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        except sqlite3.Error as exc:
            errors.append(f"sqlite validation failed: {exc}")
        finally:
            con.close()

    epub_files = list(paths.epub.glob("*.epub"))
    division_count = counts.get("divisions", 0)
    division_pages = list((paths.site / "read").glob("*.html"))
    markdown_pages = list((paths.site / "md").glob("*.md"))
    if division_count and len(division_pages) < division_count:
        errors.append(f"missing division HTML pages: expected {division_count}, found {len(division_pages)}")
    if division_count and len(markdown_pages) < division_count:
        errors.append(f"missing division Markdown pages: expected {division_count}, found {len(markdown_pages)}")

    if include_epub:
        if not epub_files:
            errors.append("missing EPUB output")
        for epub_path in epub_files:
            try:
                with zipfile.ZipFile(epub_path) as zf:
                    names = zf.namelist()
                    if not names or names[0] != "mimetype":
                        errors.append(f"EPUB mimetype must be the first ZIP entry: {epub_path}")
                    for name in ("mimetype", "META-INF/container.xml", "OEBPS/content.opf", "OEBPS/nav.xhtml"):
                        if name not in names:
                            errors.append(f"EPUB missing {name}: {epub_path}")
            except zipfile.BadZipFile:
                errors.append(f"invalid EPUB zip: {epub_path}")

    result = {
        "ok": not errors,
        "counts": counts,
        "required_files_checked": True,
        "sqlite": str(db_path),
        "site": str(paths.site),
        "division_pages": len(division_pages),
        "markdown_pages": len(markdown_pages),
        "epub": [str(path) for path in epub_files],
        "errors": errors,
    }
    write_json(paths.logs / "validation.json", result)
    write_json(paths.logs / "errors.json", errors)
    write_stage_report(paths, "validate_output", result)
    return result
