# Textoria Delete Policy

Use this reference when the user asks to delete, reset, clear, remove, or start over for a Textoria collection archive.

## Principle

Deletion is destructive. Textoria should not delete anything until the target collection is unambiguous and the user explicitly confirms the deletion after seeing what will be removed.

When the user says "刪除全部", "重頭做一次", or equivalent, interpret that as:

```text
delete all generated Textoria data for the selected collection archive,
but keep the original source files.
```

Do not automatically create backups. If the user wanted a backup, they are responsible for making one before confirming deletion.

## What To Keep

Always keep:

- original source files outside the collection archive;
- source files inside a declared source folder;
- project-local skill files under `.agents/skills/`;
- project runtime under `.textoria/`;
- project-level `textoria/theme/`;
- other collection archives;
- `textoria/registry.json`, except for removing the deleted collection's entry.

If original source files were copied under a collection archive's `raw/original/`, preserve them only when there is no known external source copy. Prefer moving them to a safe source folder inside the project before deleting generated outputs, after telling the user where they will remain.

## What To Delete

For a collection archive under:

```text
textoria/collections/<collection_slug>/
```

delete that whole collection folder after confirmation, unless it contains the only known copy of original source files. Then update `textoria/registry.json`.

For a simple single-collection archive directly under:

```text
textoria/
```

do not delete the whole `textoria/` directory. Delete only generated collection files and folders:

```text
textoria/manifest.json
textoria/config/
textoria/raw/
textoria/prepared/
textoria/clean/
textoria/intermediate/
textoria/csv/
textoria/json/
textoria/sqlite/
textoria/search/
textoria/epub/
textoria/site/
textoria/logs/
```

Keep:

```text
textoria/registry.json
textoria/theme/
textoria/collections/
```

Then remove the deleted collection entry from `textoria/registry.json`.

## Required Confirmation

Before deletion, show:

- collection title;
- collection path;
- source files that will be kept;
- generated folders/files that will be deleted;
- statement that Textoria will not create an automatic backup.

Ask the user to confirm with an exact phrase:

```text
刪除 <collection_path>
```

Do not proceed on vague replies such as "好", "yes", or "刪吧".

## Pseudocode

```text
function delete_collection_archive(request, project_root) {
    collections = call discover_textoria_collections(project_root)
    target = call resolve_target_collection(request, collections)

    if target.count == 0 {
        return ask_user_to_choose_collection(collections)
    }

    if target.count > 1 {
        return ask_user_to_choose_exact_collection(target)
    }

    deletion_plan = call plan_collection_deletion(target[0])

    return ask_exact_destructive_confirmation(
        deletion_plan,
        required_reply = "刪除 " + deletion_plan.collection_path
    )
}

function execute_confirmed_delete_collection(deletion_plan) {
    assert user_reply == "刪除 " + deletion_plan.collection_path

    if deletion_plan.collection_path matches "textoria/collections/<slug>" {
        delete directory deletion_plan.collection_path
    } else if deletion_plan.collection_path == "textoria" {
        delete only generated simple-collection paths
    } else {
        stop("collection path does not match Textoria safe-delete rules")
    }

    update textoria/registry.json
    return "deleted"
}
```

## Safety Rules

- Never delete the project root.
- Never delete `.agents/skills/`.
- Never delete `.textoria/`.
- Never delete `textoria/theme/`.
- Never delete another collection archive.
- Never delete source files unless the user separately and explicitly asks to delete source files too.
- Never use a broad or ambiguous deletion path.
