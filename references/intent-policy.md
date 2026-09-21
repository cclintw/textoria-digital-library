# Textoria Intent Policy

Use this reference when a user request is vague, broad, outside the formal Textoria pipeline, or asks to modify the skill itself.

## Ambiguous Requests

Ask for clarification when the user request could reasonably mean several Textoria formal pipeline tasks.

Examples:

- "處理這個文本" could mean inspect, clean, structure, or full archive.
- "整理一下" could mean clean or structure.
- "做成資料庫" could mean SQLite only or full archive site.
- "做電子書" could mean static reader pages or EPUB output.

Ask one concise question:

```text
你要執行哪一種 Textoria 正式流程：只檢查檔案、清理文本、結構化 document/division/paragraph、建立 SQLite/FTS、輸出 EPUB、生成靜態網站，還是執行完整流程？
```

## Missing Or Multiple Inputs

If the user gives a clear task but does not specify a file, resolve inputs according to the task mode.

- For independent file tasks such as inspection, encoding conversion, and cleaning, ask whether to process one file, selected files, or all supported files.
- For ordered corpus tasks such as structure, SQLite, FTS, EPUB, static site, or full archive, ask the user to confirm the target files and merge order. Do not ask whether each file is a document, division, paragraph, chapter, or section at this stage.

If multiple files need to be merged, tell the user that Textoria will create `textoria/intermediate/merged_text.md` for review before structure extraction continues.

## Clear Requests

Proceed without asking when the task and input are clear.

- "把 this.txt 轉成 UTF-8" -> `convert_encoding`
- "清理 this.md" -> `clean_text`
- "幫 this.html 建全文檢索網站" -> `build_fulltext_archive`
- "把 this.md 做成 EPUB" -> `build_epub`
- "從現有 CSV 重建資料庫" -> `rebuild_database`

Do not treat destructive requests as ordinary clear requests. For "刪除文獻集", "刪除資料庫", "刪除全部", "重頭做一次", or equivalent, route to `delete_collection_archive` and follow [delete-policy.md](delete-policy.md). Always require exact destructive confirmation before deleting generated Textoria data.

## Non-Pipeline Requests

Do not use the Textoria task list as a general refusal rule. If the user asks a normal question or unrelated task, answer normally and do not write Textoria files.

Examples that should be answered normally without invoking Textoria:

- Weather, dates, current events, or general factual questions.
- General Python, shell, HTML, CSS, or documentation questions.
- Historical background questions that do not ask Textoria to process files.
- Ordinary conversation, planning, or explanation.

Response pattern:

```text
<answer the user's question normally>
```

Do not create, edit, or delete `textoria/`, `.textoria/`, `SKILL.md`, `scripts/`, `references/`, or `themes/` for these requests.

## Adjacent Unsupported Textoria Features

Some requests are related to digital-humanities work but are not part of the Textoria v1 formal pipeline:

- PDF/DOCX/EPUB ingestion.
- Translation.
- Literary interpretation.
- Semantic annotation.
- Named entity enrichment.
- GIS maps.
- Social network analysis.
- Knowledge graph construction.
- Model training.
- Live hosted deployment.
- Custom plugin/app development beyond generating Textoria skill artifacts.

Do not write these results into canonical Textoria outputs. Explain the boundary and offer an experimental output only when useful:

```text
這不是 Textoria v1 正式 pipeline 的功能。我可以用一般 Codex 方式協助做一次性草稿，並輸出到 textoria/experiments/，但它不會覆蓋正式 CSV/JSON/SQLite/site，也不會參與預設 rebuild。是否要繼續？
```

If the user confirms, write to:

```text
textoria/experiments/<task-slug>/
```

or, when the result is a reusable non-core feature:

```text
textoria/extensions/<feature-slug>/
```

## Conflicting Custom Rules

If the user requests a Textoria task with rules that conflict with the default pipeline, do not silently change the skill or canonical schema.

Examples:

- "清理文本，但三個空白不要刪除。"
- "paragraphs.csv 多加一個 topic 欄位。"
- "把 divisions.csv 的欄位刪掉幾個。"

Use this pattern:

```text
這和 Textoria v1 的正式規則不同。我可以用專案 config 記錄為此專案的正式客製規則，或做一次性實驗輸出到 textoria/experiments/。我不會修改 skill 本體或 canonical schema，除非你明確要求修改 skill。你要使用哪一種？
```

Canonical schema rules:

- Extra data should go in `metadata_json`, the `metadata` table, or `textoria/extensions/<feature>/`.
- Missing required columns must stop formal rebuild until repaired or regenerated.
- Formal build steps must validate schema before reading edited intermediates.

## Skill Modification Requests

If the user asks to modify `SKILL.md`, `scripts/`, `references/`, `themes/default/`, the core schema, or deterministic pipeline behavior, warn before editing:

```text
你現在要求修改 Textoria skill 本身。這會改變此 skill 的原有設計、pipeline 行為、輸出格式或後續 rebuild 結果，也可能造成和原版 Textoria skill 不相容。如果只是一次性實驗，我建議輸出到 textoria/experiments/ 或建立 project config，不修改 skill 本體。請確認你是否仍要修改 skill 本身？
```

If the user confirms, treat the local skill as a fork/custom copy. Record the reason and changed files in `FORK_NOTES.md` or `textoria/logs/skill-fork.json`.
