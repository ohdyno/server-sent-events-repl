import argparse
import asyncio
from datetime import datetime
from pathlib import Path
import threading
import sys
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
import uvicorn


# Global variable to store static directory
STATIC_DIR: Path = Path.cwd() / "static"

# List of subscriber queues for SSE
subscribers: list[asyncio.Queue] = []


def repl_thread(loop: asyncio.AbstractEventLoop):
    """REPL thread that reads input and broadcasts to SSE clients."""
    print("\n" + "="*60)
    print("REPL Started - Type messages to broadcast via SSE")
    print("Messages will be sent to all connected clients at /events")
    print("")
    print("Usage:")
    print("  data: <message>   - Send as regular data message")
    print("  event: <name> <message> - Send as custom event")
    print("  help              - Show this help message")
    print("="*60 + "\n")

    while True:
        try:
            line = input("> ")
            if not line.strip():
                continue

            # Handle special commands
            if line.strip().lower() == "help":
                print("\nUsage:")
                print("  data: <message>         - Send as regular data message")
                print("  event: <name> <message> - Send as custom event")
                print("  help                    - Show this help message")
                print()
                continue

            # Parse the input
            event_type, message = parse_input(line)

            # Schedule the broadcast in the asyncio event loop
            asyncio.run_coroutine_threadsafe(
                broadcast_message(event_type, message), loop
            )
        except EOFError:
            break
        except KeyboardInterrupt:
            break


def parse_input(line: str) -> tuple[str, str]:
    """Parse REPL input to determine event type and message.

    Returns:
        tuple of (event_type, message) where event_type is 'message' or a custom event name
    """
    line = line.strip()

    # Check for "data:" prefix
    if line.lower().startswith("data:"):
        message = line[5:].strip()
        return ("message", message)

    # Check for "event:" prefix
    if line.lower().startswith("event:"):
        rest = line[6:].strip()
        # Split into event name and message
        parts = rest.split(None, 1)
        if len(parts) == 2:
            event_name, message = parts
            return (event_name, message)
        elif len(parts) == 1:
            # Event name but no message
            return (parts[0], "")
        else:
            # Just "event:" with nothing after
            return ("message", line)

    # No prefix - treat as regular data message
    return ("message", line)


async def broadcast_message(event_type: str, message: str):
    """Broadcast a message to all SSE subscribers.

    Args:
        event_type: 'message' for regular data, or custom event name
        message: The message content
    """
    # Escape message for JSON
    escaped_message = message.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')

    # Send to all subscribers
    event_data = {"type": event_type, "message": escaped_message}
    for queue in subscribers[:]:  # Create a copy to avoid modification during iteration
        try:
            await queue.put(event_data)
        except Exception as e:
            print(f"Error broadcasting to subscriber: {e}")


def create_app(static_dir: Path) -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="Static File Server")

    # Store static_dir in app state
    app.state.static_dir = static_dir

    @app.get("/events")
    async def events():
        """Server-Sent Events endpoint that streams REPL input."""
        async def event_generator():
            # Create a local queue for this client
            client_queue = asyncio.Queue()

            # Subscribe to global events
            subscribers.append(client_queue)

            try:
                while True:
                    # Wait for events from the REPL
                    event_data = await client_queue.get()
                    timestamp = datetime.now().isoformat()

                    event_type = event_data["type"]
                    message = event_data["message"]

                    # Format as SSE based on event type
                    if event_type == "message":
                        # Regular data message
                        yield f"data: {{\"message\": \"{message}\", \"timestamp\": \"{timestamp}\"}}\n\n"
                    else:
                        # Custom event with event type
                        yield f"event: {event_type}\ndata: {{\"message\": \"{message}\", \"timestamp\": \"{timestamp}\"}}\n\n"
            finally:
                # Cleanup when client disconnects
                subscribers.remove(client_queue)

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    @app.get("/")
    async def root():
        """Serve index.html for root path."""
        return await serve_static("index.html")

    @app.get("/{path:path}")
    async def serve_static(path: str):
        """Serve static files from the configured directory."""
        static_dir = app.state.static_dir

        # Default to index.html if path is empty
        if not path or path == "":
            path = "index.html"

        file_path = static_dir / path

        # Security check: ensure the file is within the static directory
        try:
            file_path = file_path.resolve()
            file_path.relative_to(static_dir.resolve())
        except (ValueError, RuntimeError):
            raise HTTPException(status_code=403, detail="Access denied")

        # Check if file exists and is a file (not a directory)
        if not file_path.is_file():
            raise HTTPException(status_code=404, detail=f"File not found: {path}")

        # Serve the file
        return FileResponse(file_path)

    return app


async def run_server(app: FastAPI, host: str, port: int):
    """Run the uvicorn server."""
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


def main():
    parser = argparse.ArgumentParser(
        description="Server-Sent Events REPL"
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=Path.cwd() / "static",
        help="Directory to serve static files from (default: ./static)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Host to bind to (default: localhost)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to bind to (default: 8080)"
    )

    args = parser.parse_args()

    # Ensure the static directory exists
    static_dir = args.dir.resolve()
    if not static_dir.exists():
        print(f"Creating directory: {static_dir}")
        static_dir.mkdir(parents=True, exist_ok=True)

    if not static_dir.is_dir():
        print(f"Error: {static_dir} is not a directory")
        return 1

    print(f"Starting server on http://{args.host}:{args.port}")
    print(f"Serving files from: {static_dir}")

    app = create_app(static_dir)

    # Get the event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Start REPL in a separate thread
    repl = threading.Thread(target=repl_thread, args=(loop,), daemon=True)
    repl.start()

    # Run the server
    try:
        loop.run_until_complete(run_server(app, args.host, args.port))
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        loop.close()


if __name__ == "__main__":
    main()
