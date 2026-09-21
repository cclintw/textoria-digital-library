#!/usr/bin/env python3
"""Textoria UTF-8 preparation stage."""

from __future__ import annotations

import hashlib
import shutil
import unicodedata
import re
from pathlib import Path

from charset_normalizer import from_bytes

from textoria_common import BuildPaths, SUPPORTED_EXTENSIONS, write_json, write_stage_report


def detect_encoding(raw: bytes) -> tuple[str, float | None]:
    if raw.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig", 1.0
    try:
        raw.decode("utf-8")
        return "utf-8", 1.0
    except UnicodeDecodeError:
        pass

    result = from_bytes(raw).best()
    if result and result.encoding:
        return result.encoding, getattr(result, "percent_coherence", None)

    for encoding in ("big5hkscs", "big5", "shift_jis", "gb2312"):
        try:
            raw.decode(encoding)
            return encoding, None
        except UnicodeDecodeError:
            continue
    return "big5", None


def decode_to_text(raw: bytes, encoding: str) -> str:
    candidates = [encoding]
    if encoding.lower().replace("-", "") in {"big5", "big5hkscs"}:
        candidates = ["big5hkscs", "big5"]
    for candidate in candidates:
        try:
            return raw.decode(candidate, errors="replace")
        except LookupError:
            continue
    return raw.decode("utf-8", errors="replace")


def normalize_decoded_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\ufeff", "")
    text = text.replace("\ufffd", "■")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
    return unicodedata.normalize("NFKC", text)


def prepare_utf8(source: Path, paths: BuildPaths) -> dict:
    if source.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported input format: {source.suffix}")

    raw = source.read_bytes()
    encoding, confidence = detect_encoding(raw)
    decoded = normalize_decoded_text(decode_to_text(raw, encoding))
    source_hash = hashlib.sha256(raw).hexdigest()

    shutil.copy2(source, paths.raw_original / source.name)
    prepared_path = paths.prepared / f"{source.stem}.utf8{source.suffix.lower()}"
    prepared_path.write_text(decoded, encoding="utf-8")

    manifest = {
        "source_file": str(source),
        "extension": source.suffix.lower(),
        "detected_format": source.suffix.lower().lstrip("."),
        "detected_encoding": encoding,
        "encoding_confidence": confidence,
        "byte_size": len(raw),
        "line_count": decoded.count("\n") + 1,
        "has_bom": raw.startswith(b"\xef\xbb\xbf"),
        "readable": True,
        "sha256": source_hash,
        "prepared_path": str(prepared_path),
        "warnings": [],
    }
    write_json(paths.root / "raw" / "source_manifest.json", manifest)
    write_stage_report(paths, "convert_encoding", {"ok": True, "source_manifest": manifest})
    return {"text": decoded, "prepared_path": prepared_path, "manifest": manifest}
