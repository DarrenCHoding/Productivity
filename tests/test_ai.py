"""Tes fondasi fitur AI dengan "Claude tiruan": tidak ada panggilan ke API sungguhan."""

import json
import os
import subprocess
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest import mock

from app import ai, env
from app.ai_models import cost_usd
from tests.helpers import ApiTestCase

PROJECT_DIR = Path(__file__).resolve().parent.parent
FAKE_KEY = "sk-ant-api03-RAHASIA-JANGAN-BOCOR"


def reply(text="Koneksi berhasil.", model="claude-haiku-4-5", input_tokens=100, output_tokens=50,
          stop_reason="end_turn", iterations=None):
    """Bentuk jawaban seperti yang dikembalikan SDK anthropic."""
    usage = NS(input_tokens=input_tokens, output_tokens=output_tokens,
               cache_read_input_tokens=0, cache_creation_input_tokens=0, iterations=iterations)
    return NS(content=[NS(type="text", text=text)], model=model, usage=usage, stop_reason=stop_reason)


class FakeClaude:
    """Pengganti klien SDK: mencatat permintaan, mengembalikan jawaban yang sudah disiapkan."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []
        self.messages = NS(create=self._create("messages"))
        self.beta = NS(messages=NS(create=self._create("beta")))

    def _create(self, kind):
        def create(**request):
            self.calls.append((kind, request))
            answer = self.replies.pop(0)
            if isinstance(answer, Exception):
                raise answer
            return answer
        return create


class AiTestCase(ApiTestCase):
    def use_claude(self, *replies, key=FAKE_KEY, sdk=True):
        """Pasang Claude tiruan, API key tiruan, dan (pura-pura) SDK terpasang."""
        fake = FakeClaude(replies)
        for patcher in (
            mock.patch.object(ai, "_make_client", lambda: fake),
            mock.patch.object(ai, "sdk_status", lambda: (sdk, "tiruan" if sdk else None)),
            mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": key}),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        return fake

    def settings(self, **values):
        status, data = self.request("PATCH", "/api/settings", values)
        self.assertEqual(status, 200, data)
        return data

    def enable(self, **values):
        return self.settings(ai_enabled=True, **values)

    def usage(self):
        return self.request("GET", "/api/ai/status")[1]["usage"]


class SafetyNetTest(unittest.TestCase):
    def test_tests_can_never_reach_the_real_api(self):
        self.assertEqual(os.environ["ANTHROPIC_API_KEY"], "")
        self.assertTrue(os.environ["ANTHROPIC_BASE_URL"].startswith("http://127.0.0.1:"))


class AiSettingsTest(AiTestCase):
    def test_off_by_default(self):
        status = self.request("GET", "/api/ai/status")[1]
        self.assertFalse(status["enabled"])
        self.assertFalse(status["ready"])
        self.assertEqual(status["problem"]["code"], "disabled")
        self.assertEqual(status["tiers"]["simple"]["model"], "claude-haiku-4-5")
        self.assertEqual(status["tiers"]["smart"]["model"], "claude-opus-5-5")
        self.assertEqual(status["limit_usd"], 5.0)

    def test_change_settings(self):
        data = self.settings(ai_enabled=True, ai_model_simple="claude-sonnet-5-5", ai_monthly_limit_usd=2.5)
        self.assertTrue(data["ai_enabled"])
        self.assertEqual(data["ai_model_simple"], "claude-sonnet-5-5")
        self.assertEqual(data["ai_monthly_limit_usd"], 2.5)

    def test_invalid_settings(self):
        for body in (
            {"ai_enabled": "ya"},
            {"ai_model_smart": "gpt-4"},
            {"ai_model_simple": "claude-3-haiku-20240307"},
            {"ai_monthly_limit_usd": 0},
            {"ai_monthly_limit_usd": 1000},
            {"ai_monthly_limit_usd": "5"},
        ):
            self.assertEqual(self.request("PATCH", "/api/settings", body)[0], 400, body)

    def test_api_key_never_sent_to_browser(self):
        self.use_claude()
        self.enable()
        raw = json.dumps(self.request("GET", "/api/ai/status")[1])
        self.assertNotIn(FAKE_KEY, raw)
        self.assertNotIn("RAHASIA", raw)
        status = json.loads(raw)
        self.assertTrue(status["key_configured"])
        self.assertTrue(status["ready"])


class AiUnavailableTest(AiTestCase):
    def assert_unavailable(self, code):
        status, data = self.request("POST", "/api/ai/test", {})
        self.assertEqual(status, 503, data)
        self.assertEqual(data["code"], code)
        self.assertIn("error", data)
        return data

    def test_disabled(self):
        fake = self.use_claude()
        self.assert_unavailable("disabled")
        self.assertEqual(fake.calls, [])

    def test_no_api_key(self):
        fake = self.use_claude(key="")
        self.enable()
        data = self.assert_unavailable("no_key")
        self.assertIn(".env", data["error"])
        self.assertEqual(fake.calls, [])

    def test_sdk_not_installed(self):
        fake = self.use_claude(sdk=False)
        self.enable()
        data = self.assert_unavailable("no_sdk")
        self.assertIn("requirements.txt", data["error"])
        self.assertEqual(fake.calls, [])

    def test_monthly_limit_reached_blocks_before_calling(self):
        fake = self.use_claude()
        self.enable(ai_monthly_limit_usd=1)
        ai.record_usage(ai.month_key(), cost=1.0)
        status, data = self.request("POST", "/api/ai/test", {})
        self.assertEqual(status, 429)
        self.assertEqual(data["code"], "limit")
        self.assertIn("$1.00", data["error"])
        self.assertEqual(fake.calls, [])

    def test_last_month_usage_does_not_count(self):
        self.use_claude(reply())
        self.enable(ai_monthly_limit_usd=1)
        ai.record_usage("2000-01", cost=99.0)
        self.assertEqual(self.request("POST", "/api/ai/test", {})[0], 200)

    def test_app_keeps_working_when_ai_fails(self):
        self.use_claude(ConnectionError("internet mati"))
        self.enable()
        status, data = self.request("POST", "/api/ai/test", {})
        self.assertEqual(status, 502)
        self.assertEqual(data["code"], "error")
        # Fitur lain tidak terpengaruh.
        self.assertEqual(self.request("POST", "/api/tasks", {"title": "Tetap bisa"})[0], 201)
        self.assertEqual(self.request("GET", "/api/tasks")[0], 200)
        self.assertEqual(self.usage()["failed"], 1)


class AiCallTest(AiTestCase):
    def test_connection_test_succeeds_and_is_marked_as_ai(self):
        self.use_claude(reply("Koneksi berhasil!", input_tokens=100, output_tokens=50))
        self.enable()
        status, data = self.request("POST", "/api/ai/test", {})
        self.assertEqual(status, 200, data)
        self.assertEqual(data["source"], "ai")
        self.assertEqual(data["text"], "Koneksi berhasil!")
        self.assertEqual(data["model"], "claude-haiku-4-5")
        expected = cost_usd("claude-haiku-4-5", 100, 50)
        self.assertAlmostEqual(data["cost_usd"], expected)
        usage = self.usage()
        self.assertEqual((usage["requests"], usage["input_tokens"], usage["output_tokens"]), (1, 100, 50))
        self.assertAlmostEqual(usage["cost_usd"], expected)

    def test_simple_model_request_shape(self):
        fake = self.use_claude(reply())
        self.enable()
        self.request("POST", "/api/ai/test", {"tier": "simple"})
        kind, request = fake.calls[0]
        self.assertEqual(kind, "messages")  # Haiku: tanpa fitur cadangan
        self.assertEqual(request["model"], "claude-haiku-4-5")
        self.assertNotIn("output_config", request)  # Haiku tidak mendukung effort
        self.assertNotIn("fallbacks", request)
        self.assertNotIn("thinking", request)

    def test_smart_model_uses_effort_and_fallbacks(self):
        fake = self.use_claude(reply(model="claude-opus-5-5"))
        self.enable()
        self.request("POST", "/api/ai/test", {"tier": "smart"})
        kind, request = fake.calls[0]
        self.assertEqual(kind, "beta")
        self.assertEqual(request["model"], "claude-opus-5-5")
        self.assertEqual(request["fallbacks"], "default")
        self.assertEqual(request["betas"], ["server-side-fallback-2026-07-01"])
        self.assertEqual(request["output_config"], {"effort": "low"})
        self.assertNotIn("thinking", request)  # Opus 5.5: thinking selalu aktif, tidak boleh dimatikan

    def test_unknown_tier(self):
        self.use_claude()
        self.enable()
        self.assertEqual(self.request("POST", "/api/ai/test", {"tier": "super"})[0], 400)

    def test_structured_output(self):
        fake = self.use_claude(reply('{"judul": "Bayar listrik", "menit": 15}'))
        self.enable()
        schema = {"type": "object", "properties": {"judul": {"type": "string"}, "menit": {"type": "integer"}},
                  "required": ["judul", "menit"], "additionalProperties": False}
        result = ai.ask("simple", system="s", messages=[{"role": "user", "content": "x"}], max_tokens=500, schema=schema)
        self.assertEqual(result.data, {"judul": "Bayar listrik", "menit": 15})
        self.assertEqual(fake.calls[0][1]["output_config"], {"format": {"type": "json_schema", "schema": schema}})

    def test_unreadable_structured_output(self):
        self.use_claude(reply("bukan json"))
        self.enable()
        with self.assertRaises(ai.AiError) as ctx:
            ai.ask("simple", system="s", messages=[{"role": "user", "content": "x"}], max_tokens=500, schema={"type": "object"})
        self.assertEqual(ctx.exception.code, "bad_output")

    def test_refusal_is_reported_and_still_counted(self):
        self.use_claude(reply("", stop_reason="refusal"))
        self.enable()
        status, data = self.request("POST", "/api/ai/test", {})
        self.assertEqual((status, data["code"]), (502, "refused"))
        usage = self.usage()
        self.assertEqual((usage["requests"], usage["failed"]), (1, 1))
        self.assertGreater(usage["cost_usd"], 0)

    def test_truncated_answer(self):
        self.use_claude(reply("Koneksi ber", stop_reason="max_tokens"))
        self.enable()
        status, data = self.request("POST", "/api/ai/test", {})
        self.assertEqual((status, data["code"]), (502, "truncated"))

    def test_cost_counts_every_model_when_a_fallback_answered(self):
        iterations = [
            NS(type="message", model="claude-opus-5-5", input_tokens=1000, output_tokens=10,
               cache_read_input_tokens=0, cache_creation_input_tokens=0),
            NS(type="fallback_message", model="claude-opus-4-8", input_tokens=1000, output_tokens=200,
               cache_read_input_tokens=0, cache_creation_input_tokens=0),
        ]
        self.use_claude(reply(model="claude-opus-4-8", iterations=iterations))
        self.enable()
        data = self.request("POST", "/api/ai/test", {"tier": "smart"})[1]
        expected = cost_usd("claude-opus-5-5", 1000, 10) + cost_usd("claude-opus-4-8", 1000, 200)
        self.assertAlmostEqual(data["cost_usd"], expected)

    def test_reaching_the_limit_mid_month(self):
        self.use_claude(reply(input_tokens=1_000_000, output_tokens=0), reply())
        self.enable(ai_monthly_limit_usd=0.5)
        self.assertEqual(self.request("POST", "/api/ai/test", {})[0], 200)  # biaya $1, melewati batas $0,50
        status = self.request("GET", "/api/ai/status")[1]
        self.assertEqual(status["remaining_usd"], 0)
        self.assertEqual(self.request("POST", "/api/ai/test", {})[1]["code"], "limit")


class CostTest(unittest.TestCase):
    def test_prices_per_million_tokens(self):
        self.assertAlmostEqual(cost_usd("claude-haiku-4-5", 1_000_000, 0), 1.00)
        self.assertAlmostEqual(cost_usd("claude-haiku-4-5", 0, 1_000_000), 5.00)
        self.assertAlmostEqual(cost_usd("claude-sonnet-5-5", 1_000_000, 1_000_000), 12.00)
        self.assertAlmostEqual(cost_usd("claude-opus-5-5", 1_000_000, 1_000_000), 24.00)
        self.assertAlmostEqual(cost_usd("claude-opus-5-5", 0, 0, cache_read_tokens=1_000_000), 0.20)
        self.assertAlmostEqual(cost_usd("claude-opus-5-5", 0, 0, cache_write_tokens=1_000_000), 5.00)

    def test_unknown_model_is_priced_high_not_free(self):
        self.assertGreaterEqual(cost_usd("claude-model-masa-depan", 1_000_000, 0), 4.00)


class EnvFileTest(unittest.TestCase):
    def test_parse(self):
        text = """
# komentar
ANTHROPIC_API_KEY=sk-ant-abc
KUTIP="nilai dengan spasi"
export LAIN='x'
SAMA_DENGAN=a=b
BARIS RUSAK
"""
        self.assertEqual(env.parse_env(text), {
            "ANTHROPIC_API_KEY": "sk-ant-abc",
            "KUTIP": "nilai dengan spasi",
            "LAIN": "x",
            "SAMA_DENGAN": "a=b",
        })

    def test_load_does_not_override_and_reports_names_only(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text("﻿PRODUCTIVITY_TES_BARU=1\nPRODUCTIVITY_TES_ADA=dari-file\n", encoding="utf-8")
            with mock.patch.dict(os.environ, {"PRODUCTIVITY_TES_ADA": "dari-terminal"}):
                loaded = env.load_env(path)
                self.assertEqual(loaded, ["PRODUCTIVITY_TES_BARU"])
                self.assertEqual(os.environ["PRODUCTIVITY_TES_BARU"], "1")
                self.assertEqual(os.environ["PRODUCTIVITY_TES_ADA"], "dari-terminal")
            os.environ.pop("PRODUCTIVITY_TES_BARU", None)

    def test_missing_file_is_fine(self):
        self.assertEqual(env.load_env(Path("/tidak/ada/.env")), [])


class SecretFileTest(unittest.TestCase):
    """File .env tidak boleh pernah ikut ke Git."""

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=PROJECT_DIR, capture_output=True, text=True)

    def setUp(self):
        try:
            if self.git("rev-parse", "--is-inside-work-tree").stdout.strip() != "true":
                self.skipTest("Bukan folder Git.")
        except FileNotFoundError:
            self.skipTest("Git tidak terpasang.")

    def test_env_files_are_ignored(self):
        for name in (".env", ".env.local", ".env.production"):
            self.assertEqual(self.git("check-ignore", "-q", name).returncode, 0, f"{name} harus diabaikan Git")

    def test_example_file_is_not_ignored(self):
        self.assertEqual(self.git("check-ignore", "-q", ".env.example").returncode, 1)

    def test_no_env_file_is_tracked(self):
        tracked = self.git("ls-files").stdout.split()
        self.assertEqual([f for f in tracked if f.split("/")[-1].startswith(".env") and f != ".env.example"], [])

    def test_example_file_contains_no_key(self):
        text = (PROJECT_DIR / ".env.example").read_text(encoding="utf-8")
        self.assertEqual(env.parse_env(text).get("ANTHROPIC_API_KEY"), "")
        self.assertNotIn("sk-ant-", text)
