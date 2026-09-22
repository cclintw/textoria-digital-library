# Textoria Digital Library Skill

Textoria Digital Library is a Codex skill for building local, rebuildable digital text archives from plain-text sources. It converts supported Chinese historical-text inputs into cleaned text, structured CSV/JSON intermediates, SQLite + FTS full-text search, static reader/search pages, and optional EPUB output.

## What It Does

- Checks and converts source files to UTF-8.
- Extracts text from `.txt`, `.md`, `.html/.htm`, and `.csv`.
- Cleans and normalizes text with conservative, auditable rules.
- Structures text into collections, documents, divisions, paragraphs, sentences, and tokens.
- Exports CSV and JSON intermediate files.
- Builds a SQLite database with FTS5.
- Generates a static website with `index.html`, `read.html`, and `search.html`.
- Generates EPUB files when requested.
- Keeps deterministic scripts and editable theme templates inside the skill.

## Repository Layout

This repository is the skill root:

```text
SKILL.md
references/
scripts/
themes/
```

Do not wrap these files in another `textoria-digital-library/` folder when publishing the repo.

## Project-Local Install

Recommended. Run this in the target project root:

```bash
mkdir -p .agents/skills/textoria-digital-library && curl -L https://github.com/<your-account>/textoria-digital-library/archive/refs/heads/main.tar.gz | tar -xz --strip-components=1 -C .agents/skills/textoria-digital-library
```

Replace `<your-account>` with the GitHub account or organization that owns the repo.

This installs the skill only for the current project:

```text
your-project/
└─ .agents/
   └─ skills/
      └─ textoria-digital-library/
```

## Global Install

Codex's built-in skill installer installs into the user-level Codex skills directory:

```text
install skill from https://github.com/<your-account>/textoria-digital-library
```

Use global install only if you want Textoria available in every project. Project-local install is safer for testing and for project-specific workflows.

## Runtime

Textoria uses a project-local Python environment:

```text
.textoria/venv/
```

Required Python packages:

- `charset-normalizer`
- `beautifulsoup4`
- `jinja2`
- `markdown-it-py`
- `pypinyin`

The skill asks before creating the virtual environment or installing dependencies.

## Output

Textoria writes project outputs under:

```text
textoria/collections/<collection_slug>/
```

Every collection archive uses that path, including the first and only collection in a project. The `textoria/` root is reserved for project-level files such as `registry.json`, shared theme files, global settings, and collection indexes.

```text
textoria/collections/<collection_slug>/
```

When creating a new collection, Textoria asks the user to confirm the human-readable collection `name`, defaulting to the source filename stem. Textoria then generates a WordPress-post-name-style `slug` from that name. Chinese names are converted to lowercase Hanyu Pinyin without tone marks. Duplicate slugs follow WordPress suffixing: original, then `-2`, `-3`, and so on. The generated site and EPUB display the `name`; registry ids, archive paths, and EPUB filenames use the `slug`.

Each collection contains its own cleaned text, intermediates, CSV/JSON, SQLite database, static site, EPUB, and logs.

## Example Prompts

```text
請把 sources/test.txt 做成全文檢索網站。
```

```text
請把 sources/book.html 清理、結構化，建立 SQLite + FTS，並輸出 EPUB。
```

```text
我要新建一個文獻集，用 sources/red-chamber/ 裡的檔案建立全文檢索資料庫。
```

```text
刪除紅樓夢文獻集的 Textoria 產物，保留原始檔，讓我重頭做一次。
```

## Theme

The default editable theme is:

```text
themes/default/
```

It contains templates and unminified CSS/JS:

```text
themes/default/templates/
themes/default/static/css/style.css
themes/default/static/js/
```

Generated websites copy theme assets into each collection's `site/assets/`.
