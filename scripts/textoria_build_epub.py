#!/usr/bin/env python3
"""Textoria EPUB export stage."""

from __future__ import annotations

import html
import uuid
import zipfile

from textoria_common import BuildPaths, slugify, write_json, write_stage_report


def xhtml_page(title: str, body: str) -> str:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="zh-Hant">
<head>
  <meta charset="utf-8" />
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" type="text/css" href="../styles/textoria.css" />
</head>
<body>
{body}
</body>
</html>
"""


def build_epub(paths: BuildPaths, data: dict) -> dict:
    collection = data["collections"][0]
    title = collection["title"]
    slug = slugify(title)
    epub_path = paths.epub / f"{slug}.epub"
    identifier = f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, title)}"

    paragraphs_by_div: dict[str, list[dict]] = {}
    for para in data["paragraphs"]:
        paragraphs_by_div.setdefault(para["division_id"], []).append(para)

    content_files = []
    for index, div in enumerate(data["divisions"], start=1):
        filename = f"text/div-{index:04d}.xhtml"
        heading_level = min(int(div["level"]), 6)
        body = [f"<h{heading_level}>{html.escape(div['title'])}</h{heading_level}>"]
        body.extend(f"<p>{html.escape(para['text'])}</p>" for para in paragraphs_by_div.get(div["division_id"], []))
        content_files.append({"id": f"item-{index:04d}", "href": filename, "title": div["title"], "body": xhtml_page(div["title"], "\n".join(body))})

    nav_items = "\n".join(f'<li><a href="{item["href"]}">{html.escape(item["title"])}</a></li>' for item in content_files)
    nav = xhtml_page(title, f"<nav epub:type=\"toc\" id=\"toc\"><h1>{html.escape(title)}</h1><ol>{nav_items}</ol></nav>")
    manifest_items = "\n".join(
        f'<item id="{item["id"]}" href="{item["href"]}" media-type="application/xhtml+xml" />' for item in content_files
    )
    spine_items = "\n".join(f'<itemref idref="{item["id"]}" />' for item in content_files)
    opf = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="pub-id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="pub-id">{identifier}</dc:identifier>
    <dc:title>{html.escape(title)}</dc:title>
    <dc:language>zh-Hant</dc:language>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav" />
    <item id="css" href="styles/textoria.css" media-type="text/css" />
    {manifest_items}
  </manifest>
  <spine>
    {spine_items}
  </spine>
</package>
"""
    container = """<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml" />
  </rootfiles>
</container>
"""
    css = "body{font-family:serif;line-height:1.8;} h1,h2,h3,h4,h5,h6{line-height:1.4;} p{text-indent:2em;margin:0 0 .75em;}"

    with zipfile.ZipFile(epub_path, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", container)
        zf.writestr("OEBPS/content.opf", opf)
        zf.writestr("OEBPS/nav.xhtml", nav)
        zf.writestr("OEBPS/styles/textoria.css", css)
        for item in content_files:
            zf.writestr(f"OEBPS/{item['href']}", item["body"])

    manifest = {
        "epub": str(epub_path),
        "identifier": identifier,
        "title": title,
        "content_files": [item["href"] for item in content_files],
    }
    write_json(paths.epub / "epub_manifest.json", manifest)
    write_stage_report(paths, "build_epub", {"ok": True, **manifest})
    return manifest
