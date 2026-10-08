---
name: textoria-digital-library-zh
description: 從 .txt、.md、.html/.htm 或 .csv 輸入建立 Textoria 數位文獻集，包含 UTF-8 正規化、文本清理、結構化、SQLite FTS、EPUB，以及靜態閱讀、檢索、瀏覽頁面。只用於 Textoria archive pipeline 任務；不相關的一般問題照常回答，不寫入 Textoria 檔案。
metadata:
  short-description: 建立可全文檢索的文本 archive
---

# Textoria Digital Library 中文規格草稿

這份 `skill-zh.md` 是 `SKILL.md` 的繁體中文說明版，用來先檢視自然語言 prompt 與規則長什麼樣子，再決定哪些段落要改寫成偽函式或更正式的規格。實際執行仍以 `SKILL.md` 為主，除非之後明確把這份改成正式 skill。

使用這個 skill 來檢查、正規化、清理、結構化、索引、驗證與發布純文字數位文獻集。工作流程會把支援的輸入檔轉成可稽核的 CSV/JSON 中介檔、含全文檢索的 SQLite 資料庫、需要時產生 EPUB，並產生一個包含目錄、閱讀器、搜尋、metadata 與瀏覽頁的靜態數位文獻集網站。

這個 skill 保護 Textoria 的正式 pipeline；它不限制 Codex 一般對話或寫程式的能力。在寫入任何 Textoria 檔案前，先判斷使用者的請求。如果是 Textoria pipeline 任務，就遵守這個 skill。如果是一般問題或不相關任務，就正常回答，不要寫入 `textoria/`、`.textoria/`、這個 skill 的檔案，或 Textoria canonical intermediates。

## 支援的輸入格式

第一版只接受以下輸入格式：

- `.txt`
- `.md`
- `.html`
- `.htm`
- `.csv`

如果輸入副檔名不在清單中，停止並請使用者提供支援格式之一。這一版不要處理 PDF、DOCX、EPUB、XLSX、JSON、XML、圖片、音訊、影片或壓縮檔。

每一個讀取來源檔的任務都必須從 `inspect_input(file, config)` 開始。永遠保留原始來源檔，並且在清理或結構化文本前，先建立 canonical UTF-8 工作副本。每一個執行本機 script 的任務，都必須依照 [references/runtime.md](references/runtime.md) 執行 runtime check，但只在使用者面對的任務與輸入選擇已經清楚之後才執行。

## Textoria 正式 Pipeline 任務

以下任務可以寫入 Textoria canonical outputs，並使用 deterministic scripts：

- `inspect_input`：檢查檔案是否存在、副檔名、大小、編碼、可讀文字與基本格式 metadata。
- `convert_encoding`：建立支援檔案的 canonical UTF-8 副本。
- `extract_plain_text`：從 `.txt`、`.md`、`.html/.htm` 或 `.csv` 萃取純文字。
- `clean_text`：執行低風險正規化並產生 cleaning report。
- `structure_text`：把文本切分成 collection、document、彈性 divisions、paragraphs，以及可選的 sentences、tokens。
- `export_intermediate_files`：寫出必要的 CSV 與 JSON 中介檔。
- `build_sqlite`：從中介檔建立 SQLite archive database。
- `build_fulltext_search`：建立 SQLite FTS5 tables 與可選的靜態 JSON search index。
- `build_reader_page`：從 archive data 產生靜態閱讀頁與 assets。
- `build_browse_page`：產生瀏覽頁與目錄頁。
- `build_static_site`：產生完整靜態數位文獻集網站。
- `build_epub`：從結構化 Textoria data 產生 portable EPUB。
- `validate_output`：驗證檔案、schema、ID、SQLite tables、FTS queries 與靜態頁面。
- `reclean_text`：從 prepared UTF-8 input 依更新後的 cleaning config 重跑清理。
- `restructure_text`：從 cleaned text 依更新後的 structure config 重跑結構化。
- `rebuild_database`：從既有有效中介檔重建 SQLite 與 FTS。
- `rebuild_site`：從既有有效 SQLite/JSON outputs 重建靜態網站。
- `build_fulltext_archive`：從輸入檔到已驗證靜態 archive 的完整 workflow。
- `delete_collection_archive`：在明確 destructive confirmation 後，刪除某一個 collection archive 的 generated Textoria data，以便從原始來源檔重建。

語意標註、詮釋性標註、翻譯、文學評論、超出結構性 archive metadata 的命名實體 enrichment、GIS、SNA、知識圖譜、模型訓練，或自訂 app/plugin 開發，不屬於 Textoria v1 正式 pipeline。Codex 仍可回答這些問題，或在適當時做一次性工作，但這些結果不得覆寫 Textoria canonical outputs。一次性或相鄰但未支援的輸出，只能在使用者確認後放到 `textoria/experiments/` 或 `textoria/extensions/`。

## 意圖判斷

當使用者要求 Textoria 處理或建立文本 archive 時，將自然語言對應到最接近的 Textoria formal pipeline task。

- 使用者說「檢查這個檔案」、「這是什麼格式」、「能不能用」時，執行 `inspect_input`。
- 使用者說「轉成 UTF-8」或「修正編碼」時，執行 `convert_encoding`。
- 使用者說「清理文本」時，執行 `clean_text`。
- 使用者說「結構化」、「切 divisions」、「切段落」、「切章節」或「建立目錄」時，執行 `structure_text` 與 `export_intermediate_files`。
- 使用者說「資料庫」、「個人資料庫」、「SQLite」或「archive database」時，在必要時先準備 prerequisites，再執行 `build_sqlite`。
- 使用者說「full-text search」、「全文檢索」或「search page」時，執行 `build_fulltext_search`，並在需要時產生搜尋頁。
- 使用者說「reader」、「閱讀器」、「browse」、「瀏覽頁」或「目錄」時，執行對應頁面任務。
- 使用者說「EPUB」、「epub」、「電子書」、「電子書檔」、「用 epub reader 打開」或「輸出 e-book」時，執行 `build_epub`。
- 使用者說「website」、「static site」、「digital library」、「全文檢索平台」、「數位典藏」或「complete archive」時，執行 `build_fulltext_archive`，除非他明確要求更窄的任務。
- 使用者說「delete this collection」、「remove this database」、「刪除文獻集」、「刪除資料庫」、「刪除全部」、「重頭做一次」或「清掉 Textoria 產物」時，依 [references/delete-policy.md](references/delete-policy.md) 執行 `delete_collection_archive`。

當請求可能代表多個 Textoria 任務且輸出不同時，只問一個簡短澄清問題，列出最可能的 Textoria 選項。必要輸入檔缺失時，請使用者提供檔案路徑，不要猜。如果使用者問的是不相關的一般問題，直接回答，不進入 Textoria workflow。

一次只問一個 user-facing question。不要在同一則訊息中同時要求 task confirmation、file selection、merge-order confirmation、structure review 或 dependency-installation approval。

## 輸入解析

先解析使用者要做的任務，再解析檔案。Textoria 任務有兩種輸入模式：

- `independent_files`：`inspect_input`、`convert_encoding`、`extract_plain_text`、`clean_text` 與 `reclean_text`。這些任務可以在一個或多個檔案上獨立執行。如果有多個候選檔案而使用者未指定要用哪些檔案，詢問要處理單一檔案、選定檔案，或所有支援檔案。
- `ordered_corpus`：`structure_text`、`export_intermediate_files`、`build_sqlite`、`build_fulltext_search`、`build_epub`、reader/browse/static-site tasks、rebuild tasks、validation 與 `build_fulltext_archive`。這些任務需要單一有順序的 text stream。如果有多個候選來源檔，在結構化前確認合併順序。不要在 merge resolution 階段判斷每個檔案是 document、division、paragraph 或其他單位；這是 `structure_text` 的工作。

多檔 ordered task 可以推測一個合併順序，但只是方便使用者。優先使用使用者明確指定順序，其次是數字檔名順序、檔名中的卷/章標記、檔案開頭附近的 headings，最後才是自然路徑順序。永遠顯示 proposed order，並請使用者確認或修正後才合併。

確認後，寫入固定 review file：

```text
textoria/collections/<collection_slug>/intermediate/merged_text.md
```

告訴使用者可以先打開並編輯這個檔案，再進行結構化。如果偵測到的結構看起來不對，請他用最多四層 Markdown headings 標示層級：

```markdown
# Document title
## Division level 1
### Division level 2
#### Division level 3
```

對 SQLite、FTS、EPUB、static site 或 `build_fulltext_archive` 等 final-output tasks，當結構信心是 high 或 medium 時，不要停下來做 structure review。繼續產生使用者要求的輸出，然後告訴使用者推測了哪些 divisions，以及哪些檔案可在 rebuild 前編輯。當 Textoria 無法推測可用 divisions 或 paragraph boundaries 時，在 downstream outputs 前停止。如果 Textoria 看到 candidate heading patterns，但信心仍然 low，說明 proposed rule，並請使用者確認後再 rebuild。解析多候選檔案前，閱讀 [references/input-resolution.md](references/input-resolution.md)。

## Project Archive Policy

Textoria v1 支援在一個 project root 裡放一個或多個 collection archives。所謂「collection archive」是指一個獨立的 Textoria 文獻集資料庫，擁有自己的 intermediates、SQLite、site、EPUB、logs 與 manifest。

```text
one project root = one or more Textoria collection archives
```

每個 collection archive 都必須使用：

```text
textoria/collections/<collection_slug>/
```

`textoria/registry.json` 記錄專案中的所有 collection archives。`textoria/` 根目錄只保留給 project-level registry、shared theme files、global settings、collection indexes、experiments 與 extensions；不得放單一 collection 的 `manifest.json`、`csv/`、`json/`、`sqlite/`、`site/`、`search/`、`epub/` 或 `logs/` outputs。

每個 collection 有兩個 identity fields：

- `name`：給人看的 collection name，由使用者選擇或確認，顯示在產生的 site 與 EPUB。
- `slug`：系統產生的 WordPress post-name style identifier，用於 `collection_id`、`archive_id`、collection folder name、EPUB filename 與 registry lookup。

建立新的 collection archive 時，寫入輸出前必須先請使用者確認 collection `name`。使用來源檔名 stem 作為預設建議：

```text
要建立新的 Textoria 文獻集。文獻集名稱使用「<source_filename_stem>」嗎？或請輸入文獻集名稱。
```

使用者確認 `name` 後，自動從該名稱產生 `slug`：用 Unicode NFKC 正規化，中文轉成無聲調小寫漢語拼音，拉丁字母小寫，空白與底線轉 hyphen，移除標點，並合併重複 hyphens。如果 `textoria/registry.json` 中已有其他 collection 使用相同 slug，採用 WordPress-style suffixing：原始 slug 不加 suffix，第一個 duplicate 變 `-2`，然後 `-3`，依此類推。除非遇到不尋常衝突需要人工處理，否則不要要求使用者輸入 slug。

如果尚無任何 Textoria collection，把下一次 Textoria build 視為 first-time setup。如果找到多個支援檔，詢問要使用全部檔案、選定檔案或特定檔案；ordered corpus tasks 則確認 merge order。

如果剛好只有一個 collection，而使用者要求 Textoria 任務但沒有明確說要建立新 collection，預設繼續使用既有 collection。新提到的來源檔會被視為同一 collection 的更新，除非它明顯無關。

如果有多個 collection，而使用者請求沒有識別目標 collection，在讀寫 Textoria outputs 前先問要使用哪一個 collection archive。

以下情況要建立 separate collection archive：

- 使用者明確說 "new collection"、"new archive"、"new database"、"new folder"、"新的文獻集"、"新的資料庫"、"新的全文檢索"、"新的資料夾"、"獨立資料庫"、"不要併入" 或同義說法。
- 使用者說他正在測試或處理同一專案中的不同 corpus/work。
- 使用者確認某個看起來無關的檔案不應合併進目前 collection。

當使用者要求 separate collection 時，先問來源檔在哪裡或應該放在哪裡。偏好這個 workflow：

```text
請使用者為該 collection 建立一個資料夾，把 raw source files 放在那裡，然後使用該資料夾作為 collection source folder。
```

如果使用者尚未建立資料夾，但確認這應該是新 collection，就在 `textoria/collections/<collection_slug>/` 下建立 collection output folder，並把所有 intermediates、SQLite、site、EPUB 與 logs 放在那裡。不要把兩個獨立 collections 混在同一個 collection output folder。

## 必要 Workflow

不要跳過可稽核的 intermediate outputs。SQLite 與 static pages 必須從已驗證的 CSV/JSON intermediates 建立，不能直接從 raw source 建立。

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

        if input_plan.status == "needs_structure_confirmation" {
            return ask_structure_confirmation(input_plan)
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
        return "Textoria runtime 已就緒。"
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

    if structure.confidence == "low" {
        return ask_structure_confirmation_or_manual_rule(structure)
    }

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

    if structure.confidence == "low" {
        return ask_structure_confirmation_or_manual_rule(structure)
    }

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

## 輸出契約

除非使用者明確提供另一個 output directory，否則使用標準 Textoria output layout。

V1 每個 project root 可以有一個或多個 collection archives。`textoria/registry.json` 記錄它們。每個 collection archive，包括專案中的第一個、唯一一個 collection，都必須放在 `textoria/collections/<collection_slug>/`。

```text
textoria/
|-- registry.json
|-- theme/
|-- config/
`-- collections/
    `-- <collection_slug>/
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
        |   |   `-- <top_level_division_id>.html
        |   |-- md/
        |   |   `-- <top_level_division_id>.md
        |   `-- data/
        `-- logs/
```

## 非 Pipeline 與自訂工作

不要把 Textoria task list 當成一般 Codex 工作的拒絕規則。使用以下 routing：

- 一般或不相關問題：正常回答。不要建立、編輯或刪除 Textoria 檔案。
- 相鄰但 Textoria 尚未支援的請求：說明該功能不屬於 v1 正式 pipeline。如果使用者想要一次性結果，寫入前先詢問，並使用 `textoria/experiments/<task>/` 或 `textoria/extensions/<feature>/`。不要修改 `textoria/collections/<collection_slug>/csv/`、`textoria/collections/<collection_slug>/json/`、`textoria/collections/<collection_slug>/sqlite/`、`textoria/collections/<collection_slug>/site/` 或 `textoria/collections/<collection_slug>/epub/` 底下的 canonical files。
- 與 Textoria defaults 衝突的自訂規則：說明衝突。project-specific persistent rule 寫到 `textoria/config/`；one-off run 輸出到 `textoria/experiments/` 或 `textoria/custom/`。除非使用者明確要求修改 skill 本體，不要改 `SKILL.md`、`scripts/`、`references/` 或 `themes/default/`。
- 修改 intermediate schemas：絕不要默默修改 canonical CSV/JSON schemas。額外欄位放進 `metadata_json`、`metadata` table，或 extension file。如果缺少 required canonical columns，停止正式 rebuild，請使用者修復或重新產生 canonical file。

當使用者明確要求修改這個 skill、scripts、references、schema 或 default theme 時，先警告：

```text
你正在要求修改 Textoria skill 本體。這可能改變原始 pipeline 行為、輸出格式、rebuild 相容性，以及未來升級路徑。如果這只是一次性實驗，我建議改用 textoria/experiments/ 或 project config。請確認你要 fork/customize 這個 skill。
```

使用者確認後，把 project-local skill 視為 custom fork，並把變更記錄在 `FORK_NOTES.md` 或 `.textoria/logs/skill-fork.json`。

執行本機 scripts 或安裝 dependencies 前，閱讀 [references/runtime.md](references/runtime.md)。執行 encoding conversion、extraction 或 cleaning 前，閱讀 [references/text-cleaning.md](references/text-cleaning.md)。建立或驗證 intermediate files 前，閱讀 [references/file-contracts.md](references/file-contracts.md)。建立 SQLite 或 FTS 前，閱讀 [references/schema.md](references/schema.md)。執行 multi-step workflow 前，閱讀 [references/workflow.md](references/workflow.md)。產生或修改 static site theme 前，閱讀 [references/theme-system.md](references/theme-system.md)。新增 dependencies 或 scaffolding scripts 前，閱讀 [references/package-choices.md](references/package-choices.md)。刪除、reset 或清理 Textoria collection archive 前，閱讀 [references/delete-policy.md](references/delete-policy.md)。

## 文本結構模型

所有結構化輸出使用這個穩定、受 TEI 啟發的模型：

```text
collections -> documents -> divisions -> paragraphs -> sentences -> tokens
```

`collections` 代表文獻集或 archive project。`documents` 代表主要 bibliographic 或 archival units。`divisions` 代表所有可變中間層級，使用 `parent_division_id`、`level`、`division_type` 與 `path`。不要輸出固定的 `books`、`chapters` 或 `sections` tables。Paragraphs、sentences 與 tokens 是 generic text units，可存在於任何 document type。

## 文本清理規則

Textoria 的內部 clean-text output 是 Markdown：

```text
intermediate/plain_text.md
clean/cleaned_text.md
```

中文歷史文本預設使用 `cc_text_cleaner` profile。它會把編碼正規化成 UTF-8，使用 `NFKC`，移除控制字元，以 `■` 取代 invalid characters，把選定直排標點轉成橫排標點，把 prose half-width punctuation 轉成 full-width punctuation，保留 Markdown structure，並把 HTML headings/tables/images 轉成 Markdown。只有在使用者要求 minimal intervention 時，才使用 `conservative` profile。

不要自動移除 notes、bracketed text、page numbers、headers、footers，也不要自動轉換簡繁中文，除非使用者在 config 啟用具名規則。精確規則見 [references/text-cleaning.md](references/text-cleaning.md)。

## Package Policy

在 project-local Textoria virtual environment `.textoria/venv/` 中使用 Python 3.10+。必要 packages 是 `charset-normalizer`、`beautifulsoup4`、`jinja2`、`markdown-it-py` 與 `pypinyin`。使用者專案輸出放在 `textoria/`；project-local internal runtime state 放在 `.textoria/`。如果 Python、SQLite FTS5、venv 或必要 packages 缺失，安裝或修改 project environment 前先詢問使用者批准。如果它們已存在，就直接繼續。搜尋使用 SQLite FTS5。`jieba` 或 `opencc` 等 optional packages 只能在使用者啟用需要它們的功能時使用。

產生的 archive 預設應該是 static 且 portable。第一版靜態網站不要要求 React、Vue、server-side frameworks 或 hosted services。
