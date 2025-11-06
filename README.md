# Server-Sent Events REPL

A Python-based REPL for broadcasting messages via Server-Sent Events (SSE). This project combines a FastAPI web server with an interactive REPL that streams input to connected SSE clients in real-time.

## Features

- **Interactive REPL**: Type messages to broadcast them instantly to all connected clients
- **Custom Event Types**: Send both standard data messages and custom named events
- **Real-time SSE Viewer**: Beautiful dark-themed web interface to view events as they arrive
- **Multi-client Support**: Broadcast to unlimited concurrent SSE connections
- **Thread-safe Architecture**: Proper async/threading coordination between REPL and server

## Quick Start

```bash
# Install dependencies
uv sync

# Start the server (includes REPL)
uv run main.py

# Open the viewer in your browser
# http://localhost:8080/sse-viewer.html
```

## REPL Usage

The REPL supports two types of messages:

### Data Messages (Standard SSE)
```
> data: Hello, world!
> This is also a data message (data: prefix is optional)
```

### Custom Events
```
> event: alert This is an urgent message
> event: notification New user signed up
> event: status System is running normally
```

### Special Commands
```
> help    - Show usage instructions
```

## Example Session

```bash
$ uv run main.py
Starting server on http://localhost:8080
============================================================
REPL Started - Type messages to broadcast via SSE
Messages will be sent to all connected clients at /events

Usage:
  data: <message>   - Send as regular data message
  event: <name> <message> - Send as custom event
  help              - Show this help message
============================================================

> data: Server is starting up
> event: status All systems operational
> event: alert Critical update available
> Welcome message for all users
```

## API Endpoints

- `/` - Landing page with links
- `/events` - SSE endpoint (connect here to receive broadcasts)
- `/sse-viewer.html` - Interactive event viewer
- `/docs` - FastAPI auto-generated API documentation

## Architecture

The application uses a multi-threaded architecture:
- **Main thread**: Runs the FastAPI/uvicorn server with asyncio event loop
- **REPL thread**: Runs blocking `input()` calls for user interaction
- **Communication**: Thread-safe message passing using `asyncio.run_coroutine_threadsafe()`
- **Broadcasting**: Pub/sub pattern with individual asyncio queues per SSE client

## Requirements

- Python 3.14+
- FastAPI
- uvicorn

## Development

See [CLAUDE.md](CLAUDE.md) for detailed development instructions and architecture notes.
