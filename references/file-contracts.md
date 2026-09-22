# Textoria File Contracts

This reference defines the required output layout, filenames, and fields for Textoria Digital Library v1.

Textoria v1 uses this stable intermediate model:

```text
collections -> documents -> divisions -> paragraphs -> sentences -> tokens
```

Do not emit `books.csv`, `chapters.csv`, or `sections.csv`. Use `divisions.csv` for all variable middle levels.

## Output Layout

Textoria v1 allows one or more collection archives per project root.

Project-level registry and shared files:

```text
textoria/
|-- registry.json
|-- theme/
|   |-- theme.json
|   |-- templates/
|   `-- static/
`-- collections/
    `-- <collection_slug>/
        `-- ...collection archive layout below...
```

Every collection archive, including the first or only collection in a project, must live under:

```text
textoria/collections/<collection_slug>/
```

The `textoria/` root is project-level space only. It may contain `registry.json`, shared theme files, global settings, collection indexes, experiments, and extensions. It must not contain a single collection's `manifest.json`, `raw/`, `prepared/`, `clean/`, `intermediate/`, `csv/`, `json/`, `sqlite/`, `search/`, `epub/`, `site/`, or `logs/` outputs.

Each collection archive uses this layout:

```text
<collection_archive_root>/
|-- manifest.json
|-- config/textoria.yml
|-- raw/original/<original_filename>
|-- raw/source_manifest.json
|-- prepared/<source_stem>.utf8.<ext>
|-- intermediate/plain_text.md
|-- intermediate/extraction_report.json
|-- intermediate/merged_text.md
|-- intermediate/merge_manifest.json
|-- intermediate/structure_preview.json
|-- intermediate/structure_preview.md
|-- intermediate/division_review.md
|-- intermediate/collections.json
|-- intermediate/documents.json
|-- intermediate/divisions.json
|-- intermediate/paragraphs.json
|-- intermediate/sentences.json
|-- intermediate/tokens.json
|-- clean/cleaned_text.md
|-- clean/cleaned_text.txt
|-- clean/cleaning_report.json
|-- csv/collections.csv
|-- csv/documents.csv
|-- csv/divisions.csv
|-- csv/paragraphs.csv
|-- csv/sentences.csv
|-- csv/tokens.csv
|-- csv/source_files.csv
|-- csv/metadata.csv
|-- json/collection.json
|-- json/documents.json
|-- json/divisions.json
|-- json/paragraphs.json
|-- json/toc.json
|-- json/reader_index.json
|-- json/metadata.json
|-- sqlite/library.sqlite
|-- search/fts_config.json
|-- search/search_index.json
|-- epub/<collection_slug>.epub
|-- epub/epub_manifest.json
|-- site/index.html
|-- site/read.html
|-- site/search.html
|-- site/assets/css/style.css
|-- site/assets/js/reader.js
|-- site/assets/js/search.js
|-- site/read/<top_level_division_id>.html
|-- site/md/<top_level_division_id>.md
|-- site/data/collection.json
|-- site/data/documents.json
|-- site/data/divisions.json
|-- site/data/toc.json
|-- site/data/reader_index.json
|-- site/data/metadata.json
|-- logs/build.log
|-- logs/validation.json
`-- logs/errors.json
```

`textoria/registry.json` records collection archives:

```json
{
  "collections": [
    {
      "collection_id": "bihai-jiyou",
      "archive_id": "bihai-jiyou",
      "slug": "bihai-jiyou",
      "name": "裨海紀遊",
      "title": "裨海紀遊",
      "path": "textoria/collections/bihai-jiyou",
      "source_files": ["sources/bihai/裨海紀遊.html"],
      "updated_at": "2026-09-21T00:00:00+00:00"
    }
  ]
}
```

`cleaned_text.txt` is optional and should be emitted only when the user asks for a plain-text export or `config.cleaning.export_txt == true`.

`sentences.json`, `sentences.csv`, `tokens.json`, and `tokens.csv` may be empty but should exist unless sentence or token segmentation is explicitly disabled.

`merged_text.md` and `merge_manifest.json` are required when an ordered corpus task uses multiple source files. They may be omitted for single-file tasks.

`structure_preview.json`, `structure_preview.md`, and `division_review.md` are required whenever `structure_text` runs. `division_review.md` is the human-readable review file for inferred divisions and should be easier to inspect than CSV or JSON.

`epub/<collection_slug>.epub` and `epub/epub_manifest.json` are required only when the user requests EPUB output. EPUB output is an export target; `.epub` is not a supported source input format in Textoria v1.

## IDs

IDs must be stable within one build and should be deterministic from source order when possible.

- `collection_id`: system-generated collection slug, such as `bihai-jiyou`
- `slug`: same stable system-generated slug as `collection_id`
- `name`: user-confirmed display name, such as `裨海紀遊`
- `document_id`: `doc-0001`
- `division_id`: `div-000001`
- `paragraph_id`: `p-0000001`
- `sentence_id`: `s-0000001`
- `token_id`: `tok-0000001`
- `source_file_id`: `src-0001`
- `metadata_id`: `meta-000001`

## CSV Schemas

### collections.csv

Required columns:

- `collection_id`
- `name`
- `slug`
- `title`
- `subtitle`
- `description`
- `collection_type`
- `language`
- `created_at`
- `updated_at`
- `metadata_json`

### documents.csv

Required columns:

- `document_id`
- `collection_id`
- `title`
- `document_type`
- `creator`
- `date`
- `publisher`
- `source`
- `identifier`
- `language`
- `rights`
- `source_file`
- `source_format`
- `source_encoding`
- `sort_key`
- `char_start`
- `char_end`
- `metadata_json`

### divisions.csv

Required columns:

- `division_id`
- `collection_id`
- `document_id`
- `parent_division_id`
- `level`
- `division_type`
- `title`
- `label`
- `n`
- `sort_order`
- `path`
- `char_start`
- `char_end`
- `metadata_json`

Rules:

- `parent_division_id` is empty only for top-level divisions.
- `level` starts at `1` for top-level divisions.
- `division_type` must describe meaning, not depth. Examples: `volume`, `chapter`, `section`, `date`, `issue`, `case`, `file`, `folder`, `heading`, `unknown`.
- `path` should be human-readable, such as `/卷下/地理` or `/1901年/1901-03-12`.

### paragraphs.csv

Required columns:

- `paragraph_id`
- `collection_id`
- `document_id`
- `division_id`
- `paragraph_index`
- `text`
- `char_start`
- `char_end`
- `source_file`
- `metadata_json`

Rules:

- `division_id` should point to the most specific containing division.
- If no explicit divisions exist, create one default division for the document and link paragraphs to it.

### sentences.csv

Required columns:

- `sentence_id`
- `collection_id`
- `document_id`
- `division_id`
- `paragraph_id`
- `sentence_index`
- `text`
- `char_start`
- `char_end`
- `metadata_json`

### tokens.csv

Required columns:

- `token_id`
- `collection_id`
- `document_id`
- `division_id`
- `paragraph_id`
- `sentence_id`
- `token_index`
- `text`
- `normalized_text`
- `char_start`
- `char_end`
- `token_type`
- `metadata_json`

### source_files.csv

Required columns:

- `source_file_id`
- `collection_id`
- `document_id`
- `original_path`
- `prepared_path`
- `extracted_text_path`
- `file_format`
- `detected_encoding`
- `byte_size`
- `line_count`
- `sha256`
- `sort_order`
- `metadata_json`

### metadata.csv

Required columns:

- `metadata_id`
- `subject_table`
- `subject_id`
- `key`
- `value`
- `scheme`
- `language`
- `source`

## JSON Contracts

### manifest.json

Required keys:

- `project_name`
- `textoria_version`
- `source_files`
- `created_at`
- `workflow`
- `outputs`

### source_manifest.json

Required keys:

- `source_file`
- `extension`
- `detected_format`
- `detected_encoding`
- `byte_size`
- `line_count`
- `has_bom`
- `readable`
- `warnings`

### cleaning_report.json

Required keys:

- `input_file`
- `output_file`
- `normalization`
- `rules_applied`
- `rules_skipped`
- `char_count_before`
- `char_count_after`
- `line_count_before`
- `line_count_after`
- `warnings`

### merge_manifest.json

Required keys:

- `corpus_mode`
- `confirmed_by_user`
- `order_source`
- `merge_order`
- `output_file`
- `warnings`

Each `merge_order` item should include:

- `order`
- `source_file`
- `detected_encoding`
- `prepared_file`
- `plain_text_file`

### structure_preview.json

Required keys:

- `review_file`
- `headings`
- `paragraph_count`
- `warnings`
- `needs_user_review`

Each heading item should include:

- `level`
- `text`
- `line_number`
- `char_start`
- `char_end`

### collection.json

Required keys:

- `collection`
- `counts`
- `documents`

### documents.json

Required keys:

- `documents`

### divisions.json

Required keys:

- `divisions`

Each division should include:

- `division_id`
- `document_id`
- `parent_division_id`
- `level`
- `division_type`
- `title`
- `sort_order`
- `path`

### paragraphs.json

Required keys:

- `paragraphs`

### toc.json

Required keys:

- `items`

Each item should include:

- `id`
- `type`
- `title`
- `parent_id`
- `level`
- `order`
- `path`
- `href`

### reader_index.json

Required keys:

- `paragraphs`

Each paragraph should include:

- `paragraph_id`
- `document_id`
- `division_id`
- `division_path`
- `paragraph_index`
- `text`

### metadata.json

Required keys:

- `collection`
- `documents`
- `source_files`
- `generated_at`
- `counts`

## Static Site Files

The static site must work without a backend server. Pages may use local JSON files in `site/data/`.

Static site HTML, CSS, and JavaScript must be generated from a theme/template system. See [theme-system.md](theme-system.md). Do not hard-code large HTML/CSS/JS strings inside Python scripts in the formal skill.

- `index.html`: landing/catalog view for the collection.
- `read.html`: browse entry page grouped by `documents`; each document is treated as a separate book-like unit.
- `read/<top_level_division_id>.html`: one reading page per top-level division. Child divisions render inside that page as anchored sections. Large corpora must not be rendered into one giant reader page.
- `md/<top_level_division_id>.md`: one Markdown export per top-level division, including its child divisions.
- `search.html`: full-text search interface; search results should link to `read/<top_level_division_id>.html#<paragraph_id>`.

The primary navigation must use real HTML pages for SEO:

```text
首頁 -> index.html
瀏覽 -> read.html
檢索 -> search.html
```

Do not implement the primary menu as client-side-only route switching in v1 static output.
