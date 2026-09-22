#!/usr/bin/env python3
"""Textoria structure stage."""

from __future__ import annotations

import re
from pathlib import Path

from textoria_common import BuildPaths, now_iso, write_json, write_stage_report


CHINESE_NUMERAL_CHARS = "一二三四五六七八九十百千〇零○兩"
CANDIDATE_HEADING_RE = re.compile(
    rf"^(第[{CHINESE_NUMERAL_CHARS}\d]+[卷回章節])(?:[\s　]+.{{2,}}|(?!中既將)\S.{{1,}})\s*$"
)
CHAPTER_TITLE_RE = re.compile(rf"^(第[{CHINESE_NUMERAL_CHARS}\d]+[卷回章節])[\s　]*(.+?)\s*$")


def normalize_candidate_heading_title(text: str) -> str:
    match = CHAPTER_TITLE_RE.match(text.strip())
    if not match:
        return text.strip()
    marker, title = match.groups()
    return f"{marker}　{title.strip()}"


def heading_level(line: str, *, confirm_candidate_headings: bool = False) -> tuple[int, str] | None:
    match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
    if match:
        return len(match.group(1)), match.group(2).strip()

    plain_patterns = [
        r"^(卷[上中下\d一二三四五六七八九十百]+)\s*$",
        r"^(第[一二三四五六七八九十百\d]+[卷回章節])\s*$",
    ]
    for pattern in plain_patterns:
        plain = re.match(pattern, line.strip())
        if plain:
            return 2, plain.group(1).strip()

    if confirm_candidate_headings:
        candidate = CANDIDATE_HEADING_RE.match(line.strip())
        if candidate:
            return 2, normalize_candidate_heading_title(line)
    return None


def candidate_heading_samples(cleaned: str, limit: int = 5) -> tuple[int, list[str]]:
    samples: list[str] = []
    count = 0
    for line in cleaned.splitlines():
        text = line.strip()
        if not CANDIDATE_HEADING_RE.match(text):
            continue
        count += 1
        if len(samples) < limit:
            samples.append(normalize_candidate_heading_title(text))
    return count, samples


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[。！？!?；;])", text)
    return [part.strip() for part in parts if part.strip()]


def infer_division_type(title: str) -> str:
    if re.search(r"卷[上中下\d一二三四五六七八九十百]+", title):
        return "volume"
    if re.search(r"第[一二三四五六七八九十百\d]+回", title):
        return "chapter"
    if re.search(r"第[一二三四五六七八九十百\d]+章", title):
        return "chapter"
    if re.search(r"第[一二三四五六七八九十百\d]+節", title):
        return "section"
    if re.search(r"\d{4}[-年]", title):
        return "date"
    return "heading"


def evaluate_structure_confidence(cleaned: str, divisions: list[dict], source_ext: str, *, confirmed_candidate_headings: bool = False) -> dict:
    md_heading_count = len(re.findall(r"^#{1,6}\s+", cleaned, flags=re.M))
    plain_heading_count = len(
        re.findall(r"^(卷[上中下\d一二三四五六七八九十百]+|第[一二三四五六七八九十百\d]+[卷回章節])\s*$", cleaned, flags=re.M)
    )
    candidate_heading_count, candidate_samples = candidate_heading_samples(cleaned)
    paragraph_count = len([block for block in re.split(r"\n\s*\n", cleaned) if block.strip()])

    evidence = []
    if md_heading_count:
        evidence.append(f"found {md_heading_count} Markdown or HTML-derived heading lines")
    if plain_heading_count:
        evidence.append(f"found {plain_heading_count} repeated plain-text heading markers")
    if candidate_heading_count:
        if confirmed_candidate_headings:
            evidence.append(f"confirmed {candidate_heading_count} candidate chapter-heading lines")
        else:
            evidence.append(f"found {candidate_heading_count} candidate chapter-heading lines that need user confirmation")
    evidence.append(f"found {paragraph_count} paragraph-like blocks")

    if md_heading_count:
        confidence = "high"
    elif plain_heading_count >= 2 or confirmed_candidate_headings:
        confidence = "medium"
    elif divisions and paragraph_count >= 2 and source_ext in {"html", "htm", "md"}:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "confidence": confidence,
        "evidence": evidence,
        "needs_user_confirmation": confidence == "low",
        "candidate_heading_count": candidate_heading_count,
        "candidate_heading_samples": candidate_samples,
    }


def build_structure(
    cleaned: str,
    source_file: str,
    title_hint: str,
    collection_name: str | None = None,
    *,
    confirm_candidate_headings: bool = False,
) -> dict[str, list[dict] | dict]:
    collection_title = collection_name or title_hint
    collection = {
        "collection_id": "col-0001",
        "name": collection_title,
        "slug": "col-0001",
        "title": collection_title,
        "subtitle": "",
        "description": "",
        "collection_type": "digital_archive",
        "language": "zh-Hant",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "metadata_json": "{}",
    }
    documents: list[dict] = []
    divisions: list[dict] = []
    paragraphs: list[dict] = []
    sentences: list[dict] = []
    tokens: list[dict] = []

    doc_count = 0
    div_count = 0
    paragraph_count = 0
    sentence_count = 0
    current_doc = None
    stack: dict[int, str] = {}
    div_sort_by_parent: dict[str, int] = {}
    para_buffer: list[str] = []
    current_division_id: str | None = None
    char_cursor = 0

    def ensure_document(title: str | None = None) -> dict:
        nonlocal doc_count, current_doc
        if current_doc is not None:
            return current_doc
        doc_count += 1
        current_doc = {
            "document_id": f"doc-{doc_count:04d}",
            "collection_id": collection["collection_id"],
            "title": title or title_hint,
            "document_type": "text",
            "creator": "",
            "date": "",
            "publisher": "",
            "source": "",
            "identifier": "",
            "language": "zh-Hant",
            "rights": "",
            "source_file": source_file,
            "source_format": Path(source_file).suffix.lower().lstrip("."),
            "source_encoding": "utf-8",
            "sort_key": f"{doc_count:04d}",
            "char_start": 0,
            "char_end": "",
            "metadata_json": "{}",
        }
        documents.append(current_doc)
        return current_doc

    def path_for(parent_id: str | None, title: str) -> str:
        if not parent_id:
            return "/" + title
        parent = next((d for d in divisions if d["division_id"] == parent_id), None)
        return (parent["path"] if parent else "") + "/" + title

    def create_division(level: int, division_type: str, title: str) -> str:
        nonlocal div_count, current_division_id
        doc = ensure_document()
        parent_id = stack.get(level - 1) if level > 1 else None
        div_count += 1
        parent_key = parent_id or doc["document_id"]
        div_sort_by_parent[parent_key] = div_sort_by_parent.get(parent_key, 0) + 1
        division_id = f"div-{div_count:06d}"
        divisions.append(
            {
                "division_id": division_id,
                "collection_id": collection["collection_id"],
                "document_id": doc["document_id"],
                "parent_division_id": parent_id or "",
                "level": level,
                "division_type": division_type,
                "title": title,
                "label": title,
                "n": "",
                "sort_order": div_sort_by_parent[parent_key],
                "path": path_for(parent_id, title),
                "char_start": "",
                "char_end": "",
                "metadata_json": "{}",
            }
        )
        stack[level] = division_id
        for stale in [key for key in stack if key > level]:
            del stack[stale]
        current_division_id = division_id
        return division_id

    def flush_paragraphs() -> None:
        nonlocal paragraph_count, sentence_count, para_buffer, char_cursor
        text = "\n".join(para_buffer).strip()
        para_buffer = []
        if not text:
            return
        doc = ensure_document()
        division_id = current_division_id or (divisions[-1]["division_id"] if divisions else "")
        if current_division_id is None and not divisions:
            create_division(1, "text", doc["title"])
            division_id = current_division_id or divisions[-1]["division_id"]
        for raw_para in re.split(r"\n\s*\n", text):
            para = raw_para.strip()
            if not para:
                continue
            paragraph_count += 1
            start = cleaned.find(para, char_cursor)
            if start < 0:
                start = char_cursor
            end = start + len(para)
            char_cursor = end
            paragraph_id = f"p-{paragraph_count:07d}"
            paragraphs.append(
                {
                    "paragraph_id": paragraph_id,
                    "collection_id": collection["collection_id"],
                    "document_id": doc["document_id"],
                    "division_id": division_id,
                    "paragraph_index": paragraph_count,
                    "text": para,
                    "char_start": start,
                    "char_end": end,
                    "source_file": source_file,
                    "metadata_json": "{}",
                }
            )
            for sentence_index, sentence in enumerate(split_sentences(para), start=1):
                sentence_count += 1
                sentences.append(
                    {
                        "sentence_id": f"s-{sentence_count:07d}",
                        "collection_id": collection["collection_id"],
                        "document_id": doc["document_id"],
                        "division_id": division_id,
                        "paragraph_id": paragraph_id,
                        "sentence_index": sentence_index,
                        "text": sentence,
                        "char_start": start,
                        "char_end": end,
                        "metadata_json": "{}",
                    }
                )

    for line in cleaned.splitlines():
        heading = heading_level(line, confirm_candidate_headings=confirm_candidate_headings)
        if heading:
            flush_paragraphs()
            md_level, heading_title = heading
            if md_level == 1:
                current_doc = None
                stack.clear()
                ensure_document(heading_title)
                current_division_id = None
            else:
                create_division(md_level - 1, infer_division_type(heading_title), heading_title)
            continue
        para_buffer.append(line)
    flush_paragraphs()

    if not documents:
        ensure_document(title_hint)
    if not divisions:
        create_division(1, "text", documents[0]["title"])

    for doc in documents:
        doc["char_end"] = len(cleaned)

    source_files = [
        {
            "source_file_id": "src-0001",
            "collection_id": collection["collection_id"],
            "document_id": documents[0]["document_id"],
            "original_path": source_file,
            "prepared_path": "",
            "extracted_text_path": "",
            "file_format": Path(source_file).suffix.lower().lstrip("."),
            "detected_encoding": "utf-8",
            "byte_size": "",
            "line_count": "",
            "sha256": "",
            "sort_order": 1,
            "metadata_json": "{}",
        }
    ]
    metadata: list[dict] = []
    structure_report = evaluate_structure_confidence(
        cleaned,
        divisions,
        Path(source_file).suffix.lower().lstrip("."),
        confirmed_candidate_headings=confirm_candidate_headings,
    )
    return {
        "collections": [collection],
        "documents": documents,
        "divisions": divisions,
        "paragraphs": paragraphs,
        "sentences": sentences,
        "tokens": tokens,
        "source_files": source_files,
        "metadata": metadata,
        "structure_report": structure_report,
    }


def write_structure_review(paths: BuildPaths, data: dict) -> None:
    divisions = data["divisions"]
    report = data["structure_report"]
    preview = {
        "confidence": report["confidence"],
        "evidence": report["evidence"],
        "division_count": len(divisions),
        "paragraph_count": len(data["paragraphs"]),
        "divisions": divisions,
    }
    write_json(paths.intermediate / "structure_preview.json", preview)
    lines = [
        "# Textoria Structure Preview",
        "",
        f"- confidence: {report['confidence']}",
        f"- divisions: {len(divisions)}",
        f"- paragraphs: {len(data['paragraphs'])}",
        "",
        "## Evidence",
        "",
    ]
    lines.extend(f"- {item}" for item in report["evidence"])
    lines.extend(["", "## Inferred Divisions", ""])
    lines.extend(f"{'#' * min(int(div['level']) + 1, 6)} {div['path']}" for div in divisions)
    (paths.intermediate / "structure_preview.md").write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

    review_lines = [
        "# Division Review",
        "",
        "These divisions were inferred automatically. Edit the cleaned or merged Markdown source, then rebuild structure if they are wrong.",
        "",
    ]
    for div in divisions:
        indent = "  " * (int(div["level"]) - 1)
        review_lines.append(f"{indent}- {div['division_id']} | level {div['level']} | {div['division_type']} | {div['title']}")
    (paths.intermediate / "division_review.md").write_text("\n".join(review_lines).strip() + "\n", encoding="utf-8")
    write_stage_report(paths, "structure_text", {"ok": True, **preview})
