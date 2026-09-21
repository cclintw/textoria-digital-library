#!/usr/bin/env python3
"""Textoria SQLite and FTS5 database stage."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from textoria_common import BuildPaths, write_stage_report


def build_sqlite(db_path: Path, data: dict[str, list[dict]]) -> None:
    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(db_path)
    con.executescript(
        """
        PRAGMA foreign_keys = ON;
        CREATE TABLE collections (
            collection_id TEXT PRIMARY KEY, title TEXT NOT NULL, subtitle TEXT,
            description TEXT, collection_type TEXT, language TEXT, created_at TEXT,
            updated_at TEXT, metadata_json TEXT
        );
        CREATE TABLE documents (
            document_id TEXT PRIMARY KEY, collection_id TEXT NOT NULL, title TEXT NOT NULL,
            document_type TEXT, creator TEXT, date TEXT, publisher TEXT, source TEXT,
            identifier TEXT, language TEXT, rights TEXT, source_file TEXT, source_format TEXT,
            source_encoding TEXT, sort_key TEXT, char_start INTEGER, char_end INTEGER,
            metadata_json TEXT
        );
        CREATE TABLE divisions (
            division_id TEXT PRIMARY KEY, collection_id TEXT NOT NULL, document_id TEXT NOT NULL,
            parent_division_id TEXT, level INTEGER NOT NULL, division_type TEXT, title TEXT NOT NULL,
            label TEXT, n TEXT, sort_order INTEGER NOT NULL, path TEXT, char_start INTEGER,
            char_end INTEGER, metadata_json TEXT
        );
        CREATE TABLE paragraphs (
            paragraph_id TEXT PRIMARY KEY, collection_id TEXT NOT NULL, document_id TEXT NOT NULL,
            division_id TEXT, paragraph_index INTEGER NOT NULL, text TEXT NOT NULL,
            char_start INTEGER, char_end INTEGER, source_file TEXT, metadata_json TEXT
        );
        CREATE TABLE sentences (
            sentence_id TEXT PRIMARY KEY, collection_id TEXT NOT NULL, document_id TEXT NOT NULL,
            division_id TEXT, paragraph_id TEXT NOT NULL, sentence_index INTEGER NOT NULL,
            text TEXT NOT NULL, char_start INTEGER, char_end INTEGER, metadata_json TEXT
        );
        CREATE TABLE tokens (
            token_id TEXT PRIMARY KEY, collection_id TEXT NOT NULL, document_id TEXT NOT NULL,
            division_id TEXT, paragraph_id TEXT, sentence_id TEXT, token_index INTEGER NOT NULL,
            text TEXT NOT NULL, normalized_text TEXT, char_start INTEGER, char_end INTEGER,
            token_type TEXT, metadata_json TEXT
        );
        CREATE TABLE source_files (
            source_file_id TEXT PRIMARY KEY, collection_id TEXT NOT NULL, document_id TEXT,
            original_path TEXT NOT NULL, prepared_path TEXT, extracted_text_path TEXT,
            file_format TEXT NOT NULL, detected_encoding TEXT, byte_size INTEGER,
            line_count INTEGER, sha256 TEXT, sort_order INTEGER, metadata_json TEXT
        );
        CREATE TABLE metadata (
            metadata_id TEXT PRIMARY KEY, subject_table TEXT NOT NULL, subject_id TEXT NOT NULL,
            key TEXT NOT NULL, value TEXT, scheme TEXT, language TEXT, source TEXT
        );
        CREATE INDEX idx_divisions_parent ON divisions(parent_division_id);
        CREATE INDEX idx_paragraphs_division ON paragraphs(division_id);
        CREATE VIRTUAL TABLE paragraphs_fts USING fts5(
            paragraph_id UNINDEXED, collection_id UNINDEXED, document_id UNINDEXED,
            division_id UNINDEXED, document_title, division_path, division_title, text,
            tokenize = 'unicode61'
        );
        """
    )
    for table in ("collections", "documents", "divisions", "paragraphs", "sentences", "tokens", "source_files", "metadata"):
        rows = data[table]
        if not rows:
            continue
        fields = list(rows[0].keys())
        placeholders = ", ".join(["?"] * len(fields))
        con.executemany(
            f"INSERT INTO {table} ({', '.join(fields)}) VALUES ({placeholders})",
            [[row.get(field, "") for field in fields] for row in rows],
        )
    con.execute(
        """
        INSERT INTO paragraphs_fts (
            paragraph_id, collection_id, document_id, division_id,
            document_title, division_path, division_title, text
        )
        SELECT p.paragraph_id, p.collection_id, p.document_id, p.division_id,
               d.title, COALESCE(v.path, ''), COALESCE(v.title, ''), p.text
        FROM paragraphs p
        LEFT JOIN documents d ON p.document_id = d.document_id
        LEFT JOIN divisions v ON p.division_id = v.division_id
        """
    )
    con.commit()
    con.close()


def build_sqlite_stage(paths: BuildPaths, data: dict) -> Path:
    db_path = paths.sqlite / "library.sqlite"
    build_sqlite(db_path, data)
    write_stage_report(paths, "build_sqlite", {"ok": True, "database": str(db_path)})
    return db_path
