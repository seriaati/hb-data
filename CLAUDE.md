# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**hb-data** is a Python package that parses and deobfuscates game data for Hoyo Buddy, supporting multiple games (currently GI = Genshin Impact, ZZZ = Zenless Zone Zero). It downloads data from Dimbreath data dumps and transforms it into typed Pydantic models.

## Commands

```bash
# Install dependencies
uv sync

# Run the test script
uv run python test.py

# Lint
uv run ruff check .

# Lint with auto-fix
uv run ruff check --fix .

# Format
uv run ruff format .

# Build package
uv build
```

## Architecture

### Key Patterns

**BaseClient** (`hb_data/common/base_client.py`): All game clients inherit from this. Provides async HTTP (aiohttp), async file I/O (aiofiles), atomic file writing via temp files, and JSON parsing (orjson). Data is cached under `.hb_data/`.

**BaseDeobfuscator** (`hb_data/common/base_deob.py`): Metaclass-based system for handling obfuscated JSON keys in game data. Each deobfuscator declares `DeobfuscatedField` entries with finder functions (`find_key_by_value`, `find_key_by_position`) that locate the obfuscated key from a sample entry. The deobfuscator then remaps all entries to use readable key names.

**Game Client Flow**: Each client downloads text maps (translations) + data files → reads JSON → applies deobfuscation → merges related data sources → validates into Pydantic models → provides `get_*()` methods with language parameter.

### Module Structure

- `hb_data/common/` — Shared base classes and utilities
- `hb_data/gi/` — Genshin Impact client and models
- `hb_data/zzz/` — Zenless Zone Zero client, deobfuscators, and models

### Adding a New Game

1. Create `hb_data/<game>/` with `client.py`, `deob.py`, `models/`
2. Subclass `BaseClient` for the client
3. Define `BaseDeobfuscator` subclasses for each obfuscated data table
4. Define Pydantic models with language-aware name resolution
5. Export from `hb_data/__init__.py`

### Adding Data to an Existing Game

1. Add a new `BaseDeobfuscator` subclass in `deob.py` if the table has obfuscated keys
2. Download and cache the new data file in the client's `download()` method
3. Parse and merge in the client's data loading methods
4. Add a Pydantic model in `models/`
5. Expose via a `get_*()` method on the client

## Code Style

- **Line length**: 100 characters
- **Docstrings**: Google style
- **Linter**: Ruff with an extensive rule set (see `ruff.toml`)
- **Python**: 3.12+, async-first design throughout
- Use `TYPE_CHECKING` imports for forward references
