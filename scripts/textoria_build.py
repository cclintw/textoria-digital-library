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
from textoria_common import SUPPORTED_EXTENSIONS, TEXTORIA_VERSION, ensure_dirs, now_iso, slugify, write_json
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
    parser.add_argument("--text-column")
    parser.add_argument("--epub", action="store_true", help="Also generate textoria/epub/<collection_slug>.epub")
    return parser.parse_args()


def relative_to_project(path: Path, project_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(project_root.resolve()))
    except ValueError:
        return str(path)


def write_manifest(paths, source: Path, data: dict, clean_path: Path, db_path: Path, epub_manifest: dict | None) -> None:
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
        "project_name": data["collections"][0]["title"],
        "textoria_version": TEXTORIA_VERSION,
        "source_files": [str(source)],
        "created_at": now_iso(),
        "workflow": "build_fulltext_archive",
        "outputs": outputs,
        "structure_report": data.get("structure_report", {}),
    }
    write_json(paths.root / "manifest.json", manifest)
    (paths.config / "textoria.yml").write_text("workflow: build_fulltext_archive\ncleaning_profile: cc_text_cleaner\n", encoding="utf-8")


def update_project_registry(project_root: Path, output: Path, source: Path, data: dict) -> None:
    textoria_root = project_root / "textoria"
    textoria_root.mkdir(parents=True, exist_ok=True)
    registry_path = textoria_root / "registry.json"
    if registry_path.exists():
        try:
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            registry = {"collections": []}
    else:
        registry = {"collections": []}

    collection = data["collections"][0]
    archive_path = relative_to_project(output, project_root)
    if output.resolve() == textoria_root.resolve():
        collection_id = "default"
    else:
        collection_id = slugify(output.name, fallback=collection.get("collection_id", "collection"))

    entry = {
        "collection_id": collection_id,
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


def build_fulltext_archive(source: Path, project_root: Path, output: Path, text_column: str | None, include_epub: bool) -> dict:
    if source.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise SystemExit(f"Unsupported input format: {source.suffix}")

    paths = ensure_dirs(output)
    prepared = prepare_utf8(source, paths)
    extracted = extract_plain_text(source, prepared["text"], text_column, paths)
    cleaned = clean_text(extracted["text"], extracted["plain_path"], paths, prepared["manifest"]["detected_encoding"])

    data = build_structure(cleaned["text"], str(source), source.stem)
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

    exported = export_intermediate_files(paths, data)
    db_path = build_sqlite_stage(paths, data)
    build_search_index(paths, db_path, exported["reader_paragraphs"])
    build_static_site(paths, data, exported["reader_paragraphs"])
    epub_manifest = build_epub(paths, data) if include_epub else None

    write_manifest(paths, source, data, cleaned["clean_path"], db_path, epub_manifest)
    update_project_registry(project_root, output, source, data)
    validation = validate_outputs(paths, db_path, include_epub=include_epub)
    (paths.logs / "build.log").write_text("Textoria build completed.\n", encoding="utf-8")

    divisions = data["divisions"]
    result = {
        "ok": validation["ok"],
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
    output = Path(args.output).resolve() if args.output else project_root / "textoria"
    result = build_fulltext_archive(source, project_root, output, args.text_column, args.epub)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
