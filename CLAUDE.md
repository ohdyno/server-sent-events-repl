# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python-based REPL for broadcasting messages via Server-Sent Events (SSE). This project combines a FastAPI web server with an interactive REPL that streams input to connected SSE clients in real-time.

## Architecture

The application uses a multi-threaded architecture:
- **Main thread**: Runs the FastAPI/uvicorn server with asyncio event loop
- **REPL thread**: Runs blocking `input()` calls for user interaction
- **Communication**: REPL thread schedules async tasks in main event loop using `asyncio.run_coroutine_threadsafe()`
- **Broadcasting**: Messages are distributed to all connected SSE clients via individual asyncio queues

## Development Commands

### Running the Server
```bash
# Start the server with REPL (default: localhost:8080)
uv run main.py

# Custom host and port
uv run main.py --host 0.0.0.0 --port 3000

# Custom static files directory
uv run main.py --dir /path/to/static
```

When the server starts, a REPL prompt (`>`) will appear. Type messages to broadcast them to all connected SSE clients at `/events`.

### Environment Setup
```bash
# Install dependencies (uv manages the virtual environment automatically)
uv sync

# Add a new dependency
uv add <package-name>

# Add a development dependency
uv add --dev <package-name>
```

### Python Version
The project uses Python 3.14 as specified in `.python-version`. The `uv` tool will automatically use this version.

## Project Structure

- `main.py` - FastAPI server with SSE endpoint and REPL thread
- `static/` - Static files directory
  - `index.html` - Landing page with links to SSE viewer
  - `sse-viewer.html` - Interactive SSE event viewer with real-time display
- `pyproject.toml` - Project metadata and dependencies (FastAPI, uvicorn)
- `.python-version` - Specifies Python 3.14 as the required version

## Key Endpoints

- `/` - Landing page
- `/events` - Server-Sent Events stream (broadcasts REPL input)
- `/sse-viewer.html` - Interactive viewer for SSE events
- `/docs` - FastAPI auto-generated API documentation
