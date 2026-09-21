# Textoria Package Choices

Use conservative dependencies. The first-version archive must be easy to run locally and suitable for GitHub installation.

## Required Runtime

- Python 3.10 or newer.
- SQLite with FTS5 enabled.
- Project-local Textoria virtual environment at `.textoria/venv/`.
- Required Python packages:
  - `charset-normalizer`
  - `beautifulsoup4`
  - `jinja2`
  - `markdown-it-py`

Run the checks in [runtime.md](runtime.md) before executing local scripts. If a required component is missing, ask the user for approval before installation. If all components are present, proceed without asking.

## Core Python Standard Library

Use these whenever possible:

- `argparse` for command-line interfaces.
- `csv` for CSV export/import.
- `datetime` for build timestamps.
- `html.parser` for basic HTML extraction when sufficient.
- `json` for JSON outputs.
- `logging` for build logs.
- `pathlib` for filesystem paths.
- `re` for rule-based structure detection.
- `shutil` for safe copying.
- `sqlite3` for database and FTS5.
- `unicodedata` for Unicode normalization.
- `zipfile` for EPUB package generation.

## Required Third-Party Packages

These are required for Textoria v1:

- `charset-normalizer`: encoding detection when standard-library decoding is insufficient.
- `beautifulsoup4`: robust HTML extraction.
- `jinja2`: static HTML templates.
- `markdown-it-py`: Markdown parsing when heading extraction is not enough.

Install them only inside the current project's `.textoria/venv/`; do not install into system Python.

## Optional Later Packages

Do not require these in the first-version core workflow:

- `jieba`: optional Chinese tokenization.
- `opencc`: optional simplified/traditional conversion.
- `pypinyin`: optional sort/search assistance.
- `pytest`: optional tests for scripts and workflow validation.

## Frontend Policy

Use static HTML, CSS, and JavaScript by default. Do not require a backend server. Do not introduce React, Vue, Svelte, Next.js, Vite, or server frameworks unless the user explicitly asks to build a separate application beyond Textoria v1 static output.

The static site may read JSON files from `site/data/` and may query a generated JSON search index. SQLite FTS remains the authoritative search database output.

## EPUB Policy

Generate EPUB with Python standard-library tools by default. Do not add an EPUB package dependency unless a later feature requires advanced EPUB editing.

Required EPUB package structure:

```text
epub/<collection_slug>.epub
```

Inside the EPUB archive:

```text
mimetype
META-INF/container.xml
OEBPS/content.opf
OEBPS/nav.xhtml
OEBPS/styles/textoria.css
OEBPS/text/*.xhtml
```

The `mimetype` file must be the first ZIP entry and must be stored without compression. XHTML content should be generated from Textoria JSON, ordered by document, division, and paragraph sort order.
