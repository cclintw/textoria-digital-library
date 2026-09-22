# Textoria Runtime and Dependency Setup

Use this reference before running any Textoria task that executes local scripts.

## Principle

Textoria should prepare its runtime during installation or explicit initialization when possible. Do not wait until the middle of a workflow to discover that Python or required packages are missing.

If everything required is already installed, proceed without asking. If anything must be installed, explain what is missing and request user approval before installing, creating a virtual environment, or modifying the local environment.

Ask only one user-facing question at a time. Runtime approval must not be combined with task confirmation, file selection, merge-order confirmation, or structure review.

## Required Runtime

- Python 3.10 or newer.
- Python `sqlite3` module with SQLite FTS5 enabled.
- Project-local Textoria virtual environment at `.textoria/venv/`.
- Required Python packages:
  - `charset-normalizer`
  - `beautifulsoup4`
  - `jinja2`
  - `markdown-it-py`
  - `pypinyin`

Optional packages are not installed unless the user enables a feature that needs them:

- `jieba`
- `opencc`
- `pytest`

## Runtime Check

Use this during installation or explicit initialization:

```text
function install_or_initialize_textoria(project_root, config) {
    runtime = call ensure_textoria_runtime(config)

    if runtime.status == "ready" {
        return {
            status: "ready",
            message: "Textoria runtime is ready."
        }
    }

    return ask_runtime_permission(runtime)
}
```

Use this during task execution only after intent, input file selection, merge order, and structure-review blockers have been resolved:

```text
function ensure_textoria_runtime(config) {
    python = call detect_python(">=3.10")

    if python.exists == false {
        installer = call detect_system_installer()

        if installer.exists == false {
            return ask_user_for_python_installation_path()
        }

        return ask_permission_to_install_python(installer)
    }

    sqlite = call check_sqlite_fts5(python)

    if sqlite.fts5 == false {
        return error("Python sqlite3 is available, but SQLite FTS5 is not enabled.")
    }

    venv = call ensure_venv("<project_root>/.textoria/venv", python)

    required_packages = [
        "charset-normalizer",
        "beautifulsoup4",
        "jinja2",
        "markdown-it-py",
        "pypinyin"
    ]

    missing = call check_packages(venv.python, required_packages)

    if missing.count > 0 {
        return ask_permission_to_install_packages(venv, missing)
    }

    return {
        status: "ready",
        python: venv.python,
        venv: venv.path
    }
}
```

If dependency installation is approved and succeeds as part of an already confirmed task, continue the original task automatically. Do not stop after installation unless the user only asked to install, initialize, or check the runtime.

## Permission Messages

When Python is missing:

```text
Textoria needs Python 3.10+ to run local text processing. I could not find a compatible python3. Do you want me to try installing Python with an available system package manager?
```

When packages are missing:

```text
The Textoria runtime is not ready yet. Before running this task, Textoria needs to install required dependencies into this project's Textoria virtual environment:

.textoria/venv/

Missing requirements:

<missing_requirements>

Do you want me to create/update .textoria/venv/ and install them?
```

Do not explain package purposes in the permission message unless the user asks what a package is for.

## Installation Rules

- Do not install Python without explicit user approval.
- Do not install packages without explicit user approval.
- Do not install packages into the system Python. Use `.textoria/venv/` in the current project.
- Do not ask for approval when Python, FTS5, venv, and packages are already ready.
- Record runtime checks in `.textoria/logs/runtime_check.json` when scripts are implemented.

## Package Manager Policy

Prefer project-local Textoria venv package installation:

```text
.textoria/venv/bin/python -m pip install charset-normalizer beautifulsoup4 jinja2 markdown-it-py pypinyin
```

System Python installation is platform-specific and should be conservative:

- macOS: if Homebrew exists, ask before using `brew install python`.
- Linux: ask before using `apt`, `dnf`, `yum`, `pacman`, or `brew`.
- Windows: ask before using `winget` or other package managers.

If no safe installer is detected, ask the user for a Python installation path or ask them to approve a specific installation method.
