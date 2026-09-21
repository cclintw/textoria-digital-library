#!/usr/bin/env python3
"""Textoria static-site stage with theme templates and SEO-friendly routes."""

from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from textoria_common import BuildPaths, write_json, write_stage_report


def esc(value) -> str:
    return html.escape(str(value or ""), quote=True)


def markdown_escape(value: str) -> str:
    return str(value or "").replace("\\", "\\\\").replace("#", "\\#")


def relative_prefix(depth: int) -> str:
    return "../" * depth


def brand_html(title: str) -> str:
    if len(title) >= 3:
        return f"{esc(title[:2])}<span class=\"brand-badge\">{esc(title[2])}</span>{esc(title[3:])}"
    return esc(title)


def build_site_indexes(data: dict) -> dict:
    paragraphs_by_div: dict[str, list[dict]] = {}
    children_by_parent: dict[str, list[dict]] = {}
    divisions_by_doc: dict[str, list[dict]] = {}

    for div in data["divisions"]:
        divisions_by_doc.setdefault(div["document_id"], []).append(div)
        children_by_parent.setdefault(div["parent_division_id"] or "", []).append(div)
    for para in data["paragraphs"]:
        paragraphs_by_div.setdefault(para["division_id"], []).append(para)

    return {
        "paragraphs_by_div": paragraphs_by_div,
        "children_by_parent": children_by_parent,
        "divisions_by_doc": divisions_by_doc,
    }


def division_href(div: dict, depth: int = 0) -> str:
    return f"{relative_prefix(depth)}read/{div['division_id']}.html"


def render_toc(data: dict, active_id: str | None = None, depth: int = 0) -> str:
    indexes = build_site_indexes(data)
    blocks = []
    for doc in data["documents"]:
        divs = indexes["divisions_by_doc"].get(doc["document_id"], [])
        if not divs:
            continue
        links = []
        for div in divs:
            level_class = f"toc-level-{min(int(div['level']), 4)}"
            active = " active" if div["division_id"] == active_id else ""
            links.append(f'<a class="toc-link {level_class}{active}" href="{division_href(div, depth)}">{esc(div["title"])}</a>')
        blocks.append(f'<div class="toc-group"><a class="toc-doc" href="{division_href(divs[0], depth)}">{esc(doc["title"])}</a>{"".join(links)}</div>')
    return "".join(blocks)


def paragraph_html(data: dict, div: dict) -> str:
    indexes = build_site_indexes(data)
    paragraphs = indexes["paragraphs_by_div"].get(div["division_id"], [])
    if not paragraphs:
        return '<p class="meta">此 division 無直接段落。</p>'
    return "".join(
        f'<p id="{para["paragraph_id"]}" data-paragraph-number="{para["paragraph_index"]}">{esc(para["text"])}</p>'
        for para in paragraphs
    )


def chapter_nav_html(prev_div: dict | None, next_div: dict | None, depth: int) -> str:
    return (
        '<nav class="chapter-nav">'
        + (f'<a class="prev" href="{division_href(prev_div, depth)}">上一節：{esc(prev_div["title"])}</a>' if prev_div else "<span></span>")
        + (f'<a class="next" href="{division_href(next_div, depth)}">下一節：{esc(next_div["title"])}</a>' if next_div else "<span></span>")
        + "</nav>"
    )


def resolve_theme(paths: BuildPaths) -> Path:
    project_theme = paths.root / "theme"
    if project_theme.exists():
        return project_theme
    return Path(__file__).resolve().parents[1] / "themes" / "default"


def theme_name(theme_path: Path) -> str:
    manifest = theme_path / "theme.json"
    if not manifest.exists():
        return theme_path.name
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return theme_path.name
    return str(data.get("name") or theme_path.name)


def build_template_env(theme_path: Path) -> Environment:
    return Environment(
        loader=FileSystemLoader(theme_path / "templates"),
        autoescape=select_autoescape(("html", "xml")),
    )


def copy_theme_static(theme_path: Path, paths: BuildPaths) -> None:
    static_dir = theme_path / "static"
    assets_dir = paths.site / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    if static_dir.exists():
        shutil.copytree(static_dir, assets_dir, dirs_exist_ok=True)


def base_context(collection: dict, active: str, depth: int, reader_view: bool = False) -> dict:
    prefix = relative_prefix(depth)
    return {
        "collection": collection,
        "brand_html": brand_html(collection["title"]),
        "description": collection.get("description") or collection["title"],
        "active": active,
        "body_class": "reader-view" if reader_view else "",
        "asset_prefix": f"{prefix}assets/",
        "routes": {
            "home": f"{prefix}index.html",
            "read": f"{prefix}read.html",
            "search": f"{prefix}search.html",
        },
    }


def render_template(env: Environment, template_name: str, output: Path, context: dict) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(env.get_template(template_name).render(**context), encoding="utf-8")


def render_home(env: Environment, paths: BuildPaths, data: dict) -> None:
    collection = data["collections"][0]
    counts = {key: len(data[key]) for key in ("documents", "divisions", "paragraphs", "sentences", "tokens")}
    context = {
        **base_context(collection, "home", depth=0),
        "page_title": collection["title"],
        "counts": counts,
    }
    render_template(env, "index.html", paths.site / "index.html", context)


def division_context(data: dict, collection: dict, div: dict, prev_div: dict | None, next_div: dict | None, depth: int) -> dict:
    return {
        **base_context(collection, "read", depth=depth, reader_view=True),
        "page_title": f"{div['title']} - {collection['title']}",
        "current_division": div,
        "toc_html": render_toc(data, div["division_id"], depth=depth),
        "paragraph_html": paragraph_html(data, div),
        "chapter_nav_html": chapter_nav_html(prev_div, next_div, depth=depth),
    }


def render_read_entry(env: Environment, paths: BuildPaths, data: dict) -> None:
    collection = data["collections"][0]
    divisions = data["divisions"]
    if not divisions:
        return
    first_div = divisions[0]
    next_div = divisions[1] if len(divisions) > 1 else None
    context = division_context(data, collection, first_div, None, next_div, depth=0)
    render_template(env, "read.html", paths.site / "read.html", context)


def render_division_pages(env: Environment, paths: BuildPaths, data: dict) -> None:
    collection = data["collections"][0]
    indexes = build_site_indexes(data)
    divisions = data["divisions"]
    div_pos = {div["division_id"]: idx for idx, div in enumerate(divisions)}
    read_dir = paths.site / "read"
    md_dir = paths.site / "md"
    read_dir.mkdir(parents=True, exist_ok=True)
    md_dir.mkdir(parents=True, exist_ok=True)

    for div in divisions:
        idx = div_pos[div["division_id"]]
        prev_div = divisions[idx - 1] if idx > 0 else None
        next_div = divisions[idx + 1] if idx < len(divisions) - 1 else None
        context = division_context(data, collection, div, prev_div, next_div, depth=1)
        render_template(env, "division.html", read_dir / f"{div['division_id']}.html", context)

        paragraphs = indexes["paragraphs_by_div"].get(div["division_id"], [])
        md_lines = [f"# {markdown_escape(div['title'])}", "", f"- division_id: {div['division_id']}", f"- path: {div['path']}", ""]
        md_lines.extend(para["text"] + "\n" for para in paragraphs)
        (md_dir / f"{div['division_id']}.md").write_text("\n".join(md_lines).strip() + "\n", encoding="utf-8")


def search_examples(reader_paragraphs: list[dict]) -> str:
    examples = []
    for para in reader_paragraphs:
        for token in re.findall(r"[\u4e00-\u9fff]{2,4}", para.get("text", "")):
            if token not in examples:
                examples.append(token)
            if len(examples) >= 7:
                break
        if len(examples) >= 7:
            break
    return "".join(f'<button type="button" class="search-example" data-search-example="{esc(item)}">{esc(item)}</button>' for item in examples)


def render_search(env: Environment, paths: BuildPaths, data: dict, reader_paragraphs: list[dict]) -> None:
    collection = data["collections"][0]
    context = {
        **base_context(collection, "search", depth=0),
        "page_title": f"{collection['title']} - 檢索",
        "search_examples_html": search_examples(reader_paragraphs),
    }
    render_template(env, "search.html", paths.site / "search.html", context)


def enrich_search_index(data: dict, reader_paragraphs: list[dict]) -> dict:
    divs = {div["division_id"]: div for div in data["divisions"]}
    paragraphs = []
    for para in reader_paragraphs:
        div = divs.get(para["division_id"], {})
        href = f"read/{para['division_id']}.html#{para['paragraph_id']}"
        paragraphs.append({**para, "href": href, "division_path": div.get("path", para.get("division_path", ""))})
    return {"paragraphs": paragraphs}


def build_static_site(paths: BuildPaths, data: dict, reader_paragraphs: list[dict]) -> None:
    clean_generated_site(paths)
    theme_path = resolve_theme(paths)
    env = build_template_env(theme_path)
    copy_theme_static(theme_path, paths)

    for name in ("collection.json", "documents.json", "divisions.json", "toc.json", "reader_index.json", "metadata.json"):
        shutil.copy2(paths.json / name, paths.site_data / name)
    write_json(paths.site_data / "search_index.json", enrich_search_index(data, reader_paragraphs))

    render_home(env, paths, data)
    render_read_entry(env, paths, data)
    render_division_pages(env, paths, data)
    render_search(env, paths, data, reader_paragraphs)
    write_stage_report(
        paths,
        "build_static_site",
        {
            "ok": True,
            "site": str(paths.site),
            "theme": theme_name(theme_path),
            "theme_path": str(theme_path),
            "routes": ["index.html", "read.html", "search.html"],
            "division_pages": len(data["divisions"]),
            "markdown_pages": len(data["divisions"]),
        },
    )


def clean_generated_site(paths: BuildPaths) -> None:
    for name in ("index.html", "read.html", "search.html", "reader.html", "browse.html", "metadata.html"):
        path = paths.site / name
        if path.exists():
            path.unlink()
    for name in ("assets", "data", "read", "md"):
        path = paths.site / name
        if path.exists():
            shutil.rmtree(path)
    paths.site_data.mkdir(parents=True, exist_ok=True)
