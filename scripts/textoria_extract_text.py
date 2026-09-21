#!/usr/bin/env python3
"""Textoria plain-text extraction stage."""

from __future__ import annotations

import csv
import html
from pathlib import Path

from bs4 import BeautifulSoup, Comment

from textoria_common import BuildPaths, write_json, write_stage_report


def soup_to_markdown(text: str) -> str:
    soup = BeautifulSoup(text, "html.parser")
    for item in soup(["script", "style", "head", "svg", "nav"]):
        item.decompose()
    for comment in soup.find_all(string=lambda value: isinstance(value, Comment)):
        comment.extract()
    body = soup.body or soup
    chunks: list[str] = []

    def inline_text(node) -> str:
        return html.unescape(" ".join(node.get_text(" ", strip=True).split()))

    for node in body.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote", "table", "img"], recursive=True):
        if node.name and node.find_parent(["p", "li", "blockquote", "table"]) and node.name not in {"img"}:
            continue
        if node.name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            level = int(node.name[1])
            chunks.append(f"{'#' * level} {inline_text(node)}")
        elif node.name == "p":
            value = inline_text(node)
            if value:
                chunks.append(value)
        elif node.name == "li":
            value = inline_text(node)
            if value:
                chunks.append(f"- {value}")
        elif node.name == "blockquote":
            value = inline_text(node)
            if value:
                chunks.append("> " + value)
        elif node.name == "img":
            src = node.get("src", "")
            alt = node.get("alt", "")
            if src:
                chunks.append(f"![{alt}]({src})")
        elif node.name == "table":
            rows = []
            for tr in node.find_all("tr"):
                cells = [inline_text(cell).replace("|", "｜") for cell in tr.find_all(["th", "td"])]
                if cells:
                    rows.append(cells)
            if rows:
                width = max(len(row) for row in rows)
                table_lines = []
                for index, row in enumerate(rows):
                    row = row + [""] * (width - len(row))
                    table_lines.append("| " + " | ".join(row) + " |")
                    if index == 0:
                        table_lines.append("| " + " | ".join(["---"] * width) + " |")
                chunks.append("\n".join(table_lines))

    if not chunks:
        chunks = [body.get_text("\n", strip=True)]
    return "\n\n".join(chunk for chunk in chunks if chunk.strip()) + "\n"


def extract_plain_text(source: Path, prepared_text: str, text_column: str | None, paths: BuildPaths) -> dict:
    ext = source.suffix.lower()
    if ext in {".txt", ".md"}:
        plain = prepared_text
    elif ext in {".html", ".htm"}:
        plain = soup_to_markdown(prepared_text)
    elif ext == ".csv":
        rows = []
        with source.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            if not text_column or text_column not in (reader.fieldnames or []):
                raise ValueError("CSV input requires --text-column with a valid column name.")
            for row in reader:
                value = (row.get(text_column) or "").strip()
                if value:
                    rows.append(value)
        plain = "\n\n".join(rows) + "\n"
    else:
        raise ValueError(f"Unsupported extension: {ext}")

    plain_path = paths.intermediate / "plain_text.md"
    plain_path.write_text(plain, encoding="utf-8")
    report = {
        "input_file": str(source),
        "output_file": str(plain_path),
        "format": ext.lstrip("."),
        "warnings": [],
    }
    write_json(paths.intermediate / "extraction_report.json", report)
    write_stage_report(paths, "extract_plain_text", {"ok": True, **report})
    return {"text": plain, "plain_path": plain_path, "report": report}
