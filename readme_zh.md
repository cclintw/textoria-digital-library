# Textoria Digital Library Skill 中文版

Textoria Digital Library 是一個 Codex skill，用來把支援格式的文字來源建立成本機、可重建、可檢查的數位文獻庫。它會將 `.txt`、`.md`、`.html/.htm`、`.csv` 轉成標準 UTF-8 文字、可稽核的 CSV/JSON 中介檔、具備 FTS5 全文檢索的 SQLite 資料庫、靜態閱讀/檢索網站，也可以選擇輸出 EPUB。

Textoria 適用於通用文本資料：文章集、歷史文書、機構紀錄、教學材料、個人研究筆記、公版文本，或任何支援格式的純文字來源。

## 可以產生什麼

- 保留原始檔，並建立標準 UTF-8 工作副本。
- 清理後文字與清理報告。
- 結構化資料：文獻集、文件、division、段落、句子、tokens。
- 可檢查、可重用的 CSV 與 JSON 中介檔。
- `sqlite/library.sqlite` 全文檢索資料庫。
- 靜態 HTML 首頁、閱讀頁、瀏覽頁與檢索頁。
- 可選的 EPUB 離線閱讀檔。
- 每個文獻集自己的驗證紀錄與階段輸出。

## 支援輸入格式

Textoria v1 支援：

- `.txt`
- `.md`
- `.html`
- `.htm`
- `.csv`

這個版本不把 PDF、DOCX、EPUB、XLSX、JSON、XML、圖片、音訊、影片或壓縮檔當作來源格式。

## 專案結構

這個 repository 本身就是 skill root：

```text
SKILL.md
references/
scripts/
themes/
```

發布或安裝時，不要再外包一層 `textoria-digital-library/` 資料夾。

## 安裝方式

### 專案內安裝

建議多數專案使用。請在目標專案根目錄執行：

```bash
mkdir -p .agents/skills/textoria-digital-library && curl -L https://github.com/cclintw/textoria-digital-library/archive/refs/heads/main.tar.gz | tar -xz --strip-components=1 -C .agents/skills/textoria-digital-library
```

安裝後只會作用於目前專案：

```text
your-project/
`-- .agents/
    `-- skills/
        `-- textoria-digital-library/
```

### 全域安裝

如果希望所有專案都可以使用 Textoria，可以使用 Codex skill installer：

```text
install skill from https://github.com/cclintw/textoria-digital-library
```

如果你正在測試、客製化，或某個專案需要自己的文獻庫規則，建議使用專案內安裝。

## 執行環境

Textoria 使用專案本地的 Python 環境：

```text
.textoria/venv/
```

需求如下：

- Python 3.10 或更新版本
- 啟用 FTS5 的 SQLite
- `charset-normalizer`
- `beautifulsoup4`
- `jinja2`
- `markdown-it-py`
- `pypinyin`

檢查執行環境：

```bash
.textoria/venv/bin/python scripts/textoria_runtime_check.py
```

如果環境或套件尚未準備好，Textoria 應該先詢問，再建立 `.textoria/venv/` 或安裝套件。

## 建立文獻集

主要建置腳本接受一個支援格式的來源檔：

```bash
.textoria/venv/bin/python scripts/textoria_build.py sources/sample.md --project-root . --collection-name "Sample Collection"
```

同時輸出 EPUB：

```bash
.textoria/venv/bin/python scripts/textoria_build.py sources/sample.md --project-root . --collection-name "Sample Collection" --epub
```

如果來源是 CSV，可在需要時指定文字欄位：

```bash
.textoria/venv/bin/python scripts/textoria_build.py sources/articles.csv --project-root . --collection-name "Article Collection" --text-column body
```

如果 Textoria 找到可能的標題結構，但需要使用者確認，可以用下列選項重建：

```bash
.textoria/venv/bin/python scripts/textoria_build.py sources/sample.md --project-root . --collection-name "Sample Collection" --confirm-inferred-structure
```

## 輸出位置

Textoria 會把每個文獻集輸出到：

```text
textoria/collections/<collection_slug>/
```

專案層級的 registry 位於：

```text
textoria/registry.json
```

每個文獻集可能包含：

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

常用輸出檔包括：

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

## 驗證輸出

驗證一個文獻集：

```bash
.textoria/venv/bin/python scripts/textoria_validate.py textoria/collections/sample-collection
```

也要求驗證 EPUB：

```bash
.textoria/venv/bin/python scripts/textoria_validate.py textoria/collections/sample-collection --epub
```

## Codex 使用範例

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

## 主題系統

內建可編輯主題位於：

```text
themes/default/
```

內容包含：

```text
themes/default/theme.json
themes/default/templates/
themes/default/static/css/style.css
themes/default/static/js/
```

產生網站時，主題資源會複製到每個文獻集的 `site/assets/`。

專案可以用下列目錄覆蓋內建主題：

```text
textoria/theme/
|-- theme.json
|-- templates/
`-- static/
```

如果只修改主題檔，重新產生靜態網站即可。除非來源或中介資料有變，否則不需要重新執行編碼轉換、清理、結構化或 SQLite 建置。
