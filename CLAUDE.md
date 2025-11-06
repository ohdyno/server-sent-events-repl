# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python-based REPL for interacting with Server-Sent Events (SSE). This project is managed using `uv` (a fast Python package manager) and targets Python 3.14.

## Development Commands

### Environment Setup
```bash
# Install dependencies (uv manages the virtual environment automatically)
uv sync

# Run the main application
uv run main.py

# Add a new dependency
uv add <package-name>

# Add a development dependency
uv add --dev <package-name>
```

### Python Version
The project uses Python 3.14 as specified in `.python-version`. The `uv` tool will automatically use this version.

## Project Structure

- `main.py` - Entry point for the application
- `pyproject.toml` - Project metadata and dependencies managed by uv
- `.python-version` - Specifies Python 3.14 as the required version
