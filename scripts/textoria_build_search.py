#!/usr/bin/env python3
"""Textoria static search-index stage."""

from __future__ import annotations

from pathlib import Path

from textoria_common import BuildPaths, write_json, write_stage_report


def build_search_index(paths: BuildPaths, db_path: Path, reader_paragraphs: list[dict]) -> dict:
    search_index = {"paragraphs": reader_paragraphs}
    write_json(paths.search / "search_index.json", search_index)
    write_json(paths.search / "fts_config.json", {"database": str(db_path), "table": "paragraphs_fts"})
    write_stage_report(
        paths,
        "build_fulltext_search",
        {"ok": True, "search_index": str(paths.search / "search_index.json"), "fts_config": str(paths.search / "fts_config.json")},
    )
    return search_index
