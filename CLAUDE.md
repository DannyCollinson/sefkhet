# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Setup:** Install with `uv` (preferred) or `pip install -e .[dev]` into a virtual environment.

**Format:**
```sh
ruff format .
ruff check --select I --fix .
```

**Lint / type-check:**
```sh
ruff check --config pyproject.toml
pylint src/snaplog tests
mypy src/snaplog tests
pyright -p pyproject.toml src/snaplog tests
```

**Docstring check:**
```sh
pydoclint --style=google --skip-checking-short-docstrings=True src/snaplog tests
```

**Security scan:**
```sh
bandit -c pyproject.toml -r tests src/snaplog docsrc/source/demos
```

**Test (all):**
```sh
pytest
```

**Test (single file or test):**
```sh
pytest tests/test_functional.py
pytest tests/test_functional.py::TestClassName::test_method_name
```

Tests require 100% line and branch coverage before merging to `trunk`.

## Architecture

`snaplog` is a zero-dependency wrapper around Python's built-in `logging` module that provides three levels of interface, all exported from `src/snaplog/__init__.py`:

### Module layout (`src/snaplog/`)

| File | Purpose |
|---|---|
| `_typing.py` | All private type aliases and `TypedDict`s used across the package. Defines `NoDefault`/`_NoDefaultType` sentinel, `_FormatterSpec`, `_FilterSpec`, `_HandlerSpec`, `_LoggerSpec`, etc. |
| `_functional.py` | Functional-style factory functions: `get_formatter`, `get_filter`, `get_handler`, `get_logger`, and their `*_from_spec` variants that accept the union type specs. Also contains helpers like `add_handlers_to_logger`, `add_filters_to_target`, `_parse_log_level`, and the `LOG_LEVEL_STR_TO_INT` mapping (supports shorthand strings like `"d"`, `"i"`, `"w"`, `"e"`, `"c"`). |
| `_object_oriented.py` | `SnapLogger(logging.Logger)` — wraps an internal `logging.Logger` instance, delegates all standard `logging.Logger` methods to it, and re-syncs instance attributes after mutations via the `_update_logger_attributes_hook` decorator. |
| `_one_step.py` | Module-level `log()` and `configure_default_logger()` using a singleton `_default_logger` protected by a `threading.Lock`. |

### Key design patterns

- **`NoDefault` sentinel:** Used throughout to distinguish "caller did not pass this argument" from `None`, because `None` has specific meaning in the `logging` API (e.g., `name=None` means the root logger). Never use a plain default of `None` for optional arguments where `None` is a valid user-supplied value.

- **`*Spec` union types:** Each layer (`_FormatterSpec`, `_HandlerSpec`, `_LoggerSpec`) accepts a broad union of inputs (string, pre-built object, tuple with kwargs dict, `None`, etc.) and the `get_*_from_spec` functions dispatch on the type to call the underlying factory. This is the core flexibility mechanism.

- **Functional → OO → one-step layering:** `_object_oriented.py` calls functions from `_functional.py`; `_one_step.py` calls functions from `_functional.py`. There is no reverse dependency.

- **`SnapLogger` internal logger:** `SnapLogger.__init__` calls `super().__init__("root", level=0)` to satisfy `logging.Logger`, but immediately creates a real named `logging.Logger` stored as `self.logger`. All actual logging is delegated to `self.logger`.

### Test layout (`tests/`)

Mirrors `src/snaplog/`: `test_functional.py`, `test_object_oriented.py`, `test_one_step.py`. Use `conftest.py` for shared fixtures.

## Code style

- Max line length: **80 characters**; docstring lines: **72 characters**
- **Google-style docstrings** with type hints included in the docstring body
- All functions must be fully type-hinted; `mypy` and `pyright` run in strict mode
- LF line endings; two blank lines after imports
- Suppress unavoidable linter issues inline (`# noqa: X`, `# pylint: disable=X`, `# pyright: ignore[X]`) rather than file-wide

## Branching

`trunk` is the release branch (not `main`). Branch naming: `patch/<name>/<desc>`, `feature/<name>/<desc>`, or `major/<name>/v<N>`.
