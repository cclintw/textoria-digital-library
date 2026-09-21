# Textoria Theme System

Textoria static-site output must use a theme/template system. Do not keep large HTML, CSS, or JavaScript strings embedded in Python stage scripts.

## Principle

`scripts/textoria_build_site.py` is a renderer and orchestrator only. It should:

- load templates from a theme directory;
- pass structured data into templates;
- copy CSS and JavaScript assets from the theme;
- write generated HTML/MD/JSON outputs.

It should not hard-code page layouts, large CSS blocks, or interactive JavaScript.

## Default Theme Layout

The default bundled theme lives inside the skill:

```text
themes/default/
|-- theme.json
|-- templates/
|   |-- base.html
|   |-- partials/
|   |   |-- header.html
|   |   `-- footer.html
|   |-- index.html
|   |-- read.html
|   |-- division.html
|   `-- search.html
`-- static/
    |-- css/
    |   `-- style.css
    `-- js/
        |-- reader.js
        `-- search.js
```

Users may override the bundled theme from their project:

```text
textoria/theme/
|-- theme.json
|-- templates/
`-- static/
```

If `textoria/theme/` exists, use it first. Otherwise use `themes/default/`.

## Template Responsibilities

- `base.html`: document shell, `<head>`, CSS/JS links, shared blocks.
- `partials/header.html`: brand, primary navigation, reader/sidebar controls.
- `partials/footer.html`: footer.
- `index.html`: home/catalog page.
- `read.html`: reading entry page. It should render the first division, not a catalog-only page.
- `division.html`: one page per division.
- `search.html`: full-text search page.

## Required Routes

The generated site must use real HTML files for SEO:

```text
site/index.html
site/read.html
site/search.html
site/read/<division_id>.html
site/md/<division_id>.md
```

The primary menu must link to:

```text
首頁 -> index.html
瀏覽 -> read.html
檢索 -> search.html
```

## Theme Data Contract

The renderer should pass these values to templates:

- `collection`
- `documents`
- `divisions`
- `paragraphs`
- `toc`
- `counts`
- `active`
- `page_title`
- `current_division`
- `previous_division`
- `next_division`
- `paragraphs_for_division`
- `site_prefix`
- `asset_prefix`
- `routes`

Templates should not read SQLite directly. They should use the JSON/CSV-derived data provided by the renderer.

## User Editing Rules

Users may edit:

- `textoria/theme/templates/*.html`
- `textoria/theme/templates/partials/*.html`
- `textoria/theme/static/css/*.css`
- `textoria/theme/static/js/*.js`

When those files change, rerun `build_static_site` or `rebuild_site`; do not rerun encoding, cleaning, structure, or SQLite unless their inputs changed.

## Future Theme Switching

Theme selection should be configurable:

```yaml
site:
  theme: default
  theme_path: textoria/theme
```

For v1, `default` is the only bundled theme, but the file layout must allow additional themes later.
