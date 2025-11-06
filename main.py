import argparse
import asyncio
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
import uvicorn


# Global variable to store static directory
STATIC_DIR: Path = Path.cwd() / "static"


def create_app(static_dir: Path) -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="Static File Server")

    # Store static_dir in app state
    app.state.static_dir = static_dir

    @app.get("/events")
    async def events():
        """Server-Sent Events endpoint that sends demo events."""
        async def event_generator():
            count = 0
            while True:
                count += 1
                timestamp = datetime.now().isoformat()

                # Send different types of events
                if count % 5 == 0:
                    yield f"event: custom\ndata: {{\"type\": \"custom\", \"count\": {count}, \"timestamp\": \"{timestamp}\"}}\n\n"
                else:
                    yield f"data: {{\"type\": \"message\", \"count\": {count}, \"timestamp\": \"{timestamp}\"}}\n\n"

                await asyncio.sleep(1)

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


def main():
    parser = argparse.ArgumentParser(
        description="Simple static file server"
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
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
