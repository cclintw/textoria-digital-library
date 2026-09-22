#!/usr/bin/env python3
"""Common Textoria v1 helpers and file contracts."""

from __future__ import annotations

import csv
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


TEXTORIA_VERSION = "0.1.0"
SUPPORTED_EXTENSIONS = {".txt", ".md", ".html", ".htm", ".csv"}

try:
    from pypinyin import Style, lazy_pinyin
except ImportError:  # pragma: no cover - runtime_check reports this before workflow use.
    Style = None
    lazy_pinyin = None


@dataclass
class BuildPaths:
    root: Path
    raw_original: Path
    prepared: Path
    intermediate: Path
    clean: Path
    csv: Path
    json: Path
    sqlite: Path
    search: Path
    epub: Path
    site: Path
    site_data: Path
    logs: Path
    stages: Path
    config: Path


CSV_FIELDS = {
    "collections": ["collection_id", "name", "slug", "title", "subtitle", "description", "collection_type", "language", "created_at", "updated_at", "metadata_json"],
    "documents": ["document_id", "collection_id", "title", "document_type", "creator", "date", "publisher", "source", "identifier", "language", "rights", "source_file", "source_format", "source_encoding", "sort_key", "char_start", "char_end", "metadata_json"],
    "divisions": ["division_id", "collection_id", "document_id", "parent_division_id", "level", "division_type", "title", "label", "n", "sort_order", "path", "char_start", "char_end", "metadata_json"],
    "paragraphs": ["paragraph_id", "collection_id", "document_id", "division_id", "paragraph_index", "text", "char_start", "char_end", "source_file", "metadata_json"],
    "sentences": ["sentence_id", "collection_id", "document_id", "division_id", "paragraph_id", "sentence_index", "text", "char_start", "char_end", "metadata_json"],
    "tokens": ["token_id", "collection_id", "document_id", "division_id", "paragraph_id", "sentence_id", "token_index", "text", "normalized_text", "char_start", "char_end", "token_type", "metadata_json"],
    "source_files": ["source_file_id", "collection_id", "document_id", "original_path", "prepared_path", "extracted_text_path", "file_format", "detected_encoding", "byte_size", "line_count", "sha256", "sort_order", "metadata_json"],
    "metadata": ["metadata_id", "subject_table", "subject_id", "key", "value", "scheme", "language", "source"],
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_dirs(output: Path) -> BuildPaths:
    paths = BuildPaths(
        root=output,
        raw_original=output / "raw" / "original",
        prepared=output / "prepared",
        intermediate=output / "intermediate",
        clean=output / "clean",
        csv=output / "csv",
        json=output / "json",
        sqlite=output / "sqlite",
        search=output / "search",
        epub=output / "epub",
        site=output / "site",
        site_data=output / "site" / "data",
        logs=output / "logs",
        stages=output / "logs" / "stages",
        config=output / "config",
    )
    for path in paths.__dict__.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def default_collection_name(source: Path) -> str:
    return source.stem


def default_collection_slug(source: Path, name: str | None = None) -> str:
    return slugify(name or default_collection_name(source), fallback=slugify(source.stem, fallback="collection"))


def default_collection_output(project_root: Path, source: Path, name: str | None = None, slug: str | None = None) -> Path:
    collection_slug = slug or default_collection_slug(source, name)
    return project_root / "textoria" / "collections" / collection_slug


def project_textoria_root(collection_root: Path) -> Path:
    if collection_root.parent.name == "collections":
        return collection_root.parent.parent
    return collection_root


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def make_toc(divisions: list[dict]) -> list[dict]:
    return [
        {
            "id": div["division_id"],
            "type": div["division_type"],
            "title": div["title"],
            "parent_id": div["parent_division_id"],
            "level": div["level"],
            "order": div["sort_order"],
            "path": div["path"],
            "href": f"read/{div.get('page_division_id') or div['division_id']}.html"
            + ("" if (div.get("page_division_id") or div["division_id"]) == div["division_id"] else f"#{div['division_id']}"),
        }
        for div in divisions
    ]


def romanize_cjk(value: str) -> str:
    if not re.search(r"[\u4e00-\u9fff]", value):
        return value
    if lazy_pinyin is None or Style is None:
        raise RuntimeError("pypinyin is required to generate English slugs from Chinese collection names.")
    parts: list[str] = []
    buffer: list[str] = []
    for char in value:
        if "\u4e00" <= char <= "\u9fff":
            if buffer:
                parts.append("".join(buffer))
                buffer = []
            parts.extend(lazy_pinyin(char, style=Style.NORMAL, errors="ignore"))
        else:
            buffer.append(char)
    if buffer:
        parts.append("".join(buffer))
    return " ".join(part for part in parts if part)


def slugify(value: str, fallback: str = "textoria") -> str:
    value = unicodedata.normalize("NFKC", value).strip().lower()
    value = romanize_cjk(value)
    value = re.sub(r"[\s_]+", "-", value)
    value = re.sub(r"[^\w\-]+", "", value)
    value = re.sub(r"-{2,}", "-", value)
    return value.strip("-") or fallback


def write_stage_report(paths: BuildPaths, stage: str, report: dict) -> None:
    report = {"stage": stage, "generated_at": now_iso(), **report}
    write_json(paths.stages / f"{stage}.json", report)
