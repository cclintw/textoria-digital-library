# Textoria Input Resolution

Use this reference before selecting or merging source files.

## Principle

First classify the user's task, then decide how source files should be handled. Do not choose or merge files before knowing whether the task is an independent file task or an ordered corpus task.

Textoria v1 allows one project root to contain one or more Textoria collection archives. A collection archive is one independent 文獻集資料庫 with its own intermediates, SQLite, site, EPUB, logs, and manifest.

Use `textoria/registry.json` to discover existing collections. Every collection archive must live under `textoria/collections/<collection_slug>/`; `textoria/` itself is reserved for project-level registry, shared theme, global settings, and collection indexes.

Each collection has a user-facing `name` and a system-generated `slug`. The `name` is shown in the site and EPUB. The `slug` is used for `collection_id`, `archive_id`, the folder name, EPUB filename, and registry lookup.

## Project Archive Target

Resolve which collection archive the request targets before resolving file order.

```text
function resolve_project_archive_target(user_request, project_root, candidate_files) {
    collections = call discover_textoria_collections(project_root)

    if collections.count == 0 {
        return {
            archive_action: "create_first_collection",
            archive_root: "textoria/collections/<collection_slug>/",
            needs_collection_name_confirmation: true,
            needs_file_resolution: true
        }
    }

    if call request_explicitly_asks_new_collection(user_request) == true {
        return {
            status: "needs_new_collection_setup",
            reason: "new_collection_requested",
            message: "請指定這個新文獻集的來源資料夾或來源檔案，並確認文獻集名稱。建議先建立一個資料夾放原始檔；若尚未建立，我可以使用 textoria/collections/<collection_slug>/ 作為此文獻集的輸出資料夾。"
        }
    }

    target = call detect_named_collection_in_request(user_request, collections)

    if target.exists == true {
        return {
            archive_action: "update_existing_collection",
            archive_root: target.path,
            needs_file_resolution: true
        }
    }

    if collections.count == 1 {
        collection = collections[0]
        return {
            archive_action: "continue_existing_collection",
            archive_root: collection.path,
            needs_file_resolution: true
        }
    }

    return {
        status: "needs_collection_selection",
        reason: "multiple_collections_found",
        collections: collections
    }
}
```

Default behavior:

- First Textoria run in a project: ask the user to confirm the collection `name`, defaulting to the source filename stem. Then generate the `slug` automatically and create the first collection archive under `textoria/collections/<collection_slug>/`.
- Later Textoria runs with exactly one existing collection: continue and rebuild that collection unless the user clearly says they want a new collection.
- Later Textoria runs with more than one existing collection: ask which collection to use unless the request identifies it.
- A newly mentioned source file is assumed to belong to the selected collection unless it appears clearly unrelated.
- If adding a file would remove previously recorded source files, warn and confirm before rebuilding.
- If the new file appears unrelated to the selected collection, ask before merging it into that collection.
- If the user explicitly asks for a new collection, ask where the source files are or whether to create/use a folder for that collection.

Name confirmation prompt for new collections:

```text
要建立新的 Textoria 文獻集。文獻集名稱使用「<source_filename_stem>」嗎？或請輸入文獻集名稱。
```

Slug generation:

- generate from the confirmed collection `name`;
- normalize Unicode with NFKC;
- convert Chinese characters to lowercase Hanyu Pinyin without tone marks;
- lowercase Latin letters;
- convert spaces and underscores to hyphens;
- remove punctuation except hyphens and word characters;
- collapse repeated hyphens and trim leading/trailing hyphens;
- if the slug already exists in `textoria/registry.json` for a different collection, follow WordPress-style suffixing: the original slug has no suffix, the first duplicate becomes `-2`, then `-3`, and so on.

Use these signals for "possibly unrelated":

- filename/title strongly differs from the existing collection name;
- opening headings indicate a different work or corpus;
- language/script differs substantially;
- source format or heading pattern is unlike existing source files;
- the selected collection's `manifest.json` names a specific collection and the new file clearly names another collection.

Ask:

```text
這個檔案看起來可能和目前選定的 Textoria 文獻集不同。你要把它併入這個文獻集並重建，還是建立新的文獻集？
```

Do not ask this for every new file. Ask only when the mismatch signal is strong enough that automatic continuation could surprise the user.

If multiple collections exist, ask:

```text
這個專案已有多個 Textoria 文獻集。請指定要處理哪一個文獻集，或說明要建立新的文獻集。
```

List each collection with title, path, and source-file summary when available.

## Task Input Modes

```text
function get_task_input_mode(task) {
    if task in [
        "inspect_input",
        "convert_encoding",
        "extract_plain_text",
        "clean_text",
        "reclean_text"
    ] {
        return "independent_files"
    }

    if task in [
        "structure_text",
        "export_intermediate_files",
        "build_sqlite",
        "build_fulltext_search",
        "build_reader_page",
        "build_browse_page",
        "build_static_site",
        "restructure_text",
        "rebuild_database",
        "rebuild_site",
        "validate_output",
        "build_fulltext_archive"
    ] {
        return "ordered_corpus"
    }

    return "unknown"
}
```

## Resolve Input Plan

```text
function resolve_input_plan(task, user_request, files, config) {
    mode = call get_task_input_mode(task)
    explicit_files = call detect_explicit_file_references(user_request, files)

    if explicit_files.count > 0 {
        candidates = explicit_files
    } else {
        candidates = call scan_supported_input_files(config.project_root)
    }

    candidates = call filter_supported_files(candidates, SUPPORTED_INPUT_FORMATS)

    if candidates.count == 0 {
        return {
            status: "needs_file_selection",
            reason: "no_supported_input_files"
        }
    }

    if mode == "independent_files" {
        return call resolve_independent_files(candidates, user_request, config)
    }

    if mode == "ordered_corpus" {
        return call resolve_ordered_corpus(candidates, user_request, config)
    }

    return {
        status: "error",
        reason: "unknown_task_input_mode"
    }
}
```

## Independent File Tasks

Independent tasks may process one file or multiple files separately. Do not merge files for these tasks unless the user explicitly asks to create a corpus.

```text
function resolve_independent_files(candidates, user_request, config) {
    if candidates.count == 1 and call user_implied_all_or_this(user_request) == true {
        return {
            status: "ready",
            input_mode: "independent_files",
            files: candidates
        }
    }

    if candidates.count == 1 {
        return {
            status: "needs_file_selection",
            reason: "confirm_single_file",
            candidates: candidates
        }
    }

    return {
        status: "needs_file_selection",
        reason: "choose_one_selected_or_all",
        candidates: candidates
    }
}
```

Ask:

```text
這個任務可以逐一處理檔案。我找到多個支援格式檔案，請指定要處理哪一個、哪些檔案，或確認要全部處理。
```

## Ordered Corpus Tasks

Ordered corpus tasks require a single text stream. If there are multiple source files, confirm their merge order before any structure detection. The merge step must not decide whether a source file is a document, division, paragraph, or other unit.

```text
function resolve_ordered_corpus(candidates, user_request, config) {
    if candidates.count == 1 {
        return {
            status: "ready",
            input_mode: "ordered_corpus",
            corpus_mode: "single_file",
            files: candidates,
            merge_required: false
        }
    }

    explicit_order = call detect_user_specified_order(user_request, candidates)

    if explicit_order.exists == true {
        return {
            status: "ready_to_merge",
            input_mode: "ordered_corpus",
            corpus_mode: "multi_file",
            files: explicit_order.files,
            merge_required: true,
            order_source: "user"
        }
    }

    proposed_order = call infer_merge_order(candidates, config)

    return {
        status: "needs_order_confirmation",
        input_mode: "ordered_corpus",
        corpus_mode: "multi_file",
        files: candidates,
        proposed_order: proposed_order.files,
        order_reason: proposed_order.reason,
        order_confidence: proposed_order.confidence
    }
}
```

Ask:

```text
這個任務需要先把多個文本合併成一個有順序的 corpus。我推測的合併順序如下，請確認是否正確；如果不正確，請回覆正確順序。
```

## Infer Merge Order

Use simple signals only. Never treat inferred order as final without user confirmation.

```text
function infer_merge_order(files, config) {
    if call filenames_have_numeric_prefixes(files) {
        return sort_by_natural_numeric_filename(files)
    }

    if call filenames_have_volume_or_chapter_markers(files) {
        return sort_by_detected_filename_markers(files)
    }

    openings = call read_file_openings(files, max_chars = 500)

    if call openings_have_ordered_headings(openings) {
        return sort_by_opening_heading_markers(files, openings)
    }

    return sort_by_natural_path(files)
}
```

Order signals:

- Explicit user order in the request.
- Numeric prefixes such as `001`, `02`, `10`.
- Chinese volume/chapter markers in filenames, such as `卷一`, `第一回`, `第十二章`.
- Opening headings in the first 500 characters.
- Natural path order as a last resort.

## Merge Review File

After the user confirms the order, merge into:

```text
textoria/collections/<collection_slug>/intermediate/merged_text.md
```

Also write:

```text
textoria/collections/<collection_slug>/intermediate/merge_manifest.json
```

The merged file should be human-reviewable Markdown. Insert lightweight source boundary comments or headings only when they help review and do not distort the source text.

```text
function merge_ordered_files(confirmed_files, workspace, config) {
    for each file in confirmed_files {
        inspection = call inspect_input(file, config)

        if inspection.extension not in SUPPORTED_INPUT_FORMATS {
            return unsupported_input_format(inspection.extension)
        }

        utf8 = call convert_encoding(file, inspection, workspace, config)
        plain = call extract_plain_text(utf8, inspection.format, workspace, config)
        append plain to merged buffer with a source boundary marker
    }

    write intermediate/merged_text.md
    write intermediate/merge_manifest.json

    return {
        review_file: "intermediate/merged_text.md",
        manifest: "intermediate/merge_manifest.json",
        structure_detection_required: true
    }
}
```

`merge_manifest.json` required keys:

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

## Structure Detection and Manual Review

Before continuing from merged text to final structure, propose a structure preview. Do not always stop for review. If the requested task is a final-output task, continue when the structure confidence is high or medium and report the inferred divisions at the end.

```text
function propose_structure(review_file, workspace, config) {
    headings = call detect_markdown_headings(review_file)
    evidence = []

    if headings.count == 0 {
        headings = call detect_plaintext_headings(review_file)
    }

    paragraphs = call detect_paragraph_boundaries(review_file)
    confidence = call evaluate_structure_confidence(headings, paragraphs)

    write intermediate/structure_preview.json
    write intermediate/structure_preview.md

    return {
        status: "structure_preview_ready",
        review_file: review_file,
        headings: headings,
        paragraphs: paragraphs,
        confidence: confidence,
        evidence: evidence,
        preview_files: [
            "intermediate/structure_preview.json",
            "intermediate/structure_preview.md"
        ]
    }
}
```

Use this decision rule:

```text
function handle_structure_preview(preview, requested_task, config) {
    if preview.confidence in ["high", "medium"] and requested_task in FINAL_OUTPUT_TASKS {
        return {
            status: "continue_and_report",
            preview: preview
        }
    }

    if preview.confidence == "high" {
        return {
            status: "continue_and_report",
            preview: preview
        }
    }

    if preview.confidence == "medium" and requested_task == "structure_text" {
        return {
            status: "ask_optional_review",
            preview: preview
        }
    }

    return {
        status: "needs_manual_structure_marking",
        preview: preview
    }
}
```

Low-confidence response when Textoria cannot see a plausible repeated candidate pattern:

```text
我已經完成編碼轉換與文本清理，但無法可靠判斷章節或段落結構，因此先暫停，不直接產生資料庫/網站/EPUB，避免輸出錯誤的目錄。

你可以選擇其中一種方式繼續：

1. 告訴我章節規則，例如「每一章都以 第X回 開頭」或「每個標題都是單獨一行」。
2. 讓我根據文本內容再嘗試判斷章節。
3. 打開清理後或合併後的檔案，用 Markdown 標題標示層級，最多四層，並用空行標示段落：

# 全書標題
## 第一層 division
### 第二層 division
#### 第三層 division

第一段文字。

第二段文字。

完成後請告訴我「重新結構化」或「繼續建立網站/EPUB」。
```

Final-output response after high/medium-confidence auto-structure must include:

- a clickable local website URL when `site/` was generated, such as `http://localhost:<port>/`;
- requested final output path, such as `textoria/collections/<collection_slug>/site/index.html` or `textoria/collections/<collection_slug>/epub/<collection_slug>.epub`;
- cleaned text path, usually `textoria/collections/<collection_slug>/clean/cleaned_text.md`;
- structure review files: `textoria/collections/<collection_slug>/intermediate/structure_preview.md`, `textoria/collections/<collection_slug>/intermediate/division_review.md`, `textoria/collections/<collection_slug>/json/divisions.json`, `textoria/collections/<collection_slug>/csv/divisions.csv`;
- all major generated artifacts, grouped by type: registry, manifest, config, raw/prepared/clean text, intermediate review files, CSV, JSON, SQLite, search index, EPUB, static site pages, and logs. Use clickable file links in the final response so the user can open files in the side panel.
- a short list of inferred divisions, or the first several divisions if the list is long;
- a clear note that divisions were inferred automatically and can be edited/rebuilt.
- an operation note in this form: `我已經建立一個網站，網址為 [http://localhost:<port>/](http://localhost:<port>/)。你可以用瀏覽器打開此網站；若電腦重新開機或網站停用時，可以下指令要求 Codex 重新啟用網站。`
