# Question 1 — What do the files created by `uv init` contain?

For this lab, `uv init` created the structure of an installable Python project named `mlops-lab-1`. The generated files define its configuration, select a Python version, provide a place for documentation, and include a small working program.

## 1. `pyproject.toml` — Project configuration

This is the project's main configuration file. It describes the package and tells Python tools how to build and install it. In this project, it contains three sections:

| Section | Contents and purpose |
| --- | --- |
| `[project]` | Stores metadata such as the project name, version (`0.1.0`), description, author information, and the documentation file (`README.md`). It also declares the supported Python versions and runtime dependencies. |
| `[project.scripts]` | Defines the command `mlops-lab-1` and maps it to `mlops_lab_1:main`, meaning the `main()` function in the `mlops_lab_1` package. |
| `[build-system]` | Selects `uv_build` as the build backend and specifies its required version range. The backend turns the source code into an installable Python package. |

Two entries in `[project]` are especially relevant:

- **`requires-python = ">=3.10"`** declares that the project supports Python 3.10 or later.
- **`dependencies = []`** means that no runtime dependencies have been declared yet. Running `uv add <package>` adds a dependency to this list.

The file records the project's requirements; it does not contain the installed packages themselves.

## 2. `.python-version` — Python version selection

This file contains a single line:

```text
3.10
```

It tells uv to select Python 3.10 for this project's environment. This differs from `requires-python`: the latter declares which Python versions the project supports, while `.python-version` selects the version used for local development. The value `3.10` selects a minor version, so it does **not** pin an exact patch release such as `3.10.12`.

## 3. `README.md` — Project documentation

This file is currently empty. It provides a place to explain the project's purpose, installation steps, and usage. The `readme = "README.md"` entry in `pyproject.toml` identifies it as the package's main description file.

## 4. `src/mlops_lab_1/__init__.py` — Python package source

This file identifies `mlops_lab_1` as a Python package and contains the initial program:

```python
def main() -> None:
    print("Hello from mlops-lab-1!")
```

The entry in `[project.scripts]` connects the command name to this function. From the project directory, running:

```sh
uv run mlops-lab-1
```

prepares the project environment and calls `main()`, which prints `Hello from mlops-lab-1!`.

## Files created later

The following are not present immediately after initialization. With normal settings, commands such as `uv sync`, `uv add`, or `uv run` create them as needed:

| File or directory | Purpose | Commit to Git? |
| --- | --- | --- |
| `uv.lock` | Records the resolved dependency versions, including indirect dependencies and platform-specific choices, so subsequent installs can use the same resolution. | Yes |
| `.venv/` | Holds the local virtual environment, including its Python executable, installed packages, and command scripts. It can be recreated from the project configuration and lockfile. | No — exclude it using `.gitignore`. |

The configuration, documentation, and source files should also be committed to Git. Together with `uv.lock`, they let collaborators recreate the project environment without copying `.venv/`.

Reference: [uv documentation — Project structure and files](https://docs.astral.sh/uv/concepts/projects/layout/).
