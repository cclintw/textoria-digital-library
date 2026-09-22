# Textoria Workflow Reference

This reference defines the allowed execution order for Textoria Digital Library v1. Use it for any task that runs more than one workflow step.

## Main Flow

```text
Text
 ↓
Classify Intent
 ↓
Resolve Project Archive Target
 ↓
Resolve Input
 ↓
Resolve Merge Order / Manual Structure Blockers
 ↓
Ensure Runtime
 ↓
Inspect Input
 ↓
UTF-8 Prepared Copy
 ↓
Extract Plain Text
 ↓
Merge Ordered Corpus if needed
 ↓
Structure Confidence Check
 ↓
Clean
 ↓
Structure
 ↓
Collection / Document / Division / Paragraph / Sentence / Token
 ↓
CSV + JSON Intermediates
 ↓
SQLite + FTS5
 ↓
Digital Library
 ├─ TOC
 ├─ Reader
 ├─ Full-text Search
 ├─ Metadata
 └─ Browse
 ↓
HTML / Static Site / EPUB
```

## Task Dependency Graph

Users may ask for any supported output before they know the required workflow order. Textoria must resolve the requested task, then run only the missing or stale prerequisite stages in this dependency graph.

Before resolving input files, resolve the target collection archive. In v1, a project may contain one or more Textoria collections. All collection archives must live under `textoria/collections/<collection_slug>/`, including the first and only collection in a project. If creating a new collection, ask the user to confirm the human-readable collection `name` first, defaulting to the source filename stem; then generate the system `slug` automatically. If exactly one collection exists, ambiguous Textoria requests continue that collection by default. If more than one collection exists and the request does not identify the target, ask which collection to use. If the user explicitly asks for a new collection, ask where its source folder/files are; if no source folder exists, create/use `textoria/collections/<collection_slug>/` as the new collection output root.

```text
inspect_input
 ↓
convert_encoding
 ↓
extract_plain_text
 ↓
prepare_text_stream
 ↓
clean_text
 ↓
structure_text
 ↓
export_intermediate_files
 ├─ build_sqlite
 │   └─ build_fulltext_search
 │       └─ build_static_site
 ├─ build_reader_page
 ├─ build_browse_page
 └─ build_epub
```

Rules:

- `build_epub` requires encoded, extracted, cleaned, structured, and exported Textoria data. It does not require SQLite or FTS unless the user also asks for database or search outputs.
- `build_static_site` for a full-text search platform requires SQLite and FTS. Reader-only or browse-only pages may be built from JSON, but `build_fulltext_archive` must still create SQLite and FTS.
- Rebuild tasks start from the highest valid prerequisite. For example, `rebuild_site` uses existing SQLite/JSON when they are fresh; `rebuild_database` uses existing CSV/JSON when they are fresh.
- If an upstream stage is stale or missing, rerun it and all downstream stages needed by the requested task.
- If all required outputs are fresh, do not rerun the workflow. Tell the user the requested Textoria output already exists and name the relevant file or directory.

## Freshness and Rebuild Policy

Each deterministic stage should write a stage report under:

```text
textoria/collections/<collection_slug>/logs/stages/<stage_name>.json
```

A stage is fresh when all of these are true:

- every declared output exists;
- input file hashes match the hashes stored in the stage report;
- relevant config hash matches the stage report;
- script version or script hash matches the stage report;
- upstream stage IDs match the stage report.

If a source text, cleaned text, structure config, candidate rule file, or script changes, mark that stage and its downstream outputs stale. Do not rerun unchanged upstream stages unless the user explicitly asks for a force rebuild.

```text
function run_requested_task(task, input_plan, config) {
    stages = call resolve_required_stages(task)

    for stage in stages {
        status = call check_stage_freshness(stage, input_plan, config)

        if status == "fresh" {
            continue
        }

        result = call run_stage(stage, input_plan, config)

        if result.needs_manual_structure_marking == true {
            return ask_manual_structure_marking(result)
        }

        if result.ok != true {
            return error(result)
        }
    }

    validation = call validate_requested_outputs(task, config)

    if validation.ok == true {
        return requested_outputs(task, config)
    }

    return error(validation)
}
```

## Structure Confidence Policy

Textoria should not stop final-output tasks merely because divisions were inferred automatically. If the user asks for a far-downstream output such as EPUB, SQLite, FTS, static site, or full archive, continue when Textoria has usable high-confidence or medium-confidence structure signals. After the build finishes, clearly tell the user that divisions were auto-detected and list the review/edit/rebuild files.

Stop before downstream output only when structure confidence is low enough that continuing would produce a misleading archive.

```text
function decide_structure_policy(structure_preview, requested_task, config) {
    if structure_preview.confidence == "high" {
        return "continue_and_report"
    }

    if structure_preview.confidence == "medium" and requested_task in FINAL_OUTPUT_TASKS {
        return "continue_and_report"
    }

    if structure_preview.confidence == "medium" {
        return "ask_review"
    }

    return "needs_structure_confirmation"
}
```

Confidence rules:

- `high`: explicit Markdown headings, HTML `h1`-`h6`, or CSV title fields provide a clear hierarchy.
- `medium`: repeated plain-text heading patterns are found, such as `卷上`, `卷一`, `第一卷`, `第一章`, `第一節`, `第十二回`, date headings, issue numbers, case numbers, or other consistent short-line markers.
- `low`: no reliable heading pattern exists, heading-like lines are inconsistent, or paragraph boundaries are unclear.

When confidence is `high` or `medium`, write:

```text
textoria/collections/<collection_slug>/intermediate/structure_preview.json
textoria/collections/<collection_slug>/intermediate/structure_preview.md
textoria/collections/<collection_slug>/intermediate/division_review.md
```

Then continue the requested final-output workflow. The final response must list the inferred divisions or a useful sample, state the confidence level and evidence, and tell the user they can edit the review files and run `restructure_text` or rebuild the requested output.

When confidence is `low`, stop before CSV, JSON, SQLite, FTS, site, EPUB, manifest, and registry outputs. Write the structure preview/review files first, then ask exactly one confirmation question.

If Textoria can see a plausible repeated candidate pattern that has not been confirmed, summarize it and ask the user to confirm:

```text
我目前無法可靠判斷這份文本的章節結構，但看到可能的章節標題：「第一回　...」、「第二回　...」。請確認是否以這類標題作為第一層 division。
```

After the user confirms the proposed structure rule, rerun the build with that rule enabled; for the bundled script this means passing `--confirm-inferred-structure`.

When a confirmed candidate heading combines a Chinese volume/chapter marker and title on one line, normalize the division title with one ideographic space after the marker. For example, `第十五回王鳳姐弄權鐵檻寺秦鯨卿得趣饅頭庵` becomes `第十五回　王鳳姐弄權鐵檻寺秦鯨卿得趣饅頭庵`.

If Textoria cannot see a plausible candidate pattern, ask the user for a rule or manual markings:

```text
我目前無法可靠判斷這份文本的章節結構。你可以提供章節切分規則嗎？或讓我先自行判斷並提出建議。
```

Manual markings use Markdown headings and paragraph breaks:

```markdown
# Document title
## Division level 1
### Division level 2
#### Division level 3

Paragraph one.

Paragraph two.
```

Use `#` for document-level titles and `##`, `###`, `####` for division levels. Blank lines mark paragraph boundaries.

## Independent Task Functions

Before calling these functions in a multi-step task, resolve the input plan according to [input-resolution.md](input-resolution.md).

```text
function inspect_input(file, config) {
    assert file.exists
    assert file.extension in SUPPORTED_INPUT_FORMATS

    encoding = call detect_encoding(file)
    format = call detect_format(file)
    text_sample = call read_safe_sample(file, encoding)

    report = {
        path,
        extension,
        format,
        encoding,
        byte_size,
        line_count,
        has_bom,
        readable
    }

    write report to raw/source_manifest.json
    return report
}
```

```text
function ensure_runtime(config) {
    runtime = call ensure_textoria_runtime(config)

    if runtime.status != "ready" {
        return runtime
    }

    return runtime
}
```

```text
function convert_encoding(file, inspection, workspace, config) {
    decode bytes using Textoria encoding rules:
        UTF-8 -> BIG5 -> SJIS -> GB2312 -> fallback BIG5
    replace invalid bytes or unsupported characters with visible markers
    normalize Unicode with NFKC by default
    normalize line endings to \n
    write UTF-8 without BOM to prepared/<stem>.utf8<normalized_extension>
    never overwrite the original source
    return prepared_file
}
```

```text
function extract_plain_text(prepared_file, format, workspace, config) {
    if format == "txt" {
        preserve text as-is except normalized newline handling
    }

    if format == "markdown" {
        preserve heading lines as structure hints
        remove or neutralize markdown control syntax only when needed for plain text
    }

    if format == "html" {
        remove script, style, nav, and hidden boilerplate when safely identifiable
        preserve h1-h6, p, li, blockquote, and table text as structure hints
    }

    if format == "csv" {
        require config.input.text_column
        optionally read config.input.title_column and metadata columns
    }

    write intermediate/plain_text.md
    write intermediate/extraction_report.json
    return plain_text_md
}
```

```text
function clean_text(plain_text_md, workspace, config) {
    apply config.cleaning.profile or "cc_text_cleaner"
    preserve Markdown heading structure for later division detection
    write clean/cleaned_text.md
    write clean/cleaning_report.json
    optionally write clean/cleaned_text.txt when config.cleaning.export_txt == true
    return cleaned_text_md
}
```

```text
function structure_text(cleaned_text, workspace, config) {
    detect or apply configured collection/document/division rules
    prefer Markdown heading levels in merged_text.md:
        # document title
        ## division level 1
        ### division level 2
        #### division level 3
    create divisions with parent_division_id, level, division_type, sort_order, and path
    split paragraphs on preserved blank-line boundaries
    optionally split sentences if config.structure.enable_sentences == true
    optionally split tokens if config.structure.enable_tokens == true
    assign stable IDs
    evaluate structure_confidence and evidence

    if structure_confidence == "low" and config.workflow.allow_low_confidence_structure != true {
        write intermediate/structure_preview.json
        write intermediate/structure_preview.md
        return needs_manual_structure_marking
    }

    write intermediate/collections.json
    write intermediate/documents.json
    write intermediate/divisions.json
    write intermediate/paragraphs.json
    write intermediate/sentences.json when enabled
    write intermediate/tokens.json when enabled
    write intermediate/division_review.md

    return structure
}
```

```text
function export_intermediate_files(structure, workspace, config) {
    write all required CSV files to csv/
    write all required JSON files to json/
    validate file contracts
    return {csv_files, json_files}
}
```

```text
function build_sqlite(csv_files, workspace, config) {
    create sqlite/library.sqlite
    create normalized archive tables
    import CSV records
    create indexes and foreign-key-like consistency checks
    return sqlite_path
}
```

```text
function build_fulltext_search(sqlite, json_files, workspace, config) {
    create SQLite FTS5 table over paragraph text by default
    optionally emit search/search_index.json for static frontend use
    run smoke-test queries
    return search_outputs
}
```

```text
function build_epub(json_files, workspace, config) {
    read collection, documents, divisions, paragraphs, and toc JSON
    generate XHTML files ordered by document, division, and paragraph order
    generate EPUB navigation from toc.json
    generate EPUB package metadata from collection and metadata JSON
    create epub/<collection_slug>.epub using EPUB zip rules
    write epub/epub_manifest.json
    return epub_outputs
}
```

```text
function summarize_outputs_with_structure_review(output, structure, workspace, config) {
    if a static site was generated:
        start or reuse a local static HTTP server for site/
        report the clickable URL, such as http://localhost:<port>/
    report generated output paths
    report all major generated artifacts with clickable file links:
        textoria/registry.json
        manifest.json
        config/textoria.yml
        raw/source_manifest.json
        prepared/<source>.utf8.<ext>
        clean/cleaned_text.md
        csv/*.csv
        json/*.json
        sqlite/library.sqlite
        search/search_index.json
        search/fts_config.json
        epub/<collection_slug>.epub
        epub/epub_manifest.json
        site/index.html
        site/read.html
        site/search.html
        site/data/*.json
        logs/*.json
    report important intermediate files:
        clean/cleaned_text.md
        intermediate/structure_preview.md
        intermediate/division_review.md
        json/divisions.json
        csv/divisions.csv
        json/paragraphs.json
        csv/paragraphs.csv
    report structure.confidence and structure.evidence
    list all inferred divisions when the list is short
    if divisions are many, list the first config.summary.max_divisions_to_show and point to division_review.md
    explain that the divisions were inferred automatically and can be edited/rebuilt
    add operation note:
        我已經建立一個網站，網址為 [http://localhost:<port>/](http://localhost:<port>/)。你可以用瀏覽器打開此網站；若電腦重新開機或網站停用時，可以下指令要求 Codex 重新啟用網站。
    return final_summary
}
```

```text
function build_static_site(sqlite, json_files, search, workspace, config) {
    resolve theme:
        use textoria/theme/ if present
        otherwise use themes/default/
    load templates:
        base.html
        partials/header.html
        partials/footer.html
        index.html
        read.html
        division.html
        search.html
    copy static assets:
        static/css/
        static/js/
    generate SEO-friendly top-level HTML routes:
        index.html
        read.html
        search.html
    generate one reading HTML page per top-level division:
        read/<top_level_division_id>.html
    render child divisions as anchored sections inside their top-level division page
    generate one Markdown file per top-level division:
        md/<top_level_division_id>.md
    copy required JSON to site/data/
    copy CSS and JS assets to site/assets/
    return site_path
}
```

```text
function validate_output(workspace, sqlite, site, config) {
    check required files exist
    check required CSV columns exist
    check IDs join across tables
    check SQLite tables and FTS tables exist
    run sample FTS query
    check static HTML pages exist and reference available assets
    check EPUB package files exist when EPUB was requested
    write logs/validation.json
    return validation
}
```

## Repair Loop

Use repair loops only for deterministic workflow problems such as missing generated files, invalid IDs, recoverable structure-rule ambiguity, or stale derived outputs. Do not use repair loops to invent unsupported functionality.

```text
function repair_from_validation(validation, config) {
    if validation.error == "missing_intermediate_file" {
        rerun the producer function for that file
    }

    if validation.error == "invalid_csv_schema" {
        fix exporter mapping, then rerun export_intermediate_files
    }

    if validation.error == "sqlite_import_failed" {
        rerun build_sqlite from validated CSV
    }

    if validation.error == "site_asset_missing" {
        rerun build_static_site
    }

    return repair_result
}
```
