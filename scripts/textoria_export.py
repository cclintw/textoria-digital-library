#!/usr/bin/env python3
"""Textoria CSV/JSON export stage."""

from __future__ import annotations

from textoria_common import BuildPaths, CSV_FIELDS, make_toc, now_iso, write_csv, write_json, write_stage_report


STRUCTURE_TABLES = ("collections", "documents", "divisions", "paragraphs", "sentences", "tokens")


def reader_paragraphs(data: dict) -> list[dict]:
    div_by_id = {div["division_id"]: div for div in data["divisions"]}
    rows = []
    for para in data["paragraphs"]:
        div = div_by_id.get(para["division_id"], {})
        rows.append({**para, "division_path": div.get("path", ""), "division_title": div.get("title", "")})
    return rows


def export_intermediate_files(paths: BuildPaths, data: dict) -> dict:
    for key in STRUCTURE_TABLES:
        write_json(paths.intermediate / f"{key}.json", data[key])

    for table, table_fields in CSV_FIELDS.items():
        write_csv(paths.csv / f"{table}.csv", data.get(table, []), table_fields)

    counts = {key: len(data[key]) for key in ("documents", "divisions", "paragraphs", "sentences", "tokens")}
    collection_json = {
        "collection": data["collections"][0],
        "counts": counts,
        "documents": data["documents"],
    }
    read_index = reader_paragraphs(data)
    write_json(paths.json / "collection.json", collection_json)
    write_json(paths.json / "documents.json", {"documents": data["documents"]})
    write_json(paths.json / "divisions.json", {"divisions": data["divisions"]})
    write_json(paths.json / "paragraphs.json", {"paragraphs": data["paragraphs"]})
    write_json(paths.json / "toc.json", {"items": make_toc(data["divisions"])})
    write_json(paths.json / "reader_index.json", {"paragraphs": read_index})
    write_json(
        paths.json / "metadata.json",
        {
            "collection": data["collections"][0],
            "documents": data["documents"],
            "source_files": data["source_files"],
            "generated_at": now_iso(),
            "counts": counts,
            "structure_report": data.get("structure_report", {}),
        },
    )
    outputs = {"counts": counts, "reader_paragraphs": read_index}
    write_stage_report(paths, "export_intermediate_files", {"ok": True, "counts": counts})
    return outputs
