# AGENTS.md — pyLoDStorage Developer Guide

## Project Overview

`pyLoDStorage` is a Python library (requires ≥3.10) for working with **Lists of Dicts (LoD)** as a lightweight tabular data abstraction, with backends for SQLite, MySQL, SPARQL/RDF, YAML, JSON, and CSV. Build system: **hatchling**. Version is sourced from `lodstorage/__init__.py`.

---

## Build / Install Commands

```bash
# Standard editable install
pip install -e .

# Full install (including optional pylatexenc)
scripts/install
```

---

## Test Commands

The test framework is **Python `unittest`** (not pytest). All test classes inherit from `tests.basetest.Basetest`, which extends `unittest.TestCase`.

```bash
# Run the full test suite
python -m unittest discover

# Run a single test file
python -m unittest tests/test_sqlite3.py

# Run a single test class
python -m unittest tests.test_sqlite3.TestSQLDB

# Run a single test method
python -m unittest tests.test_sqlite3.TestSQLDB.testEntityInfo

# Run all tests with the 'green' runner (colored output, stop on first failure)
green tests -s 1

# Run a single file with green
green tests/test_sqlite3.py -s 1

# Run via the project test script (supports --green, --module, --tox flags)
scripts/test
scripts/test --green
```

No `conftest.py` — there are no pytest fixtures. Do not use pytest-specific features.

---

## Lint / Format Commands

```bash
# Format all source and test files (runs isort then black)
scripts/blackisort

# Manually: isort then black on a directory
isort lodstorage/*.py tests/*.py
black lodstorage/*.py tests/*.py
```

- **black** (88-char line length, default settings)
- **isort** (default settings, compatible with black)
- No mypy, flake8, pylint, or ruff configurations exist — do not add type-checking CI steps without discussion.

---

## Code Style Guidelines

### Imports

Order imports as three groups separated by blank lines (enforced by isort):
1. Standard library
2. Third-party packages
3. Local (`lodstorage.*` or `tests.*`)

```python
import os
import re
from typing import Any, Dict, List, Optional

import yaml
from tabulate import tabulate

from lodstorage.lod import LOD
```

Always use top-level imports. Inline (deferred) imports inside functions are only acceptable for **optional** dependencies not listed in `pyproject.toml` — i.e. libraries that may not be installed. Never use inline imports for standard library modules or packages declared in `[project.dependencies]`.

```python
# WRONG — pymysql is a declared dependency, inline import is needless
def get_backend():
    from lodstorage.mysql import MySqlQuery
    backend = MySqlQuery(...)
    return backend

# CORRECT
from lodstorage.mysql import MySqlQuery

def get_backend():
    backend = MySqlQuery(...)
    return backend
```

### Formatting

- Line length: **88 characters** (black default)
- Strings: black enforces double quotes
- Always run `scripts/blackisort` before committing

### Type Annotations

Newer code (2024+) uses full type annotations; older code uses docstring-only documentation. When adding new code:
- Annotate function signatures and return types
- Use `Optional[X]` for nullable values (not `X | None` for ≥3.10 — be consistent with the file)
- Use `List`, `Dict`, `Any` from `typing` (older style) or built-in generics `list[str]`, `dict[str, Any]` (newer style — match the file's existing style)
- `ClassVar` for class-level attributes in dataclasses

### Docstrings

Use **Google style** docstrings (configured in `mkdocs.yml` as `docstring_style: google`):

```python
def store(self, list_of_records: list, entity_info: "EntityInfo") -> None:
    """
    Store the given list of records based on the given entityInfo.

    Args:
        list_of_records: the list of dicts to be stored
        entity_info: the metadata used for storing
        execute_many: if True, insert is done with executemany

    Returns:
        None

    Raises:
        Exception: if the SQL execution fails
    """
```

File-level module docstrings follow the pattern:
```python
"""
Created on YYYY-MM-DD

@author: <name>
"""
```

### Naming Conventions

The codebase has two coexisting styles due to evolution over time:

| Element | Older style (pre-2024) | Newer style (2024+) |
|---|---|---|
| Methods | `camelCase` (`getFields`, `createTable`) | `snake_case` (`get_instance`, `of_yaml`) |
| Variables | `camelCase` (`listOfRecords`, `startTime`) | `snake_case` (`list_of_records`) |
| Classes | `CamelCase` (`SQLDB`, `LOD`, `EntityInfo`) | `CamelCase` (unchanged) |
| Constants | `ALL_CAPS` (`RAM = ":memory:"`) | `ALL_CAPS` (unchanged) |
| Dataclass fields | `snake_case` | `snake_case` |

**Rule**: Match the style of the file you are editing. New files should use `snake_case` for methods and variables per PEP 8. When a legacy camelCase public API must be preserved for backward compatibility, add a thin delegate:

```python
def applyFormat(self, ...):
    """legacy delegate"""
    self.apply_format(...)
```

### Test Helpers

**Never define module-level helper functions in test files.** All shared test setup and helper methods belong on the test class itself (or on `Basetest` if truly reusable across multiple test classes). Module-level functions bypass `setUp`/`tearDown`, cannot access `self`, and pollute the test module namespace.

```python
# WRONG — module-level helper
def make_endpoint():
    ep = Endpoint()
    ...
    return ep

# CORRECT — instance method on the test class
class TestFoo(Basetest):
    def make_endpoint(self):
        ep = Endpoint()
        ...
        return ep
```

### Return Statements

Always assign the result to a named variable before returning. Never return a bare expression.

```python
# WRONG
return SQLDB(dbname=url, debug=debug)

# CORRECT
backend = SQLDB(dbname=url, debug=debug)
return backend
```

### Error Handling

- Raise plain `Exception(f"descriptive message: {detail}")` — no custom exception hierarchy
- Use `ExceptionHandler.handle(msg, ex, debug=debug)` from `lodstorage.exception_handler` for non-fatal, log-only errors
- Log to `sys.stderr` via `self.logError(msg)` in database classes
- In tests, use `self.fail("There should be an exception")` when asserting an exception must occur

### Debug / Logging

- Classes accept a `debug: bool = False` constructor parameter, stored as `self.debug`
- Conditional output: `if self.debug: print(...)`
- Newer code uses the `logging` module; older code uses bare `print()` — match the file's existing approach
- Classes also accept `profile: bool = True` (handled by `Basetest` automatically in tests)

---

## Key Architectural Patterns

### `@lod_storable` Dataclass Decorator

The primary pattern for domain model classes. Provided by `pybasemkit` (`basemkit.yamlable`). Adds YAML load/save and dict round-trip to Python dataclasses:

```python
from basemkit.yamlable import lod_storable

@lod_storable
class Query:
    name: str = ""
    sparql: str = ""
    endpoint_name: Optional[str] = None
```

### `LOD` Static Utility Class

`lodstorage/lod.py` — static methods for manipulating lists of dicts: `getFields`, `getLookup`, `intersect`, `filterFields`, `handleListTypes`, `setNone`, etc. Use these before reaching for pandas.

### `SQLDB` + `EntityInfo`

`lodstorage/sql.py` — lightweight SQLite wrapper. `EntityInfo` introspects a sample dict to derive `CREATE TABLE` DDL. No ORM.

### `YamlPath` Configuration Resolution

`lodstorage/yaml_path.py` — resolves YAML data files by checking `sampledata/` in the package first, then `~/.pylodstorage/` for user overrides. Use this for any YAML-driven configuration.

### Singleton Pattern

```python
_instance: ClassVar[Optional["MyClass"]] = None

@classmethod
def get_instance(cls) -> "MyClass":
    if cls._instance is None:
        cls._instance = cls.of_yaml()
    return cls._instance
```

---

## Test Conventions

All tests must inherit from `Basetest`:

```python
from tests.basetest import Basetest

class TestMyFeature(Basetest):
    def setUp(self):
        Basetest.setUp(self, debug=False, profile=True)

    def testBasicBehavior(self):
        # test method names: prefer testCamelCase (legacy) or test_snake_case (new)
        result = my_function()
        self.assertEqual(expected, result)
```

- `self.debug` — set in `setUp`, use for conditional test output
- `self.profile` — controls profiler output in `tearDown`
- `Basetest.inPublicCI()` — returns `True` on Travis/GitHub Actions; skip slow/external tests there
- `Basetest.isUser("wf")` — skip tests that require a specific local user environment
- Test files: `tests/test_<module>.py` (lowercase)
- Test classes: `TestXxx` (CamelCase)
- Test methods: `testXxx` (camelCase preferred) or `test_xxx`

---

## YAML / Sample Data

- YAML data files live in `sampledata/` (endpoints, queries, prefixes, royals, etc.)
- User overrides go in `~/.pylodstorage/`
- Use `YamlPath` to resolve paths — never hardcode absolute paths

---

## Dependencies & Python Version

- **Requires Python ≥ 3.10**; CI tests on 3.10–3.13
- Key runtime deps: `rdflib`, `SPARQLWrapper`, `PyYAML`, `tabulate`, `jsonpickle`, `pybasemkit`, `orjson`, `requests`, `PyMySQL`, `ratelimit`, `matplotlib`
- Optional test dep: `green` (colored test runner)
- Add new dependencies to `[project.dependencies]` in `pyproject.toml`
