#!/usr/bin/env python3
"""Runtime boundary tests for the local Aura Studio server."""

import io
import sys
import subprocess
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from auracode.studio.server import create_server
from tools import assurance
from tools.check_slop_code import check_file


class StudioServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.assets = Path(self.temp_dir.name)
        (self.assets / "index.html").write_text("<h1>Aura Studio</h1>", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_server_binds_only_to_loopback_and_serves_security_headers(self) -> None:
        server = create_server(self.assets, port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            host, port = server.server_address
            self.assertEqual(host, "127.0.0.1")
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=3) as response:
                body = response.read().decode("utf-8")
                self.assertIn("Aura Studio", body)
                self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
                self.assertEqual(response.headers["Referrer-Policy"], "no-referrer")
                self.assertIn("default-src 'self'", response.headers["Content-Security-Policy"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)

    def test_server_rejects_http_writes(self) -> None:
        server = create_server(self.assets, port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            _, port = server.server_address
            request = urllib.request.Request(f"http://127.0.0.1:{port}/", data=b"change", method="POST")
            with self.assertRaises(urllib.error.HTTPError) as raised:
                urllib.request.urlopen(request, timeout=3)
            self.assertEqual(raised.exception.code, 405)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)

    def test_public_cli_refuses_unverified_studio_package(self) -> None:
        package_result = {"status": "NOT_RUN", "reason": "Assets are not packaged."}
        output = io.StringIO()
        with (
            patch.object(sys, "argv", ["auracode", "studio", "--no-browser"]),
            patch("tools.assurance.studio_package.verify_studio_package", return_value=package_result),
            patch("tools.assurance._serve_studio") as serve,
            redirect_stdout(output),
        ):
            with self.assertRaises(SystemExit) as raised:
                assurance.main()

        self.assertEqual(raised.exception.code, 2)
        self.assertFalse(serve.called)
        self.assertIn("Assets are not packaged", output.getvalue())

    def test_cli_can_be_imported_before_studio_server(self) -> None:
        root = Path(__file__).resolve().parents[1]
        completed = subprocess.run(
            [sys.executable, "-c", "import tools.assurance; import auracode.studio.server"],
            cwd=root,
            capture_output=True,
            text=True,
            shell=False,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_server_has_no_silently_swallowed_exception(self) -> None:
        server_source = Path(__file__).resolve().parents[1] / "auracode" / "studio" / "server.py"

        violations = check_file(str(server_source), str(server_source.parent))

        self.assertFalse(
            any(item["type"] == "silent_exception_swallowing" for item in violations),
            violations,
        )


if __name__ == "__main__":
    unittest.main()
