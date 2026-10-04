"""Tes fitur AI memakai SDK `anthropic` yang ASLI, terhadap server Anthropic TIRUAN.

Server tiruan berjalan di komputer ini (127.0.0.1), jadi tidak ada permintaan yang
keluar ke internet dan tidak ada biaya. Tes ini memastikan permintaan yang dikirim
SDK berbentuk benar dan error dari server diterjemahkan dengan benar.

Dilewati bila paket `anthropic` belum terpasang (lihat requirements.txt).
"""

import json
import os
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest import mock

from app import ai
from tests.helpers import ApiTestCase

try:
    import anthropic  # noqa: F401
    HAVE_SDK = True
except ImportError:
    HAVE_SDK = False

KEY = "sk-ant-api03-kunci-tiruan"


def message(model, text="Koneksi berhasil."):
    return 200, {
        "id": "msg_tiruan", "type": "message", "role": "assistant", "model": model,
        "content": [{"type": "text", "text": text}],
        "stop_reason": "end_turn", "stop_sequence": None,
        "usage": {"input_tokens": 20, "output_tokens": 10},
    }


def error(status, kind, text="error"):
    return status, {"type": "error", "error": {"type": kind, "message": text}}


class FakeAnthropic:
    """Server HTTP kecil yang meniru POST /v1/messages."""

    def __init__(self):
        self.answers = []
        self.received = []
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                headers = {k.lower(): v for k, v in self.headers.items()}
                fake.received.append({"path": self.path, "headers": headers, "body": body})
                status, payload = fake.answers.pop(0)
                data = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()


@unittest.skipUnless(HAVE_SDK, "Paket 'anthropic' belum terpasang; tes SDK dilewati (opsional).")
class RealSdkTest(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.fake = FakeAnthropic()
        self.addCleanup(self.fake.close)
        for patcher in (
            mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": KEY, "ANTHROPIC_BASE_URL": self.fake.url}),
            mock.patch.object(ai, "MAX_RETRIES", 0),  # tanpa coba ulang, supaya tes cepat
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.request("PATCH", "/api/settings", {"ai_enabled": True})

    def test_simple_model_request(self):
        self.fake.answers.append(message("claude-haiku-4-5"))
        status, data = self.request("POST", "/api/ai/test", {"tier": "simple"})
        self.assertEqual(status, 200, data)
        self.assertEqual(data["text"], "Koneksi berhasil.")
        sent = self.fake.received[0]
        self.assertEqual(sent["headers"]["x-api-key"], KEY)
        self.assertEqual(sent["body"]["model"], "claude-haiku-4-5")
        self.assertNotIn("fallbacks", sent["body"])
        self.assertNotIn("output_config", sent["body"])
        self.assertNotIn("anthropic-beta", sent["headers"])

    def test_smart_model_request_has_fallbacks_and_effort(self):
        self.fake.answers.append(message("claude-opus-5-5"))
        status, data = self.request("POST", "/api/ai/test", {"tier": "smart"})
        self.assertEqual(status, 200, data)
        sent = self.fake.received[0]
        self.assertIn("server-side-fallback-2026-07-01", sent["headers"]["anthropic-beta"])
        self.assertEqual(sent["body"]["fallbacks"], "default")
        self.assertEqual(sent["body"]["output_config"], {"effort": "low"})
        self.assertNotIn("thinking", sent["body"])

    def test_structured_output_round_trip(self):
        self.fake.answers.append(message("claude-haiku-4-5", '{"ok": true}'))
        schema = {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"], "additionalProperties": False}
        result = ai.ask("simple", system="s", messages=[{"role": "user", "content": "x"}], max_tokens=100, schema=schema)
        self.assertEqual(result.data, {"ok": True})
        self.assertEqual(self.fake.received[0]["body"]["output_config"]["format"]["type"], "json_schema")

    def test_errors_are_translated(self):
        cases = [
            (error(401, "authentication_error"), "auth", ".env"),
            (error(404, "not_found_error"), "model", "Pengaturan"),
            (error(429, "rate_limit_error"), "rate", "Tunggu"),
            (error(402, "billing_error"), "billing", "Billing"),
            (error(529, "overloaded_error"), "overloaded", "sibuk"),
            (error(400, "invalid_request_error"), "bad_request", "400"),
        ]
        for answer, code, hint in cases:
            with self.subTest(code=code):
                self.fake.answers.append(answer)
                status, data = self.request("POST", "/api/ai/test", {})
                self.assertEqual(status, 502, data)
                self.assertEqual(data["code"], code)
                self.assertIn(hint, data["error"])

    def test_no_internet(self):
        with mock.patch.dict(os.environ, {"ANTHROPIC_BASE_URL": "http://127.0.0.1:9"}):
            status, data = self.request("POST", "/api/ai/test", {})
        self.assertEqual((status, data["code"]), (502, "network"))
        self.assertIn("internet", data["error"])
        # Aplikasi tetap berjalan.
        self.assertEqual(self.request("POST", "/api/tasks", {"title": "Tetap jalan"})[0], 201)
