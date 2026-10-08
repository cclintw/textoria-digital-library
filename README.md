# Textoria Digital Library Skill

中文說明請見 [readme_zh.md](readme_zh.md).

Textoria Digital Library is a Codex skill for building local, rebuildable digital text archives from supported text sources. It converts `.txt`, `.md`, `.html/.htm`, and `.csv` inputs into normalized UTF-8 text, auditable CSV/JSON intermediates, a SQLite database with FTS5 full-text search, a static reading/search website, and optional EPUB output.

Textoria is designed for general corpora: article collections, historical documents, institutional records, teaching materials, personal research notes, public-domain texts, or any other supported plain-text source.

## What It Builds

- Canonical UTF-8 working copies while preserving original source files.
- Cleaned text with a cleaning report.
- Structured archive data: collections, documents, divisions, paragraphs, sentences, and tokens.
- CSV and JSON intermediate files for inspection and reuse.
- `sqlite/library.sqlite` with full-text search support.
- Static HTML pages for catalog, reading, browsing, and search.
- Optional EPUB files for offline reading.
- Validation logs and stage outputs under each collection archive.

## Supported Inputs

Textoria v1 accepts:

- `.txt`
- `.md`
- `.html`
- `.htm`
- `.csv`

PDF, DOCX, EPUB, XLSX, JSON, XML, images, audio, video, and archive files are not source formats in this version.

## Repository Layout

This repository is the skill root:

```text
SKILL.md
references/
scripts/
themes/
```

Do not wrap these files in another `textoria-digital-library/` folder when publishing or installing the skill.

## Install

### Project-Local Install

Recommended for most projects. Run this in the target project root:

```bash
mkdir -p .agents/skills/textoria-digital-library && curl -L https://github.com/cclintw/textoria-digital-library/archive/refs/heads/main.tar.gz | tar -xz --strip-components=1 -C .agents/skills/textoria-digital-library
```

This installs Textoria only for the current project:

```text
your-project/
`-- .agents/
    `-- skills/
        `-- textoria-digital-library/
```

### Global Install

Use Codex's skill installer if you want Textoria available in every project:

```text
install skill from https://github.com/cclintw/textoria-digital-library
```

Project-local installation is safer when testing, customizing, or working with project-specific archive rules.

## Runtime

Textoria uses a project-local Python environment:

```text
.textoria/venv/
```

Requirements:

- Python 3.10 or newer
- SQLite with FTS5 enabled
- `charset-normalizer`
- `beautifulsoup4`
- `jinja2`
- `markdown-it-py`
- `pypinyin`

Check the runtime:

```bash
.textoria/venv/bin/python scripts/textoria_runtime_check.py
```

If the environment or dependencies are missing, Textoria should ask before creating `.textoria/venv/` or installing packages.

## Build a Collection

The main build script accepts one supported source file:

```bash
.textoria/venv/bin/python scripts/textoria_build.py sources/sample.md --project-root . --collection-name "Sample Collection"
```

Add EPUB output:

```bash
.textoria/venv/bin/python scripts/textoria_build.py sources/sample.md --project-root . --collection-name "Sample Collection" --epub
```

For CSV input, specify the text column when needed:

```bash
.textoria/venv/bin/python scripts/textoria_build.py sources/articles.csv --project-root . --collection-name "Article Collection" --text-column body
```

If Textoria detects a plausible heading structure but needs confirmation, rebuild with:

```bash
.textoria/venv/bin/python scripts/textoria_build.py sources/sample.md --project-root . --collection-name "Sample Collection" --confirm-inferred-structure
```

## Output Layout

Textoria writes collection archives under:

```text
textoria/collections/<collection_slug>/
```

The project-level registry lives at:

```text
textoria/registry.json
```

Each collection archive may contain:

```text
textoria/collections/<collection_slug>/
|-- manifest.json
|-- config/textoria.yml
|-- raw/
|-- prepared/
|-- clean/
|-- intermediate/
|-- csv/
|-- json/
|-- sqlite/library.sqlite
|-- search/
|-- epub/
|-- site/
`-- logs/
```

Important generated files include:

```text
clean/cleaned_text.md
intermediate/structure_preview.md
intermediate/division_review.md
csv/divisions.csv
json/divisions.json
sqlite/library.sqlite
site/index.html
site/read.html
site/search.html
```

## Validate Output

Validate a collection archive:

```bash
.textoria/venv/bin/python scripts/textoria_validate.py textoria/collections/sample-collection
```

Require EPUB validation too:

```bash
.textoria/venv/bin/python scripts/textoria_validate.py textoria/collections/sample-collection --epub
```

## Example Prompts for Codex

```text
請把 sources/sample.md 做成全文檢索網站。
```

```text
請把 sources/articles.csv 清理、結構化，建立 SQLite + FTS，並輸出 EPUB。文字欄位是 body。
```

```text
我要建立一個新的文獻集，用 sources/corpus/ 裡的檔案建立全文檢索資料庫。
```

```text
請重新產生 article-collection 文獻集的靜態網站，不要重新清理原文。
```

```text
刪除 sample-collection 文獻集的 Textoria 產物，保留原始檔，讓我重頭建立。
```

## Theme

The bundled editable theme lives at:

```text
themes/default/
```

It contains:

```text
themes/default/theme.json
themes/default/templates/
themes/default/static/css/style.css
themes/default/static/js/
```

Generated websites copy theme assets into each collection's `site/assets/` directory.

Projects may override the bundled theme with:

```text
textoria/theme/
|-- theme.json
|-- templates/
`-- static/
```

When only theme files change, rebuild the static site. Encoding, cleaning, structuring, and SQLite do not need to be rerun unless their inputs changed.
