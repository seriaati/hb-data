# GEMINI.md

This file provides project-specific guidance and architectural context for Gemini CLI when working in this repository.

## Project Overview

**hb-data** is a Python 3.12+ package designed to fetch, deobfuscate, and parse game data from HoyoVerse titles (Genshin Impact, Zenless Zone Zero). It transforms raw JSON dumps from upstream sources (e.g., Dimbreath) into typed, validated Pydantic models for use in the Hoyo Buddy application.

### Key Technologies

- **Package Manager**: [uv](https://github.com/astral-sh/uv)
- **Async Stack**: `aiohttp` (networking), `aiofiles` (disk I/O)
- **Serialization**: `orjson` (performance-critical JSON parsing)
- **Data Validation**: `pydantic` (v2)
- **Logging**: `loguru`
- **Tooling**: `ruff` (linting & formatting), `pyright` (type checking)

## Architecture & Patterns

### 1. Client Architecture (`hb_data/common/base_client.py`)

All game-specific clients (e.g., `GIClient`, `ZZZClient`) inherit from `BaseClient`.

- **Download Logic**: Uses `aiohttp` for concurrent downloads and `aiofiles` for atomic file writes using temporary files.
- **Caching**: Game data is cached locally in the `.hb_data/` directory.
- **Memory Management**: Implements a simple `_FILE_CACHE` to avoid redundant disk reads during a single session.

### 2. Deobfuscation System (`hb_data/common/base_deob.py`)

Used primarily for ZZZ data, where JSON keys are obfuscated (e.g., `_12345` instead of `Name`).

- **Metaclass-driven**: `BaseDeobfuscator` uses `DeobfuscatorMeta` to collect `DeobfuscatedField` definitions.
- **Dynamic Key Discovery**: Fields define "finder" functions (like `find_key_by_value`) that look at a sample entry to identify the current obfuscated key name at runtime.
- **Transformation**: The `deobfuscate()` method returns a list of dictionaries with readable, stable keys.

### 3. Text Map Management (`textmaps/` & `scripts/`)

Upstream text maps (translations) are massive (100MB+). This project uses a "stripping" strategy:

- `scripts/generate_textmaps.py`: Downloads full upstream maps, extracts only the hash keys actually referenced by the data tables used in this project, and saves the minimal versions to `textmaps/`.
- **Local Storage**: The `textmaps/` directory is tracked in Git to allow the package to function without downloading massive files at runtime.

### 4. Game-Specific Modules

- `hb_data/gi/`: Genshin Impact. Data typically doesn't require deobfuscation but often uses integer hash keys for text.
- `hb_data/zzz/`: Zenless Zone Zero. Heavy use of the deobfuscation system.

## Development Workflows

### Setup & Maintenance

```bash
# Install dependencies
uv sync

# Update/Regenerate stripped text maps (requires internet)
uv run python scripts/generate_textmaps.py
```

### Testing & Validation

```bash
# Run the verification script
uv run python test.py

# Linting (Ruff)
uv run ruff check .
uv run ruff check --fix .

# Formatting
uv run ruff format .

# Type Checking
uv run pyright
```

## Coding Standards

- **Python Version**: Strict 3.12+ (uses features like `TaskGroup`, type alias statements).
- **Async-First**: All network and I/O operations must be `async`.
- **Type Safety**: Use Pydantic models for all public data structures. All functions should have type hints.
- **Style**: Adhere to the 100-character line limit defined in `ruff.toml`. Use Google-style docstrings.
- **Imports**: Use `from __future__ import annotations` and place type-only imports inside `if TYPE_CHECKING:` blocks.

## Guidelines for Adding New Data

1. **Locate Source**: Identify the upstream JSON file in Dimbreath's repositories.
2. **Define Model**: Create a Pydantic model in `hb_data/<game>/models/`.
3. **Update Deobfuscator**: If keys are obfuscated, add a new `BaseDeobfuscator` in `deob.py`.
4. **Update Client**:
    - Add the URL to the client's download list.
    - Implement a `get_*` method that merges data and returns the Pydantic models.
5. **Update TextMaps**: Add any new text map hash fields to `scripts/generate_textmaps.py` and rerun the script.
