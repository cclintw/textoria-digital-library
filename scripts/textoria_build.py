#!/usr/bin/env python3
"""Run the Textoria v1 full archive workflow.

This file is intentionally thin. Stage logic lives in separate modules so each
pipeline step can be edited, tested, and rebuilt independently.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from textoria_build_epub import build_epub
from textoria_build_search import build_search_index
from textoria_build_site import build_static_site
from textoria_build_sqlite import build_sqlite_stage
from textoria_clean_text import clean_text
from textoria_common import (
    SUPPORTED_EXTENSIONS,
    TEXTORIA_VERSION,
    default_collection_name,
    default_collection_output,
    default_collection_slug,
    ensure_dirs,
    now_iso,
    write_json,
)
from textoria_export import export_intermediate_files
from textoria_extract_text import extract_plain_text
from textoria_structure import build_structure, write_structure_review
from textoria_utf8_converter import prepare_utf8
from textoria_validate import validate_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a Textoria archive from one supported source file.")
    parser.add_argument("source")
    parser.add_argument("--project-root")
    parser.add_argument("--output")
    parser.add_argument("--collection-name", help="Confirmed human-readable collection name. Defaults to the source filename stem in non-interactive runs.")
    parser.add_argument("--text-column")
    parser.add_argument(
        "--confirm-inferred-structure",
        action="store_true",
        help="Use candidate plain-text heading rules after the user confirms the proposed structure.",
    )
    parser.add_argument("--epub", action="store_true", help="Also generate textoria/collections/<collection_slug>/epub/<collection_slug>.epub")
    return parser.parse_args()


def relative_to_project(path: Path, project_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(project_root.resolve()))
    except ValueError:
        return str(path)


def read_project_registry(project_root: Path) -> dict:
    registry_path = project_root / "textoria" / "registry.json"
    if not registry_path.exists():
        return {"collections": []}
    try:
        return json.loads(registry_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"collections": []}


def resolve_collection_slug(project_root: Path, source: Path, collection_name: str) -> str:
    base_slug = default_collection_slug(source, collection_name)
    registry = read_project_registry(project_root)
    source_path = relative_to_project(source, project_root)
    used_slugs = set()
    for entry in registry.get("collections", []):
        entry_slug = entry.get("slug") or entry.get("collection_id") or entry.get("archive_id")
        if not entry_slug:
            continue
        if source_path in entry.get("source_files", []):
            return entry_slug
        used_slugs.add(entry_slug)
    if base_slug not in used_slugs:
        return base_slug
    suffix = 2
    while f"{base_slug}-{suffix}" in used_slugs:
        suffix += 1
    return f"{base_slug}-{suffix}"


def retag_collection(data: dict, collection_slug: str) -> None:
    old_collection_id = data["collections"][0]["collection_id"]
    data["collections"][0]["collection_id"] = collection_slug
    data["collections"][0]["slug"] = collection_slug
    for table in ("documents", "divisions", "paragraphs", "sentences", "tokens", "source_files"):
        for row in data.get(table, []):
            if row.get("collection_id") == old_collection_id:
                row["collection_id"] = collection_slug


def write_manifest(paths, source: Path, data: dict, clean_path: Path, db_path: Path, epub_manifest: dict | None) -> None:
    collection = data["collections"][0]
    outputs = {
        "cleaned_text": str(clean_path),
        "sqlite": str(db_path),
        "site": str(paths.site),
        "structure_preview": str(paths.intermediate / "structure_preview.md"),
        "division_review": str(paths.intermediate / "division_review.md"),
        "divisions_json": str(paths.json / "divisions.json"),
        "divisions_csv": str(paths.csv / "divisions.csv"),
    }
    if epub_manifest:
        outputs["epub"] = epub_manifest["epub"]

    manifest = {
        "collection_id": collection["collection_id"],
        "collection_slug": collection["slug"],
        "collection_name": collection["name"],
        "project_name": collection["name"],
        "textoria_version": TEXTORIA_VERSION,
        "source_files": [str(source)],
        "created_at": now_iso(),
        "workflow": "build_fulltext_archive",
        "outputs": outputs,
        "structure_report": data.get("structure_report", {}),
    }
    write_json(paths.root / "manifest.json", manifest)
    (paths.config / "textoria.yml").write_text("workflow: build_fulltext_archive\ncleaning_profile: cc_text_cleaner\n", encoding="utf-8")


def update_project_registry(project_root: Path, output: Path, source: Path, data: dict, collection_slug: str) -> None:
    textoria_root = project_root / "textoria"
    textoria_root.mkdir(parents=True, exist_ok=True)
    registry_path = textoria_root / "registry.json"
    registry = read_project_registry(project_root)

    collection = data["collections"][0]
    archive_path = relative_to_project(output, project_root)
    collection_id = collection_slug

    entry = {
        "collection_id": collection_id,
        "archive_id": collection_id,
        "slug": collection_id,
        "name": collection["name"],
        "title": collection["title"],
        "path": archive_path,
        "source_files": [relative_to_project(source, project_root)],
        "updated_at": now_iso(),
    }

    collections = registry.get("collections", [])
    replaced = False
    for index, existing in enumerate(collections):
        if existing.get("path") == archive_path or existing.get("collection_id") == collection_id:
            collections[index] = {**existing, **entry}
            replaced = True
            break
    if not replaced:
        collections.append(entry)
    registry["collections"] = collections
    write_json(registry_path, registry)


def build_fulltext_archive(
    source: Path,
    project_root: Path,
    output: Path,
    text_column: str | None,
    include_epub: bool,
    collection_name: str,
    collection_slug: str,
    confirm_inferred_structure: bool = False,
) -> dict:
    if source.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise SystemExit(f"Unsupported input format: {source.suffix}")

    paths = ensure_dirs(output)
    prepared = prepare_utf8(source, paths)
    extracted = extract_plain_text(source, prepared["text"], text_column, paths)
    cleaned = clean_text(extracted["text"], extracted["plain_path"], paths, prepared["manifest"]["detected_encoding"])

    data = build_structure(
        cleaned["text"],
        str(source),
        source.stem,
        collection_name=collection_name,
        confirm_candidate_headings=confirm_inferred_structure,
    )
    retag_collection(data, collection_slug)
    data["source_files"][0].update(
        {
            "prepared_path": str(prepared["prepared_path"]),
            "extracted_text_path": str(extracted["plain_path"]),
            "detected_encoding": prepared["manifest"]["detected_encoding"],
            "byte_size": prepared["manifest"]["byte_size"],
            "line_count": prepared["manifest"]["line_count"],
            "sha256": prepared["manifest"]["sha256"],
        }
    )
    write_structure_review(paths, data)

    structure_report = data["structure_report"]
    if structure_report["confidence"] == "low":
        samples = structure_report.get("candidate_heading_samples", [])
        if samples:
            question = (
                "我目前無法可靠判斷這份文本的章節結構，但看到可能的章節標題："
                + "、".join(samples)
                + "。請確認是否以這類標題作為第一層 division。"
            )
        else:
            question = "我目前無法可靠判斷這份文本的章節結構。你可以提供章節切分規則嗎？或讓我先自行判斷並提出建議。"
        return {
            "ok": False,
            "status": "needs_structure_confirmation",
            "collection_id": collection_slug,
            "collection_slug": collection_slug,
            "collection_name": collection_name,
            "output": str(output),
            "cleaned_text": str(cleaned["clean_path"]),
            "structure_preview": str(paths.intermediate / "structure_preview.md"),
            "division_review": str(paths.intermediate / "division_review.md"),
            "structure_confidence": structure_report["confidence"],
            "structure_evidence": structure_report["evidence"],
            "candidate_heading_count": structure_report.get("candidate_heading_count", 0),
            "candidate_heading_samples": samples,
            "question": question,
            "next_command_hint": "--confirm-inferred-structure",
            "project_root": str(project_root),
        }

    exported = export_intermediate_files(paths, data)
    db_path = build_sqlite_stage(paths, data)
    build_search_index(paths, db_path, exported["reader_paragraphs"])
    build_static_site(paths, data, exported["reader_paragraphs"])
    epub_manifest = build_epub(paths, data) if include_epub else None

    write_manifest(paths, source, data, cleaned["clean_path"], db_path, epub_manifest)
    update_project_registry(project_root, output, source, data, collection_slug)
    validation = validate_outputs(paths, db_path, include_epub=include_epub)
    (paths.logs / "build.log").write_text("Textoria build completed.\n", encoding="utf-8")

    divisions = data["divisions"]
    result = {
        "ok": validation["ok"],
        "collection_id": collection_slug,
        "collection_slug": collection_slug,
        "collection_name": collection_name,
        "output": str(output),
        "sqlite": str(db_path),
        "site": str(paths.site),
        "epub": epub_manifest["epub"] if epub_manifest else None,
        "cleaned_text": str(cleaned["clean_path"]),
        "structure_preview": str(paths.intermediate / "structure_preview.md"),
        "division_review": str(paths.intermediate / "division_review.md"),
        "divisions_csv": str(paths.csv / "divisions.csv"),
        "divisions_json": str(paths.json / "divisions.json"),
        "structure_confidence": data["structure_report"]["confidence"],
        "structure_evidence": data["structure_report"]["evidence"],
        "division_count": len(divisions),
        "division_sample": [div["path"] for div in divisions[:12]],
        "validation": validation,
        "project_root": str(project_root),
    }
    return result


def main() -> int:
    args = parse_args()
    source = Path(args.source).resolve()
    project_root = Path(args.project_root).resolve() if args.project_root else source.parent.resolve()
    collection_name = args.collection_name or default_collection_name(source)
    collection_slug = resolve_collection_slug(project_root, source, collection_name)
    output = Path(args.output).resolve() if args.output else default_collection_output(project_root, source, collection_name, collection_slug)
    result = build_fulltext_archive(
        source,
        project_root,
        output,
        args.text_column,
        args.epub,
        collection_name,
        collection_slug,
        confirm_inferred_structure=args.confirm_inferred_structure,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("status") == "needs_structure_confirmation":
        return 2
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
