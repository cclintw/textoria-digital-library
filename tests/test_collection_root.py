#!/usr/bin/env python3
"""Regression tests for Textoria collection archive root handling."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = REPO_ROOT / "scripts" / "textoria_build.py"
VALIDATE_SCRIPT = REPO_ROOT / "scripts" / "textoria_validate.py"


class CollectionRootWorkflowTest(unittest.TestCase):
    def test_full_build_defaults_to_collection_slug_root_and_validates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            source_dir = project_root / "sources"
            source_dir.mkdir()
            source = source_dir / "sample_archive.md"
            source.write_text(
                "\n".join(
                    [
                        "# Sample Archive",
                        "",
                        "## First Division",
                        "",
                        "This is the first paragraph for search.",
                        "",
                        "## Second Division",
                        "",
                        "This is another paragraph for SQLite and site output.",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            build = subprocess.run(
                [sys.executable, str(BUILD_SCRIPT), str(source), "--project-root", str(project_root), "--epub"],
                check=True,
                capture_output=True,
                text=True,
            )
            result = json.loads(build.stdout)

            collection_root = project_root / "textoria" / "collections" / "sample-archive"
            self.assertEqual(Path(result["output"]).resolve(), collection_root.resolve())
            self.assertTrue(collection_root.exists())
            self.assertFalse((project_root / "textoria" / "manifest.json").exists())
            self.assertFalse((project_root / "textoria" / "sqlite").exists())
            self.assertFalse((project_root / "textoria" / "site").exists())

            registry = json.loads((project_root / "textoria" / "registry.json").read_text(encoding="utf-8"))
            self.assertEqual(
                registry["collections"],
                [
                    {
                        "collection_id": "sample-archive",
                        "archive_id": "sample-archive",
                        "slug": "sample-archive",
                        "name": "sample_archive",
                        "title": "sample_archive",
                        "path": "textoria/collections/sample-archive",
                        "source_files": ["sources/sample_archive.md"],
                        "updated_at": registry["collections"][0]["updated_at"],
                    }
                ],
            )

            sqlite_path = collection_root / "sqlite" / "library.sqlite"
            self.assertTrue(sqlite_path.exists())
            with sqlite3.connect(sqlite_path) as con:
                collection_id, name, slug, title = con.execute("SELECT collection_id, name, slug, title FROM collections").fetchone()
                paragraph_count = con.execute("SELECT COUNT(*) FROM paragraphs_fts").fetchone()[0]
            self.assertEqual(collection_id, "sample-archive")
            self.assertEqual(name, "sample_archive")
            self.assertEqual(slug, "sample-archive")
            self.assertEqual(title, "sample_archive")
            self.assertGreaterEqual(paragraph_count, 2)

            self.assertTrue((collection_root / "site" / "index.html").exists())
            search_page = (collection_root / "site" / "search.html")
            self.assertTrue(search_page.exists())
            search_html = search_page.read_text(encoding="utf-8")
            self.assertIn("全文檢索", search_html)
            self.assertIn('placeholder="搜尋原文"', search_html)
            self.assertNotIn("實體擴展", search_html)
            self.assertNotIn("熱門查詢", search_html)
            self.assertTrue((collection_root / "search" / "search_index.json").exists())
            self.assertTrue((collection_root / "site" / "data" / "search_index.json").exists())
            generated_search_js = (collection_root / "site" / "assets" / "js" / "search.js").read_text(encoding="utf-8")
            site_search_index = json.loads((collection_root / "site" / "data" / "search_index.json").read_text(encoding="utf-8"))
            self.assertIn("function resultTitle", generated_search_js)
            self.assertIn("division_title", site_search_index["paragraphs"][0])
            self.assertNotIn("${esc(r.division_path)}", generated_search_js)
            self.assertNotIn("第 #", generated_search_js)
            self.assertIn("第 ${esc(r.paragraph_index || '')} 段", generated_search_js)
            self.assertTrue((collection_root / "epub" / "sample-archive.epub").exists())

            subprocess.run(
                [sys.executable, str(VALIDATE_SCRIPT), str(collection_root), "--epub"],
                check=True,
                capture_output=True,
                text=True,
            )

    def test_explicit_output_path_is_recorded_in_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            source = project_root / "override_source.md"
            source.write_text("# Override Source\n\n## Unit\n\nBody text.\n", encoding="utf-8")
            output = project_root / "custom-archives" / "chosen-root"

            subprocess.run(
                [
                    sys.executable,
                    str(BUILD_SCRIPT),
                    str(source),
                    "--project-root",
                    str(project_root),
                    "--output",
                    str(output),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            registry = json.loads((project_root / "textoria" / "registry.json").read_text(encoding="utf-8"))
            self.assertEqual(registry["collections"][0]["collection_id"], "override-source")
            self.assertEqual(registry["collections"][0]["archive_id"], "override-source")
            self.assertEqual(registry["collections"][0]["path"], "custom-archives/chosen-root")
            self.assertTrue((output / "sqlite" / "library.sqlite").exists())

    def test_collection_name_is_display_name_and_slug_is_system_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            source = project_root / "source.md"
            source.write_text("# Source\n\n## Unit\n\nBody text.\n", encoding="utf-8")

            build = subprocess.run(
                [
                    sys.executable,
                    str(BUILD_SCRIPT),
                    str(source),
                    "--project-root",
                    str(project_root),
                    "--collection-name",
                    "Red Chamber Archive",
                    "--epub",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            result = json.loads(build.stdout)
            collection_root = project_root / "textoria" / "collections" / "red-chamber-archive"

            self.assertEqual(result["collection_name"], "Red Chamber Archive")
            self.assertEqual(result["collection_slug"], "red-chamber-archive")
            self.assertEqual(Path(result["output"]).resolve(), collection_root.resolve())
            self.assertTrue((collection_root / "epub" / "red-chamber-archive.epub").exists())

            registry = json.loads((project_root / "textoria" / "registry.json").read_text(encoding="utf-8"))
            entry = registry["collections"][0]
            self.assertEqual(entry["collection_id"], "red-chamber-archive")
            self.assertEqual(entry["archive_id"], "red-chamber-archive")
            self.assertEqual(entry["slug"], "red-chamber-archive")
            self.assertEqual(entry["name"], "Red Chamber Archive")
            self.assertEqual(entry["title"], "Red Chamber Archive")

            site_index = (collection_root / "site" / "index.html").read_text(encoding="utf-8")
            epub_manifest = json.loads((collection_root / "epub" / "epub_manifest.json").read_text(encoding="utf-8"))
            self.assertIn("Red Chamber Archive", site_index)
            self.assertEqual(epub_manifest["title"], "Red Chamber Archive")

    def test_chinese_collection_name_generates_english_pinyin_slug_and_duplicate_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            first = project_root / "first.md"
            second = project_root / "second.md"
            first.write_text("# First\n\n## Unit\n\nBody text.\n", encoding="utf-8")
            second.write_text("# Second\n\n## Unit\n\nBody text.\n", encoding="utf-8")

            first_build = subprocess.run(
                [
                    sys.executable,
                    str(BUILD_SCRIPT),
                    str(first),
                    "--project-root",
                    str(project_root),
                    "--collection-name",
                    "紅樓夢 文獻集",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            second_build = subprocess.run(
                [
                    sys.executable,
                    str(BUILD_SCRIPT),
                    str(second),
                    "--project-root",
                    str(project_root),
                    "--collection-name",
                    "紅樓夢 文獻集",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            first_result = json.loads(first_build.stdout)
            second_result = json.loads(second_build.stdout)
            self.assertEqual(first_result["collection_slug"], "hong-lou-meng-wen-xian-ji")
            self.assertEqual(second_result["collection_slug"], "hong-lou-meng-wen-xian-ji-2")

            registry = json.loads((project_root / "textoria" / "registry.json").read_text(encoding="utf-8"))
            self.assertEqual([entry["slug"] for entry in registry["collections"]], ["hong-lou-meng-wen-xian-ji", "hong-lou-meng-wen-xian-ji-2"])
            self.assertTrue((project_root / "textoria" / "collections" / "hong-lou-meng-wen-xian-ji").exists())
            self.assertTrue((project_root / "textoria" / "collections" / "hong-lou-meng-wen-xian-ji-2").exists())

    def test_reader_pages_are_top_level_divisions_with_child_anchors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            source = project_root / "nested.md"
            source.write_text(
                "\n".join(
                    [
                        "# Nested",
                        "",
                        "## 第一章 台灣縣志",
                        "",
                        "### 第一節 風土",
                        "",
                        "風土正文。",
                        "",
                        "#### 一、氣候",
                        "",
                        "氣候正文。",
                        "",
                        "### 第二節 物產",
                        "",
                        "物產正文。",
                        "",
                        "## 第二章 續志",
                        "",
                        "### 第一節 沿革",
                        "",
                        "沿革正文。",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            subprocess.run(
                [
                    sys.executable,
                    str(BUILD_SCRIPT),
                    str(source),
                    "--project-root",
                    str(project_root),
                    "--collection-name",
                    "Nested Reader",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            collection_root = project_root / "textoria" / "collections" / "nested-reader"
            read_pages = sorted((collection_root / "site" / "read").glob("*.html"))
            self.assertEqual([path.name for path in read_pages], ["div-000001.html", "div-000005.html"])
            first_page = (collection_root / "site" / "read" / "div-000001.html").read_text(encoding="utf-8")
            generated_css = (collection_root / "site" / "assets" / "css" / "style.css").read_text(encoding="utf-8")
            generated_js = (collection_root / "site" / "assets" / "js" / "reader.js").read_text(encoding="utf-8")
            self.assertIn("第一章 台灣縣志", first_page)
            self.assertIn("第一節 風土", first_page)
            self.assertIn("風土正文。", first_page)
            self.assertIn('id="div-000002"', first_page)
            self.assertIn("一、氣候", first_page)
            self.assertFalse((collection_root / "site" / "read" / "div-000002.html").exists())
            self.assertIn(".toc-item-root{display:grid", generated_css)
            self.assertIn(".toc-item-child{display:block}", generated_css)
            self.assertIn(".toc-level-2{padding-left:1em}", generated_css)
            self.assertIn(".toc-level-3{padding-left:2em}", generated_css)
            self.assertIn('@media(max-width:910px)', generated_css)
            self.assertIn('<main class="view layout reader-left-collapsed reader-entering">', first_page)
            self.assertIn("window.matchMedia('(max-width: 910px)')", generated_js)
            self.assertIn("textoria.readerLeftCollapsed.session", generated_js)
            self.assertNotIn("window.localStorage", generated_js)
            self.assertIn("window.sessionStorage.setItem", generated_js)
            self.assertIn("if (!mobileQuery.matches)", generated_js)
            self.assertIn("document.querySelectorAll('.toc-link')", generated_js)
            self.assertIn('id="readerContent" class="content reader reader-slide-ready"', first_page)
            self.assertIn("reader-slide-active", generated_js)
            self.assertIn("reader-entering", generated_css)
            self.assertIn("classList.remove('reader-entering')", generated_js)
            self.assertIn("visibility:hidden", generated_css)
            self.assertIn("transition:transform .42s cubic-bezier(.2,.8,.2,1)", generated_css)
            self.assertIn("translateX(min(22vw,220px))", generated_css)
            self.assertNotIn("reader-page-exit-left", generated_js)
            self.assertNotIn("initReaderPageTransitions", generated_js)

            toc = json.loads((collection_root / "json" / "toc.json").read_text(encoding="utf-8"))["items"]
            hrefs = {item["id"]: item["href"] for item in toc}
            self.assertEqual(hrefs["div-000001"], "read/div-000001.html")
            self.assertEqual(hrefs["div-000002"], "read/div-000001.html#div-000002")
            self.assertEqual(first_page.count('class="toc-children" hidden'), 2)
            self.assertIn('<ul class="toc-children"><li class="toc-item toc-item-child"><a class="toc-link toc-level-3"', first_page)

            subprocess.run(
                [sys.executable, str(VALIDATE_SCRIPT), str(collection_root)],
                check=True,
                capture_output=True,
                text=True,
            )

    def test_low_confidence_candidate_headings_require_confirmation_before_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            source = project_root / "dream.txt"
            source.write_text(
                "\n".join(
                    [
                        "第一回　甄士隱夢幻識通靈　賈雨村風塵懷閨秀",
                        "此開卷第一回也。",
                        "",
                        "第二回　賈夫人仙逝揚州城　冷子興演說榮國府",
                        "詩云正文。",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            blocked = subprocess.run(
                [
                    sys.executable,
                    str(BUILD_SCRIPT),
                    str(source),
                    "--project-root",
                    str(project_root),
                    "--collection-name",
                    "紅樓夢通行本",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(blocked.returncode, 2)
            blocked_result = json.loads(blocked.stdout)
            collection_root = project_root / "textoria" / "collections" / "hong-lou-meng-tong-xing-ben"

            self.assertFalse(blocked_result["ok"])
            self.assertEqual(blocked_result["status"], "needs_structure_confirmation")
            self.assertEqual(blocked_result["candidate_heading_count"], 2)
            self.assertIn("第一回　甄士隱", blocked_result["candidate_heading_samples"][0])
            self.assertTrue((collection_root / "intermediate" / "structure_preview.md").exists())
            self.assertTrue((collection_root / "intermediate" / "division_review.md").exists())
            self.assertFalse((collection_root / "sqlite" / "library.sqlite").exists())
            self.assertFalse((collection_root / "site" / "index.html").exists())
            self.assertFalse((project_root / "textoria" / "registry.json").exists())

            confirmed = subprocess.run(
                [
                    sys.executable,
                    str(BUILD_SCRIPT),
                    str(source),
                    "--project-root",
                    str(project_root),
                    "--collection-name",
                    "紅樓夢通行本",
                    "--confirm-inferred-structure",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            confirmed_result = json.loads(confirmed.stdout)

            self.assertTrue(confirmed_result["ok"])
            self.assertEqual(confirmed_result["structure_confidence"], "medium")
            self.assertEqual(confirmed_result["division_count"], 2)
            self.assertIn("/第一回　甄士隱", confirmed_result["division_sample"][0])
            self.assertTrue((collection_root / "sqlite" / "library.sqlite").exists())
            self.assertTrue((collection_root / "site" / "index.html").exists())
            divisions = json.loads((collection_root / "json" / "divisions.json").read_text(encoding="utf-8"))["divisions"]
            self.assertEqual(divisions[0]["title"], "第一回　甄士隱夢幻識通靈賈雨村風塵懷閨秀")
            self.assertIn("第一回　甄士隱", (collection_root / "site" / "read" / "div-000001.html").read_text(encoding="utf-8"))
            registry = json.loads((project_root / "textoria" / "registry.json").read_text(encoding="utf-8"))
            self.assertEqual(registry["collections"][0]["slug"], "hong-lou-meng-tong-xing-ben")


if __name__ == "__main__":
    unittest.main()
