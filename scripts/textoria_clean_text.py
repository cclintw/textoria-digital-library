#!/usr/bin/env python3
"""Textoria text-cleaning stage."""

from __future__ import annotations

import re
import unicodedata

from textoria_common import BuildPaths, write_json, write_stage_report


PUNCT_MAP = str.maketrans(
    {
        "﹃": "『",
        "﹄": "』",
        "﹁": "「",
        "﹂": "」",
        "︿": "〈",
        "﹀": "〉",
        "︽": "《",
        "︾": "》",
    }
)

HALFWIDTH_PUNCT = {
    "!": "！",
    "#": "＃",
    "$": "＄",
    "%": "％",
    "&": "＆",
    "'": "’",
    "(": "（",
    ")": "）",
    "*": "＊",
    "+": "＋",
    ",": "，",
    "-": "－",
    ".": "。",
    "/": "／",
    ":": "：",
    ";": "；",
    "<": "＜",
    "=": "＝",
    ">": "＞",
    "?": "？",
    "@": "＠",
    "[": "［",
    "\\": "＼",
    "]": "］",
    "^": "＾",
    "_": "＿",
    "`": "｀",
    "{": "｛",
    "|": "｜",
    "}": "｝",
    "~": "～",
}


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\ufeff", "")
    text = text.replace("\ufffd", "■")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
    return unicodedata.normalize("NFKC", text)


def is_markdown_protected(line: str) -> bool:
    return bool(
        re.match(r"^\s{0,3}#{1,6}\s+", line)
        or re.match(r"^\s*\|.*\|\s*$", line)
        or re.match(r"^\s*\[\^[^\]]+\]:", line)
        or re.search(r"!\[[^\]]*\]\([^)]+\)", line)
    )


def convert_punctuation_line(line: str) -> str:
    converted = []
    open_quote = True
    for char in line:
        if char == '"':
            converted.append("「" if open_quote else "」")
            open_quote = not open_quote
        elif char == "“":
            converted.append("「")
            open_quote = False
        elif char == "”":
            converted.append("」")
            open_quote = True
        else:
            converted.append(HALFWIDTH_PUNCT.get(char, char))
    return "".join(converted)


def clean_cc_text(text: str) -> tuple[str, dict]:
    before_chars = len(text)
    before_lines = text.count("\n") + 1
    invalid_before = text.count("■")
    text = normalize_text(text).translate(PUNCT_MAP)

    lines = []
    for line in text.split("\n"):
        if is_markdown_protected(line):
            lines.append(line.rstrip())
            continue
        line = re.sub(r"(?<![A-Za-z0-9])[ \t]+|[ \t]+(?![A-Za-z0-9])", "", line)
        line = convert_punctuation_line(line)
        lines.append(line.rstrip())

    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
    report = {
        "profile": "cc_text_cleaner",
        "normalization": "NFKC",
        "rules_applied": [
            "normalize_line_endings",
            "remove_control_characters",
            "replace_invalid_characters",
            "normalize_vertical_punctuation",
            "convert_halfwidth_punctuation_in_prose",
            "convert_curly_double_quotes",
            "collapse_excess_blank_lines",
        ],
        "rules_skipped": [],
        "invalid_character_count": invalid_before,
        "replacement_marker_count": text.count("■"),
        "char_count_before": before_chars,
        "char_count_after": len(text),
        "line_count_before": before_lines,
        "line_count_after": text.count("\n") + 1,
        "warnings": [],
    }
    return text, report


def clean_text(plain_text: str, plain_path, paths: BuildPaths, detected_encoding: str) -> dict:
    cleaned, report = clean_cc_text(plain_text)
    clean_path = paths.clean / "cleaned_text.md"
    clean_path.write_text(cleaned, encoding="utf-8")
    report.update({"input_file": str(plain_path), "output_file": str(clean_path), "detected_encoding": detected_encoding})
    write_json(paths.clean / "cleaning_report.json", report)
    write_stage_report(paths, "clean_text", {"ok": True, **report})
    return {"text": cleaned, "clean_path": clean_path, "report": report}
