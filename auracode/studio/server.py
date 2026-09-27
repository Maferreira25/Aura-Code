#!/usr/bin/env python3
"""Loopback-only static server for packaged Aura Studio assets."""

import functools
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional


class StudioRequestHandler(SimpleHTTPRequestHandler):
    """Serve immutable Studio assets without exposing write methods."""

    def end_headers(self) -> None:
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _reject_write(self) -> None:
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            content_length = 0
        if content_length > 1_048_576:
            self.send_response(413)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if content_length:
            self.rfile.read(content_length)
        self.send_response(405)
        self.send_header("Allow", "GET, HEAD")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self) -> None:
        self._reject_write()

    def do_PUT(self) -> None:
        self._reject_write()

    def do_PATCH(self) -> None:
        self._reject_write()

    def do_DELETE(self) -> None:
        self._reject_write()

    def log_message(self, format_string: str, *args: object) -> None:
        return


def create_server(assets_dir: Path, port: int = 0) -> ThreadingHTTPServer:
    """Create an HTTP server bound exclusively to IPv4 loopback."""
    assets = Path(assets_dir).resolve()
    if not assets.is_dir() or not (assets / "index.html").is_file():
        raise ValueError("packaged Studio assets and index.html are required")
    if port < 0 or port > 65535:
        raise ValueError("port must be between 0 and 65535")
    handler = functools.partial(StudioRequestHandler, directory=str(assets))
    return ThreadingHTTPServer(("127.0.0.1", port), handler)


def serve_studio(port: int = 0, open_browser: bool = True, assets_dir: Optional[Path] = None) -> None:
    """Serve verified assets until interrupted by the local user."""
    assets = assets_dir or Path(__file__).resolve().parent / "assets"
    server = create_server(assets, port)
    host, assigned_port = server.server_address
    url = f"http://{host}:{assigned_port}/"
    print(f"Aura Studio: {url}")
    if open_browser:
        webbrowser.open(url, new=2)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Aura Studio stopped by the local user.")
    finally:
        server.server_close()
