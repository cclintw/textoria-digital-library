---
name: textoria-digital-library
description: Build UTF-8 normalized, cleaned, structured, searchable Textoria digital archives from .txt, .md, .html/.htm, or .csv inputs, including SQLite FTS, EPUB, and static reading/search/browse pages. Use only for Textoria archive pipeline tasks; answer unrelated general questions normally without writing Textoria files.
metadata:
  short-description: Build searchable text archives
---

# Textoria Digital Library

Use this skill to inspect, normalize, clean, structure, index, validate, and publish plain-text digital archives. The workflow turns supported input files into auditable intermediate CSV/JSON files, a SQLite database with FTS, an EPUB reading file when requested, and a static digital library with table of contents, reader, search, metadata, and browse pages.

This skill protects the Textoria formal pipeline; it does not limit Codex's ordinary conversation or coding abilities. Before writing any Textoria files, classify the user's request. If it is a Textoria pipeline task, follow this skill. If it is a general question or unrelated task, answer normally and do not write into `textoria/`, `.textoria/`, this skill's files, or Textoria canonical intermediates.

## Supported Input Formats

Only accept these first-version input formats:

- `.txt`
- `.md`
- `.html`
- `.htm`
- `.csv`

If the input extension is not listed, stop and tell the user to provide one of the supported formats. Do not process PDF, DOCX, EPUB, XLSX, JSON, XML, images, audio, video, or archive files in this version.

Every task that reads a source file must start with `inspect_input(file, config)`. Always preserve the original source file and create a canonical UTF-8 working copy before cleaning or structuring text. Every task that executes local scripts must run the runtime check in [references/runtime.md](references/runtime.md), but only after the user-facing task and input choices are clear.

## Textoria Formal Pipeline Tasks

These tasks may write Textoria canonical outputs and use the deterministic scripts:

- `inspect_input`: check existence, extension, size, encoding, readable text, and basic format metadata.
- `convert_encoding`: create a canonical UTF-8 copy of a supported file.
- `extract_plain_text`: extract plain text from `.txt`, `.md`, `.html/.htm`, or `.csv`.
- `clean_text`: perform low-risk normalization and produce a cleaning report.
- `structure_text`: segment text into collection, document, flexible divisions, paragraphs, optional sentences, and optional tokens.
- `export_intermediate_files`: write the required CSV and JSON intermediate files.
- `build_sqlite`: create the SQLite archive database from intermediate files.
- `build_fulltext_search`: create SQLite FTS5 tables and optional static JSON search index.
- `build_reader_page`: generate static reader pages/assets from the archive data.
- `build_browse_page`: generate browse and table-of-contents pages/assets.
- `build_static_site`: generate the full static digital library site.
- `build_epub`: generate a portable EPUB reading file from structured Textoria data.
- `validate_output`: validate files, schemas, IDs, SQLite tables, FTS queries, and static pages.
- `reclean_text`: rerun cleaning from the prepared UTF-8 input using updated cleaning config.
- `restructure_text`: rerun structuring from cleaned text using updated structure config.
- `rebuild_database`: rebuild SQLite and FTS from existing valid intermediate files.
- `rebuild_site`: rebuild static site from existing valid SQLite/JSON outputs.
- `build_fulltext_archive`: run the complete workflow from input file to validated static archive.
- `delete_collection_archive`: after explicit destructive confirmation, delete one collection archive's generated Textoria data so it can be rebuilt from the original source files.

Features such as semantic annotation, interpretive annotation, translation, literary criticism, named-entity enrichment beyond structural archive metadata, GIS, SNA, knowledge graph construction, model training, or custom app/plugin development are not part of the Textoria v1 formal pipeline. Codex may still answer questions about them or perform one-off work when appropriate, but those results must not overwrite Textoria canonical outputs. Put one-off or unsupported adjacent outputs under `textoria/experiments/` or `textoria/extensions/` only after confirming with the user.

## Intent Handling

Map natural language to the closest Textoria formal pipeline task when the user is asking Textoria to process or build a text archive.

- If the user says "check this file", "what format is this", or "is this usable", run `inspect_input`.
- If the user says "convert to UTF-8" or "fix encoding", run `convert_encoding`.
- If the user says "clean this text", run `clean_text`.
- If the user says "structure", "split into divisions", "make paragraphs", "split into chapters", or "make a table of contents", run `structure_text` and `export_intermediate_files`.
- If the user says "database", "personal database", "SQLite", or "archive database", run `build_sqlite`, after preparing prerequisite intermediates if needed.
- If the user says "full-text search", "全文檢索", or "search page", run `build_fulltext_search` and generate the search page if requested.
- If the user says "reader", "閱讀器", "browse", "瀏覽頁", or "目錄", run the matching page task.
- If the user says "EPUB", "epub", "電子書", "電子書檔", "用 epub reader 打開", or "輸出 e-book", run `build_epub`.
- If the user says "website", "static site", "digital library", "全文檢索平台", "數位典藏", or "complete archive", run `build_fulltext_archive` unless they explicitly request a narrower task.
- If the user says "delete this collection", "remove this database", "刪除文獻集", "刪除資料庫", "刪除全部", "重頭做一次", or "清掉 Textoria 產物", run `delete_collection_archive` according to [references/delete-policy.md](references/delete-policy.md).

When the request could mean multiple Textoria tasks with different outputs, ask one concise clarification question listing only the likely Textoria choices. When a required input file is missing, ask for the file path instead of guessing. If the user asks an unrelated general question, answer directly without entering the Textoria workflow.

Ask only one user-facing question at a time. Do not combine task confirmation, file selection, merge-order confirmation, structure review, or dependency-installation approval in one message.

## Input Resolution

Resolve the user's intended task before resolving files. Textoria tasks use two input modes:

- `independent_files`: `inspect_input`, `convert_encoding`, `extract_plain_text`, `clean_text`, and `reclean_text`. These tasks can run on one file or several files independently. If multiple candidate files exist and the user did not specify which files to use, ask whether to process one file, selected files, or all supported files.
- `ordered_corpus`: `structure_text`, `export_intermediate_files`, `build_sqlite`, `build_fulltext_search`, `build_epub`, reader/browse/static-site tasks, rebuild tasks, validation, and `build_fulltext_archive`. These tasks require a single ordered text stream. If multiple candidate source files exist, confirm the merge order before structuring. Do not decide whether each file is a document, division, paragraph, or other unit during merge resolution; that belongs to `structure_text`.

For ordered multi-file tasks, infer a proposed merge order only as a convenience. Prefer explicit user order, then numeric filename order, then volume/chapter markers in filenames, then headings found near file openings, then natural path order. Always show the proposed order and ask the user to confirm or correct it before merging.

After confirmation, write a fixed review file:

```text
textoria/intermediate/merged_text.md
```

Tell the user they may open and edit this file before structuring. If the detected structure looks wrong, ask them to mark levels with Markdown headings up to four levels:

```markdown
# Document title
## Division level 1
### Division level 2
#### Division level 3
```

For final-output tasks such as SQLite, FTS, EPUB, static site, or `build_fulltext_archive`, do not stop for structure review when the structure confidence is high or medium. Continue to the requested output, then tell the user which divisions were inferred and which files can be edited before rebuilding. Stop for manual structure marking only when Textoria cannot infer usable divisions or paragraph boundaries. Read [references/input-resolution.md](references/input-resolution.md) before resolving multiple candidate files.

## Project Archive Policy

Textoria v1 supports one or more collection archives inside one project root. A "collection archive" means one independent Textoria 文獻集資料庫 with its own intermediates, SQLite, site, EPUB, logs, and manifest.

```text
one project root = one or more Textoria collection archives
```

For a simple project with only one collection, `textoria/` may be used as the collection archive root. For projects with multiple collections, use:

```text
textoria/collections/<collection_slug>/
```

`textoria/registry.json` records all collection archives in the project.

If no Textoria collection exists, treat the next Textoria build as first-time setup. If multiple supported files are found, ask whether to use all files, selected files, or a specific file; for ordered corpus tasks, confirm merge order.

If exactly one collection exists and the user asks a Textoria task without explicitly saying they want a new collection, continue that existing collection by default. A newly mentioned source file is treated as an update to the same collection unless it appears clearly unrelated.

If more than one collection exists and the user's request does not identify the target collection, ask which collection archive to use before reading or writing Textoria outputs.

Create a separate collection archive when:

- the user explicitly says "new collection", "new archive", "new database", "new folder", "新的文獻集", "新的資料庫", "新的全文檢索", "新的資料夾", "獨立資料庫", "不要併入", or equivalent;
- the user says they are testing or processing a different corpus/work in the same project;
- the user confirms that a file which appears unrelated should not be merged into the current collection.

When a separate collection is requested, first ask where its source files are or should live. Prefer this workflow:

```text
Ask the user to create a folder for that collection, put the raw source files there, then use that folder as the collection's source folder.
```

If the user has not created a folder but confirms this should be a new collection, create a collection output folder under `textoria/collections/<collection_slug>/` and put all intermediates, SQLite, site, EPUB, and logs there. Do not mix two independent collections in the same collection output folder.

## Required Workflow

Do not skip auditable intermediate outputs. SQLite and static pages must be built from validated CSV/JSON intermediates, not directly from the raw source.

```text
function handle_user_request(user_request, files, config) {
    intent = call classify_intent(user_request)

    if intent.kind == "general_or_unrelated" {
        return answer_normally_without_textoria_writes(intent)
    }

    if intent.kind == "adjacent_unsupported_textoria_feature" {
        return offer_experiment_or_extension_output(intent)
    }

    if intent.kind == "modify_textoria_skill" {
        return warn_and_confirm_skill_fork(intent)
    }

    if intent.task not in TEXTORIA_FORMAL_PIPELINE_TASKS {
        return answer_normally_without_textoria_writes(intent)
    }

    if intent.confidence < config.intent_confidence_threshold {
        return ask_for_confirmation(intent.candidates)
    }

    if call task_requires_input_file(intent.task) == true {
        input_plan = call resolve_input_plan(intent.task, user_request, files, config)

        if input_plan.status == "needs_file_selection" {
            return ask_for_input_file()
        }

        if input_plan.status == "needs_order_confirmation" {
            return ask_merge_order_confirmation(input_plan)
        }

        if input_plan.status == "needs_manual_structure_marking" {
            return ask_manual_structure_marking(input_plan)
        }
    }

    runtime = call ensure_textoria_runtime(config)

    if runtime.status != "ready" {
        return ask_runtime_permission(runtime)
    }

    return call dispatch_task(intent.task, input_plan, config)
}
```

```text
function install_or_initialize_textoria(project_root, config) {
    runtime = call ensure_textoria_runtime(config)

    if runtime.status == "ready" {
        return "Textoria runtime is ready."
    }

    return ask_runtime_permission(runtime)
}
```

```text
function build_fulltext_archive(input_plan, config) {
    workspace = call init_workspace(input_plan, config)

    prepared_input = call prepare_text_stream(input_plan, workspace, config)

    if prepared_input.manual_structure_required == true {
        structure_preview = call propose_structure(prepared_input.review_file, workspace, config)
        return ask_manual_structure_marking(structure_preview)
    }

    cleaned_text = call clean_text(prepared_input.text_file, workspace, config)
    structure = call structure_text(cleaned_text, workspace, config)

    csv_files = call export_csv(structure, workspace, config)
    json_files = call export_json(structure, workspace, config)

    sqlite = call build_sqlite(csv_files, workspace, config)
    search = call build_fulltext_search(sqlite, json_files, workspace, config)

    site = call build_static_site(sqlite, json_files, search, workspace, config)
    validation = call validate_output(workspace, sqlite, site, config)

    if validation.ok == true {
        return call summarize_outputs_with_structure_review(site, structure, workspace, config)
    }

    return error(validation)
}
```

```text
function build_epub_archive(input_plan, config) {
    workspace = call init_workspace(input_plan, config)

    prepared_input = call prepare_text_stream(input_plan, workspace, config)

    if prepared_input.manual_structure_required == true {
        structure_preview = call propose_structure(prepared_input.review_file, workspace, config)
        return ask_manual_structure_marking(structure_preview)
    }

    cleaned_text = call clean_text(prepared_input.text_file, workspace, config)
    structure = call structure_text(cleaned_text, workspace, config)

    csv_files = call export_csv(structure, workspace, config)
    json_files = call export_json(structure, workspace, config)

    epub = call build_epub(json_files, workspace, config)
    validation = call validate_output(workspace, epub, config)

    if validation.ok == true {
        return call summarize_outputs_with_structure_review(epub, structure, workspace, config)
    }

    return error(validation)
}
```

```text
function run_until_valid(file, config) {
    attempt = 0

    do {
        result = call build_fulltext_archive(file, config)
        validation = call validate_output(result.workspace, result.sqlite, result.site, config)

        if validation.ok == true {
            return result
        }

        call repair_from_validation(validation, config)
        attempt = attempt + 1
    } while attempt < config.max_repair_attempts

    return error(validation)
}
```

## Output Contract

Use the standard Textoria output layout unless the user explicitly provides another output directory.

V1 may have one or more collection archives per project root. `textoria/registry.json` records them. A single simple collection may use `textoria/` directly; multiple collections should use `textoria/collections/<collection_slug>/`.

```text
textoria/
|-- manifest.json
|-- config/
|   `-- textoria.yml
|-- raw/
|   |-- original/
|   `-- source_manifest.json
|-- prepared/
|-- clean/
|-- intermediate/
|-- csv/
|-- json/
|-- sqlite/
|-- search/
|-- epub/
|-- site/
|   |-- index.html
|   |-- read.html
|   |-- search.html
|   |-- assets/
|   |-- read/
|   |   `-- <division_id>.html
|   |-- md/
|   |   `-- <division_id>.md
|   `-- data/
`-- logs/
```

## Non-Pipeline And Custom Work

Do not treat the Textoria task list as a refusal rule for ordinary Codex work. Use this routing:

- General or unrelated questions: answer normally. Do not create, edit, or delete Textoria files.
- Adjacent but unsupported Textoria requests: explain that the feature is not part of the v1 formal pipeline. If the user wants a one-off result, ask before writing and use `textoria/experiments/<task>/` or `textoria/extensions/<feature>/`. Do not modify canonical files under `textoria/csv/`, `textoria/json/`, `textoria/sqlite/`, `textoria/site/`, or `textoria/epub/`.
- Custom rules that conflict with Textoria defaults: explain the conflict. For a project-specific persistent rule, write config under `textoria/config/`; for a one-off run, write outputs under `textoria/experiments/` or `textoria/custom/`. Do not change `SKILL.md`, `scripts/`, `references/`, or `themes/default/` unless the user explicitly asks to modify the skill itself.
- Modified intermediate schemas: never silently change canonical CSV/JSON schemas. Store extra fields in `metadata_json`, the `metadata` table, or an extension file. If required canonical columns are missing, stop the formal rebuild and ask the user to repair or regenerate the canonical file.

When the user explicitly asks to modify this skill, its scripts, references, schema, or default theme, warn first:

```text
You are asking to modify the Textoria skill itself. This can change the original pipeline behavior, output formats, rebuild compatibility, and future upgrade path. If this is only a one-off experiment, I recommend using textoria/experiments/ or project config instead. Please confirm that you want to fork/customize this skill.
```

If the user confirms, treat the project-local skill as a custom fork and record the change in `FORK_NOTES.md` or `textoria/logs/skill-fork.json`.

Read [references/runtime.md](references/runtime.md) before executing local scripts or installing dependencies. Read [references/text-cleaning.md](references/text-cleaning.md) before encoding conversion, extraction, or cleaning. Read [references/file-contracts.md](references/file-contracts.md) before creating or validating intermediate files. Read [references/schema.md](references/schema.md) before building SQLite or FTS. Read [references/workflow.md](references/workflow.md) before running a multi-step workflow. Read [references/theme-system.md](references/theme-system.md) before generating or modifying the static site theme. Read [references/package-choices.md](references/package-choices.md) before adding dependencies or scaffolding scripts.
Read [references/delete-policy.md](references/delete-policy.md) before deleting, resetting, or cleaning a Textoria collection archive.

## Text Structure Model

Use this stable TEI-inspired model for all structured outputs:

```text
collections -> documents -> divisions -> paragraphs -> sentences -> tokens
```

`collections` represent the文獻集 or archive project. `documents` represent the main bibliographic or archival units. `divisions` represent all variable middle levels using `parent_division_id`, `level`, `division_type`, and `path`. Do not emit fixed `books`, `chapters`, or `sections` tables. Paragraphs, sentences, and tokens are generic text units and may exist for any document type.

## Cleaning Rules

Textoria's internal clean-text output is Markdown:

```text
intermediate/plain_text.md
clean/cleaned_text.md
```

Use the `cc_text_cleaner` profile by default for Chinese historical text. It normalizes encoding to UTF-8, uses `NFKC`, removes control characters, replaces invalid characters with `■`, converts selected vertical punctuation to horizontal punctuation, converts prose half-width punctuation to full-width punctuation, preserves Markdown structure, and converts HTML headings/tables/images into Markdown. Use the `conservative` profile only when the user asks for minimal intervention.

Do not automatically remove notes, bracketed text, page numbers, headers, footers, or convert simplified/traditional Chinese unless the user enables a named rule in config. See [references/text-cleaning.md](references/text-cleaning.md) for the exact rules.

## Package Policy

Use Python 3.10+ in the project-local Textoria virtual environment at `.textoria/venv/`. Required packages are `charset-normalizer`, `beautifulsoup4`, `jinja2`, and `markdown-it-py`. User project outputs go in `textoria/`; project-local internal runtime state goes in `.textoria/`. If Python, SQLite FTS5, the venv, or required packages are missing, ask for user approval before installing or modifying the project environment. If they already exist, proceed without asking. Use SQLite FTS5 for search. Optional packages such as `jieba`, `opencc`, or `pypinyin` may be used only when the user enables a feature that needs them.

The generated archive should be static and portable by default. Do not require React, Vue, server-side frameworks, or hosted services for the first-version static site.
