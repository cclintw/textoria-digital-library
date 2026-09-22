# Textoria Skill Fork Notes

## 2026-09-22 - Collection archives always live under `textoria/collections/`

Textoria no longer writes a first or single collection directly into the project-level `textoria/` root.

- The default collection archive root is now `textoria/collections/<collection_slug>/`.
- The `textoria/` root is reserved for project-level files such as `registry.json`, shared theme files, global settings, collection indexes, experiments, and extensions.
- Collection-level generated outputs such as `manifest.json`, `csv/`, `json/`, `sqlite/`, `search/`, `epub/`, `site/`, and `logs/` must stay inside the collection archive root.
- New collections have a user-confirmed `name` and a system-generated `slug`. The generated site and EPUB display `name`; `collection_id`, `archive_id`, archive path, and EPUB filename use `slug`.
- `scripts/textoria_build.py` accepts `--collection-name`; non-interactive runs default it to the source filename stem. The slug is generated from the confirmed name with WordPress-post-name-style normalization and numeric suffixes for conflicts.
- Explicit `--output` is still allowed, but `textoria/registry.json` records the actual archive path and source files.

## 2026-09-22 - Low-confidence structure detection now requires confirmation

Textoria no longer continues to SQLite, search, site, EPUB, manifest, or registry outputs when division detection is low-confidence.

- Low-confidence structuring writes only cleaned text and structure review files under the collection archive root.
- If repeated candidate headings are visible, Textoria asks the user to confirm the proposed rule before continuing.
- For plain-text chapter headings such as `第一回　回目標題`, the bundled build script can stop with `status: needs_structure_confirmation`; after user confirmation, rerun with `--confirm-inferred-structure`.
- If no candidate rule is visible, Textoria asks the user for a chapter/division rule or manual Markdown structure markings.
