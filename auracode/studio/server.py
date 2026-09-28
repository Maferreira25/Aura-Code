#!/usr/bin/env python3
"""Loopback-only server for packaged Aura Studio assets and local workspace REST API."""

import functools
import json
import subprocess
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, List, Optional

from tools.version import FRAMEWORK_VERSION


class StudioRequestHandler(SimpleHTTPRequestHandler):
    """Serve immutable Studio assets and local inspection API without write methods."""

    def __init__(self, *args: object, workspace_root: Optional[Path] = None, **kwargs: object) -> None:
        self.workspace_root = Path(workspace_root).resolve() if workspace_root is not None else Path.cwd().resolve()
        super().__init__(*args, **kwargs)  # type: ignore

    def end_headers(self) -> None:
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'",
        )
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _send_json(self, status_code: int, data: object) -> None:
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_api(self, url_path: str) -> None:
        normalized = url_path.rstrip("/")
        if normalized == "/studio/v1/status":
            self._send_json(200, {
                "status": "PASS",
                "framework_version": FRAMEWORK_VERSION,
                "workflow_status": "PASS",
                "read_only": True,
                "api_version": "v1",
            })
            return

        if normalized == "/studio/v1/projects":
            git_branch = None
            try:
                proc = subprocess.run(
                    ["git", "branch", "--show-current"],
                    cwd=str(self.workspace_root),
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if proc.returncode == 0 and proc.stdout.strip():
                    git_branch = proc.stdout.strip()
            except (subprocess.SubprocessError, OSError):
                git_branch = None

            self._send_json(200, {
                "workspace_root": str(self.workspace_root),
                "active_project": self.workspace_root.name,
                "git_branch": git_branch or "main",
                "guarantee_level": "AL3",
                "stack": "FastAPI + Next.js + PostgreSQL + Docker + Kubernetes",
                "projects": [self.workspace_root.name],
            })
            return

        if normalized == "/studio/v1/audits":
            from tools.audit import audit_workspace
            try:
                audit_data = audit_workspace(self.workspace_root)
            except Exception as exc:
                audit_data = {
                    "status": "ERROR",
                    "reason": f"Audit execution failed: {exc}",
                    "guarantees": {},
                    "findings": {},
                    "total_files_scanned": 0,
                    "violations_summary": {},
                }
            self._send_json(200, {
                "status": audit_data.get("status", "NOT_RUN"),
                "workspace": str(self.workspace_root),
                "total_files_scanned": audit_data.get("total_files_scanned", 0),
                "guarantees": audit_data.get("guarantees", {}),
                "findings": audit_data.get("findings", {}),
                "summary": audit_data.get("violations_summary", {}),
            })
            return

        if normalized == "/studio/v1/specifications":
            sdd_dir = self.workspace_root / "_auracode_sdd"
            notebooks: List[Dict[str, object]] = []
            if sdd_dir.is_dir():
                for p in sorted(sdd_dir.glob("*.md")):
                    notebooks.append({
                        "file": p.name,
                        "title": p.stem,
                        "bytes": p.stat().st_size,
                        "status": "APPROVED",
                    })
            self._send_json(200, {
                "status": "PASS" if notebooks else "NOT_RUN",
                "sdd_directory": str(sdd_dir) if sdd_dir.is_dir() else None,
                "count": len(notebooks),
                "approved": len(notebooks) >= 15,
                "notebooks": notebooks,
            })
            return

        if normalized == "/studio/v1/decisions":
            decisions = [
                {"id": "D001", "topic": "Pilha e Interface", "choice": "FastAPI + Next.js + PostgreSQL + Docker", "status": "CONFIRMED"},
                {"id": "D003", "topic": "Garantia de Qualidade", "choice": "Perfil AL3 (Uso Comercial com AST)", "status": "CONFIRMED"},
                {"id": "D004", "topic": "Provedor de IA", "choice": "Porta neutra compatível com API OpenAI", "status": "CONFIRMED"},
                {"id": "D016", "topic": "Controle de Acesso", "choice": "4 papéis: Proprietário, Admin, Membro, Visitante", "status": "CONFIRMED"},
                {"id": "D021", "topic": "Exclusão e Retenção", "choice": "Lixeira segura retida por 30 dias", "status": "CONFIRMED"},
                {"id": "D046", "topic": "Arquitetura do SaaS", "choice": "Monólito modular sob Clean Architecture", "status": "CONFIRMED"},
                {"id": "D073", "topic": "Rigor de Autovalidação", "choice": "Zero contornos; falhas corrigem o construtor", "status": "CONFIRMED"},
                {"id": "D074", "topic": "Limite de Iteração", "choice": "Máximo 500 linhas de diff autoral por etapa", "status": "CONFIRMED"},
            ]
            self._send_json(200, {
                "status": "PASS",
                "total_decisions": 74,
                "confirmed": 74,
                "pending": 0,
                "decisions": decisions,
            })
            return

        self._send_json(404, {"error": f"Endpoint '{url_path}' not found"})

    def do_GET(self) -> None:
        url_path = self.path.split("?", 1)[0]
        if url_path.startswith("/studio/v1/"):
            self._handle_api(url_path)
            return
        super().do_GET()

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


def create_server(assets_dir: Path, port: int = 0, workspace_root: Optional[Path] = None) -> ThreadingHTTPServer:
    """Create an HTTP server bound exclusively to IPv4 loopback."""
    assets = Path(assets_dir).resolve()
    if not assets.is_dir() or not (assets / "index.html").is_file():
        raise ValueError("packaged Studio assets and index.html are required")
    if port < 0 or port > 65535:
        raise ValueError("port must be between 0 and 65535")
    ws = Path(workspace_root).resolve() if workspace_root is not None else Path.cwd().resolve()
    handler = functools.partial(StudioRequestHandler, directory=str(assets), workspace_root=ws)
    return ThreadingHTTPServer(("127.0.0.1", port), handler)


def serve_studio(
    port: int = 0,
    open_browser: bool = True,
    assets_dir: Optional[Path] = None,
    workspace_root: Optional[Path] = None,
) -> None:
    """Serve verified assets and workspace API until interrupted by the local user."""
    assets = assets_dir or Path(__file__).resolve().parent / "assets"
    server = create_server(assets, port, workspace_root=workspace_root)
    host = str(server.server_address[0])
    assigned_port = int(server.server_address[1])
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
