#!/usr/bin/env python3
"""Tests for Aura Code local-only DAST engine."""

import io
import json
import shutil
import tempfile
import unittest
from email.message import Message
from pathlib import Path
from unittest.mock import patch

from tools.dynamic_security_engine import evaluate_dast_suite, load_dast_suite


class _FakeResponse:
    def __init__(self, status=200, headers=None, body=b"ok"):
        self._status = status
        self.headers = Message()
        for k, v in (headers or {}).items():
            self.headers[k] = v
        self._body = io.BytesIO(body)

    def getcode(self):
        return self._status

    def read(self, amount=-1):
        return self._body.read(amount)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class TestDynamicSecurityEngine(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()).resolve()
        self.manifest = self.root / "dast-suite.json"
        self.manifest.write_text(json.dumps({
            "schema_version": "1.0.0",
            "suite_id": "DAST-LOCAL-001",
            "title": "Local runtime security",
            "requirements": ["REQ-SEC-001"],
            "base_url": "http://127.0.0.1:8000",
            "checks": [{
                "check_id": "DAST-HEADERS-001",
                "path": "/health",
                "method": "GET",
                "expected_status": 200,
                "required_headers": ["X-Content-Type-Options"]
            }],
            "timeout_seconds": 2,
            "max_response_bytes": 1024
        }), encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_remote_target_is_rejected(self):
        data = json.loads(self.manifest.read_text(encoding="utf-8"))
        data["base_url"] = "https://example.com"
        self.manifest.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(ValueError):
            load_dast_suite(self.manifest)

    def test_valid_runtime_contract_passes(self):
        response = _FakeResponse(
            status=200,
            headers={"X-Content-Type-Options": "nosniff"},
            body=b"ok",
        )
        with patch("tools.dynamic_security_engine.urllib.request.urlopen", return_value=response):
            result = evaluate_dast_suite(self.root, self.manifest)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["progression"]["state"], "READY")

    def test_missing_security_header_fails(self):
        response = _FakeResponse(status=200, headers={}, body=b"ok")
        with patch("tools.dynamic_security_engine.urllib.request.urlopen", return_value=response):
            result = evaluate_dast_suite(self.root, self.manifest)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["progression"]["state"], "BLOCKED")

    def test_wrong_status_fails(self):
        response = _FakeResponse(
            status=201,
            headers={"X-Content-Type-Options": "nosniff"},
            body=b"ok",
        )
        with patch("tools.dynamic_security_engine.urllib.request.urlopen", return_value=response):
            result = evaluate_dast_suite(self.root, self.manifest)
        self.assertEqual(result["status"], "FAIL")

    def test_connection_error_is_error(self):
        import urllib.error
        with patch(
            "tools.dynamic_security_engine.urllib.request.urlopen",
            side_effect=urllib.error.URLError("offline"),
        ):
            result = evaluate_dast_suite(self.root, self.manifest)
        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["progression"]["state"], "BLOCKED")

    def test_oversized_response_fails(self):
        response = _FakeResponse(
            status=200,
            headers={"X-Content-Type-Options": "nosniff"},
            body=b"x" * 2048,
        )
        with patch("tools.dynamic_security_engine.urllib.request.urlopen", return_value=response):
            result = evaluate_dast_suite(self.root, self.manifest)
        self.assertEqual(result["status"], "FAIL")


class TestDASTSchema(unittest.TestCase):
    def test_schema_is_strict(self):
        root = Path(__file__).resolve().parents[1]
        schema = json.loads((root / "schemas" / "dast-suite.schema.json").read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertFalse(schema["properties"]["checks"]["items"]["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
