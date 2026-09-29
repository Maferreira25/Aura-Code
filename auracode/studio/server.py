#!/usr/bin/env python3
"""Loopback-only server for packaged Aura Studio assets and local workspace REST API.

Architecture:
- Single Responsibility Principle (SRP): Decoupled inspection domain service (StudioWorkspaceService)
  from HTTP protocol transport and security enforcement (StudioRequestHandler).
- Open/Closed Principle (OCP): Dispatch route table mapping API endpoints to domain methods.
- Fail-Closed Security: Strictly loopback IPv4 (127.0.0.1), immutable read-only methods (GET/HEAD),
  strict Content-Security-Policy, and anti-tamper security headers.
"""

import functools
import json
import re
import socket
import subprocess
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from tools.version import FRAMEWORK_VERSION


class StudioWorkspaceService:
    """Domain service responsible for inspecting workspace state, specs, and audits."""

    def __init__(self, workspace_root: Path, server_port: Optional[int] = None) -> None:
        self.workspace_root = workspace_root.resolve()
        self.server_port = server_port

    def get_status(self) -> Dict[str, Any]:
        """Return framework status and the truthful state of the workspace audit."""
        workflow_status = self.get_audits().get("status", "NOT_RUN")
        return {
            "status": "PASS",
            "framework_version": FRAMEWORK_VERSION,
            "workflow_status": workflow_status,
            "read_only": True,
            "api_version": "v1",
        }

    def get_projects(self) -> Dict[str, Any]:
        """Inspect workspace metadata, Git branch, assurance profile, and stack."""
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

        assurance_level = "AL3"
        for candidate in [
            self.workspace_root / "contracts.json",
            self.workspace_root / ".auracode" / "contracts.json",
        ]:
            if candidate.is_file():
                try:
                    data = json.loads(candidate.read_text(encoding="utf-8"))
                    assurance_level = data.get("assurance_level", "AL3")
                    break
                except (json.JSONDecodeError, OSError):
                    assurance_level = "AL3"
                    break

        detected_parts = []
        if (self.workspace_root / "pyproject.toml").is_file() or (self.workspace_root / "requirements.txt").is_file():
            detected_parts.append("Python")
        if (self.workspace_root / "package.json").is_file():
            detected_parts.append("Node.js / TypeScript")
        if (self.workspace_root / "Dockerfile").is_file() or (self.workspace_root / "docker-compose.yml").is_file():
            detected_parts.append("Docker")
        if (self.workspace_root / "saas.db").is_file():
            detected_parts.append("SQLite")
        if (self.workspace_root / "go.mod").is_file():
            detected_parts.append("Go")
        if (self.workspace_root / "pom.xml").is_file():
            detected_parts.append("Java")

        detected_stack = " + ".join(detected_parts) if detected_parts else "General Application Workspace"

        return {
            "workspace_root": str(self.workspace_root),
            "active_project": self.workspace_root.name,
            "git_branch": git_branch or "main",
            "guarantee_level": assurance_level,
            "stack": detected_stack,
            "projects": [self.workspace_root.name],
        }

    def get_audits(self) -> Dict[str, Any]:
        """Run or inspect workspace static AST audit."""
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

        return {
            "status": audit_data.get("status", "NOT_RUN"),
            "workspace": str(self.workspace_root),
            "total_files_scanned": audit_data.get("total_files_scanned", 0),
            "guarantees": audit_data.get("guarantees", {}),
            "findings": audit_data.get("findings", {}),
            "summary": audit_data.get("violations_summary", {}),
        }

    def get_specifications(self) -> Dict[str, Any]:
        """Inspect theoretical blueprint specification notebooks in _auracode_sdd."""
        sdd_dir = self.workspace_root / "_auracode_sdd"
        if not sdd_dir.is_dir() and (self.workspace_root / "_reversa_sdd").is_dir():
            sdd_dir = self.workspace_root / "_reversa_sdd"
        notebooks: List[Dict[str, Any]] = []
        approved_count = 0
        if sdd_dir.is_dir():
            for p in sorted(sdd_dir.glob("*.md")):
                content_lower = ""
                try:
                    content_lower = p.read_text(encoding="utf-8", errors="ignore").lower()
                except OSError as exc:
                    content_lower = f"unreadable: {exc}"
                is_this_approved = any(
                    marker in content_lower
                    for marker in ("status: aprovado", "status: approved", "planta aprovada")
                )
                if is_this_approved:
                    approved_count += 1
                notebooks.append({
                    "file": p.name,
                    "title": p.stem,
                    "bytes": p.stat().st_size,
                    "status": "APPROVED" if is_this_approved else "DRAFT",
                })

        is_approved = (len(notebooks) > 0 and approved_count == len(notebooks))
        return {
            "status": "PASS" if is_approved else ("DRAFT" if notebooks else "NOT_RUN"),
            "sdd_directory": str(sdd_dir) if sdd_dir.is_dir() else None,
            "count": len(notebooks),
            "approved": is_approved,
            "approved_count": approved_count,
            "notebooks": notebooks,
        }

    def get_decisions(self) -> Dict[str, Any]:
        """Read traceability decisions from PRD specification or report uninitialized state."""
        decisions: List[Dict[str, str]] = []
        total_count = 0
        prd_file = self.workspace_root / "_auracode_sdd" / "01_PRD.md"
        if not prd_file.is_file():
            cand = self.workspace_root / "_reversa_sdd" / "01_PRD.md"
            if cand.is_file():
                prd_file = cand

        if prd_file.is_file():
            try:
                lines = prd_file.read_text(encoding="utf-8").splitlines()
                in_table = False
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith("| Decisões") or stripped.startswith("| Decisao"):
                        in_table = True
                        continue
                    if in_table and stripped.startswith("|---"):
                        continue
                    if in_table and stripped.startswith("|"):
                        cols = [c.strip() for c in stripped.strip("|").split("|")]
                        if len(cols) >= 3:
                            id_col = cols[0]
                            range_match = re.search(r"(\d+)\s*[–\-]\s*[A-Za-z]*(\d+)", id_col)
                            if range_match:
                                start_n, end_n = int(range_match.group(1)), int(range_match.group(2))
                                total_count += max(1, end_n - start_n + 1)
                            else:
                                total_count += 1
                            decisions.append({
                                "id": id_col,
                                "topic": cols[1],
                                "choice": cols[2],
                                "status": "CONFIRMED",
                            })
                    elif in_table and not stripped.startswith("|"):
                        if stripped.startswith("#"):
                            in_table = False
            except OSError:
                decisions = []
                total_count = 0

        if not decisions:
            return {
                "status": "NOT_RUN",
                "total_decisions": 0,
                "confirmed": 0,
                "pending": 0,
                "decisions": [],
            }

        return {
            "status": "PASS",
            "total_decisions": total_count,
            "confirmed": total_count,
            "pending": 0,
            "decisions": decisions,
        }

    def get_agents(self) -> Dict[str, Any]:
        """Dynamically discover available agents and skills from .agents/skills."""
        agents_dir = self.workspace_root / ".agents" / "skills"
        if not agents_dir.is_dir():
            framework_root = Path(__file__).resolve().parents[2]
            cand = framework_root / ".agents" / "skills"
            if cand.is_dir():
                agents_dir = cand

        agent_items: List[Dict[str, str]] = []
        if agents_dir.is_dir():
            for skill_dir in sorted(agents_dir.iterdir()):
                if not skill_dir.is_dir():
                    continue
                skill_file = skill_dir / "SKILL.md"
                if not skill_file.is_file():
                    continue
                name = skill_dir.name
                desc = "Agente especializado do Aura Code"
                try:
                    content = skill_file.read_text(encoding="utf-8")
                    if content.startswith("---"):
                        parts = content.split("---", 2)
                        if len(parts) >= 3:
                            for line in parts[1].splitlines():
                                if line.startswith("description:"):
                                    desc = line.split("description:", 1)[1].strip()
                                elif line.startswith("name:"):
                                    name = line.split("name:", 1)[1].strip()
                except OSError as exc:
                    desc = f"Carregamento indisponível: {exc}"

                agent_items.append({
                    "id": skill_dir.name,
                    "name": name,
                    "status": "READY",
                    "scope": desc,
                })

        if not agent_items:
            agent_items = [
                {"id": "auracode", "name": "Orquestrador Geral", "status": "READY", "scope": "Pair programming para leigos"},
                {"id": "auracode-clarify", "name": "Clarificador", "status": "READY", "scope": "Briefing e analogias cotidianas"},
                {"id": "auracode-brainstorm", "name": "Ideação", "status": "READY", "scope": "Maturação de ideias e pre-mortem"},
                {"id": "auracode-new", "name": "Arquiteto Inicial", "status": "READY", "scope": "Entrevista guiada e Planta Teórica"},
                {"id": "auracode-forward", "name": "Construtor Clean Arch", "status": "READY", "scope": "Scaffolding e código cirúrgico"},
                {"id": "auracode-audit", "name": "Auditor Geral", "status": "READY", "scope": "Garantias estáticas AST 7 eixos"},
                {"id": "auracode-adversary", "name": "Auditor Adversarial", "status": "READY", "scope": "Red-team, STRIDE e oráculos"},
                {"id": "auracode-debugger", "name": "Tratador de Bugs", "status": "READY", "scope": "Reprodução obrigatória e correção"},
                {"id": "auracode-refactor", "name": "Refatorador", "status": "READY", "scope": "Tipagem, slop e Clean Arch"},
                {"id": "auracode-guard", "name": "Guardião Ativo", "status": "READY", "scope": "Interceptação pré-execução e hooks"},
                {"id": "auracode-worktree", "name": "Isolador de Branches", "status": "READY", "scope": "Contenção física em Git worktrees"},
                {"id": "auracode-cage", "name": "Sandbox Hermético", "status": "READY", "scope": "DevContainer Default-Deny"},
                {"id": "auracode-loop", "name": "Runner Autônomo", "status": "READY", "scope": "Arquitetura Ralph anti-dumb-zone"},
                {"id": "auracode-debate", "name": "Debate Dialético", "status": "READY", "scope": "3 subagentes em turnos com contenção"},
                {"id": "auracode-agents-help", "name": "Catálogo de Agentes", "status": "READY", "scope": "Manual explicativo não-técnico"},
            ]

        return {
            "status": "PASS",
            "total_agents": len(agent_items),
            "ready_count": len(agent_items),
            "agents": agent_items,
        }

    def get_services(self) -> Dict[str, Any]:
        """Inspect running local services for preview and diagnosis."""
        def is_port_open(port: int) -> bool:
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.15):
                    return True
            except (OSError, TimeoutError):
                return False

        fastapi_online = is_port_open(8000)
        postgres_online = is_port_open(5432)
        web_online = is_port_open(3000)
        saas_db_found = (
            (self.workspace_root / "_auracode_forward" / "saas" / "saas.db").is_file()
            or (self.workspace_root / "saas.db").is_file()
        )

        db_status = "ONLINE (:5432 PostgreSQL)" if postgres_online else ("ONLINE (saas.db)" if saas_db_found else "READY")

        db_healthy = postgres_online or saas_db_found
        return {
            "status": "PASS",
            "services": [
                {
                    "name": "FastAPI REST Server",
                    "endpoint": "http://127.0.0.1:8000",
                    "status": "ONLINE" if fastapi_online else "STANDBY",
                    "healthy": fastapi_online,
                },
                {
                    "name": "SQL Database",
                    "endpoint": ":5432 (PostgreSQL) / saas.db (SQLite)",
                    "status": db_status,
                    "healthy": db_healthy,
                },
                {
                    "name": "SaaS Web (Next.js / React)",
                    "endpoint": "http://127.0.0.1:3000",
                    "status": "ONLINE" if web_online else "STANDBY",
                    "healthy": web_online,
                },
                {
                    "name": "Aura Studio API",
                    "endpoint": f"http://127.0.0.1:{self.server_port}",
                    "status": "ONLINE",
                    "healthy": True,
                },
            ],
        }


# Open/Closed Principle: Endpoint router dispatch table
ROUTE_DISPATCH: Dict[str, Callable[[StudioWorkspaceService], Dict[str, Any]]] = {
    "/studio/v1/status": lambda svc: svc.get_status(),
    "/studio/v1/projects": lambda svc: svc.get_projects(),
    "/studio/v1/audits": lambda svc: svc.get_audits(),
    "/studio/v1/specifications": lambda svc: svc.get_specifications(),
    "/studio/v1/decisions": lambda svc: svc.get_decisions(),
    "/studio/v1/agents": lambda svc: svc.get_agents(),
    "/studio/v1/services": lambda svc: svc.get_services(),
}


class StudioRequestHandler(SimpleHTTPRequestHandler):
    """Serve immutable Studio assets and local inspection API without write methods."""

    def __init__(
        self,
        *args: object,
        workspace_root: Optional[Path] = None,
        server_port: Optional[int] = None,
        **kwargs: object,
    ) -> None:
        self.workspace_root = Path(workspace_root).resolve() if workspace_root is not None else Path.cwd().resolve()
        port = server_port
        if port is None and len(args) >= 3 and hasattr(args[2], "server_address"):
            server_obj = args[2]
            if isinstance(server_obj.server_address, tuple) and len(server_obj.server_address) >= 2:  # type: ignore
                port = int(server_obj.server_address[1])  # type: ignore
        self.service = StudioWorkspaceService(self.workspace_root, server_port=port or 4300)
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

    def _send_json(self, status_code: int, data: object, send_body: bool = True) -> None:
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if send_body:
            self.wfile.write(body)

    def _handle_api(self, url_path: str, send_body: bool = True) -> None:
        normalized = url_path.rstrip("/")
        handler = ROUTE_DISPATCH.get(normalized)
        if handler is not None:
            try:
                data = handler(self.service)
                self._send_json(200, data, send_body=send_body)
            except Exception as exc:
                self._send_json(500, {"error": f"Handler error on '{url_path}': {exc}"}, send_body=send_body)
            return

        self._send_json(404, {"error": f"Endpoint '{url_path}' not found"}, send_body=send_body)

    def do_GET(self) -> None:
        url_path = self.path.split("?", 1)[0]
        if url_path.startswith("/studio/v1/"):
            self._handle_api(url_path, send_body=True)
            return
        super().do_GET()

    def do_HEAD(self) -> None:
        url_path = self.path.split("?", 1)[0]
        if url_path.startswith("/studio/v1/"):
            self._handle_api(url_path, send_body=False)
            return
        super().do_HEAD()

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

    def log_message(self, format: str, *args: object) -> None:
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
    assigned_port = server.server_address[1]
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
