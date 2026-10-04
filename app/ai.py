"""Fondasi fitur AI (Claude API dari Anthropic).

Aturan yang dijaga di sini:
- Semua panggilan ke Claude dilakukan dari server. API key dibaca dari variabel
  lingkungan ANTHROPIC_API_KEY (diisi lewat file .env) dan tidak pernah dikirim
  ke browser.
- Fitur AI tidak dipakai bila: dimatikan di Pengaturan, API key kosong, paket
  `anthropic` belum terpasang, atau batas pemakaian bulanan sudah tercapai.
  Dalam semua keadaan itu aplikasi tetap berjalan normal; hanya fitur AI yang
  menampilkan pesan.
- Fungsi di sini hanya MEMINTA jawaban. Tidak ada yang mengubah data aplikasi;
  setiap hasil AI harus disetujui pengguna dulu di tampilan.
- Yang dicatat hanya jumlah token dan perkiraan biaya per bulan, bukan isi
  pertanyaan atau jawaban.

Fitur lain memakai fungsi ask(). Contoh:

    result = ai.ask("simple", system="...", messages=[{"role": "user", "content": "..."}],
                    max_tokens=1000, schema={...})
    result.data   # hasil JSON (bila schema diisi)
"""

import json
import os
import sys
import threading
from dataclasses import dataclass
from datetime import date

from app import ai_models
from app.api.settings import read_settings
from app.db import connection
from app.router import ApiError

TIMEOUT_SECONDS = 120
MAX_RETRIES = 2  # SDK mencoba ulang otomatis untuk gangguan sementara (jaringan, server sibuk)
FALLBACK_BETA = "server-side-fallback-2026-07-01"
MIN_PYTHON = (3, 10)

_usage_lock = threading.Lock()


class AiError(ApiError):
    """Kesalahan fitur AI, dengan pesan berbahasa Indonesia yang bisa ditampilkan."""

    def __init__(self, message, code, status=503):
        super().__init__(status, message, code)


@dataclass
class AiResult:
    text: str
    data: object  # hasil JSON bila memakai schema, selain itu None
    model: str
    cost_usd: float
    input_tokens: int
    output_tokens: int

    def as_json(self):
        """Bentuk yang dikirim ke tampilan. "source": "ai" menandai ini sebagai usulan AI."""
        return {
            "source": "ai",
            "model": self.model,
            "cost_usd": round(self.cost_usd, 6),
            "text": self.text,
            "data": self.data,
        }


# ----- Keadaan fitur AI -----

def api_key():
    return os.environ.get("ANTHROPIC_API_KEY", "").strip()


def sdk_status():
    """Hasil: (terpasang?, versi)."""
    try:
        import anthropic
    except ImportError:
        return False, None
    return True, getattr(anthropic, "__version__", "?")


def python_ok():
    return sys.version_info >= MIN_PYTHON


def _problem(settings):
    """Alasan AI belum bisa dipakai (code, pesan), atau None bila siap."""
    if not settings["ai_enabled"]:
        return "disabled", "Fitur AI sedang dimatikan. Nyalakan di halaman Pengaturan."
    if not python_ok():
        return "old_python", (
            f"Fitur AI butuh Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} atau lebih baru "
            f"(yang terpasang {sys.version_info[0]}.{sys.version_info[1]})."
        )
    if not sdk_status()[0]:
        return "no_sdk", (
            "Paket 'anthropic' belum terpasang. Jalankan: python3 -m pip install -r requirements.txt, "
            "lalu jalankan ulang aplikasi."
        )
    if not api_key():
        return "no_key", "API key belum diisi. Isi ANTHROPIC_API_KEY di file .env, lalu jalankan ulang aplikasi."
    return None


# ----- Catatan pemakaian bulanan -----

def month_key(today=None):
    return (today or date.today()).strftime("%Y-%m")


def read_usage(conn, month):
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (f"ai_usage:{month}",)).fetchone()
    usage = {"requests": 0, "failed": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}
    if row:
        usage.update(json.loads(row["value"]))
    return usage


def record_usage(month, cost=0.0, input_tokens=0, output_tokens=0, failed=False):
    with _usage_lock, connection() as conn:
        usage = read_usage(conn, month)
        usage["requests"] += 1
        usage["failed"] += int(failed)
        usage["input_tokens"] += input_tokens
        usage["output_tokens"] += output_tokens
        usage["cost_usd"] = round(usage["cost_usd"] + cost, 6)
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (f"ai_usage:{month}", json.dumps(usage)),
        )


def status():
    """Keadaan fitur AI untuk halaman Pengaturan. API key TIDAK ikut dikirim, hanya ada/tidaknya."""
    month = month_key()
    with connection() as conn:
        settings = read_settings(conn)
        usage = read_usage(conn, month)
    installed, version = sdk_status()
    problem = _problem(settings)
    limit = settings["ai_monthly_limit_usd"]
    return {
        "enabled": settings["ai_enabled"],
        "ready": problem is None,
        "problem": {"code": problem[0], "message": problem[1]} if problem else None,
        "key_configured": bool(api_key()),
        "sdk_installed": installed,
        "sdk_version": version,
        "python_ok": python_ok(),
        "models": [
            {"id": model_id, "label": info["label"], "input": info["input"], "output": info["output"]}
            for model_id, info in ai_models.MODELS.items()
        ],
        "tiers": {
            name: {"label": tier["label"], "model": settings[tier["setting"]]}
            for name, tier in ai_models.TIERS.items()
        },
        "usage": {"month": month, **usage},
        "limit_usd": limit,
        "remaining_usd": round(max(0.0, limit - usage["cost_usd"]), 4),
    }


# ----- Memanggil Claude -----

def _make_client():
    import anthropic

    return anthropic.Anthropic(api_key=api_key(), timeout=TIMEOUT_SECONDS, max_retries=MAX_RETRIES)


def _measure(response):
    """Hitung token & perkiraan biaya dari jawaban. Hasil: (biaya, token_masuk, token_keluar)."""
    usage = response.usage
    parts = getattr(usage, "iterations", None) or [usage]  # beberapa model bila ada cadangan (fallback)
    cost = 0.0
    tokens_in = tokens_out = 0
    for part in parts:
        model = getattr(part, "model", None) or response.model
        t_in = part.input_tokens or 0
        t_out = part.output_tokens or 0
        cost += ai_models.cost_usd(
            model, t_in, t_out,
            cache_read_tokens=getattr(part, "cache_read_input_tokens", 0) or 0,
            cache_write_tokens=getattr(part, "cache_creation_input_tokens", 0) or 0,
        )
        tokens_in += t_in
        tokens_out += t_out
    return cost, tokens_in, tokens_out


def _translate(error, model):
    """Ubah error dari SDK menjadi AiError dengan pesan yang jelas."""
    try:
        import anthropic
    except ImportError:
        return AiError("Terjadi kesalahan saat menghubungi layanan AI.", "error", 502)

    if isinstance(error, anthropic.AuthenticationError):
        return AiError("API key ditolak oleh Anthropic. Periksa isi ANTHROPIC_API_KEY di file .env.", "auth", 502)
    if isinstance(error, anthropic.PermissionDeniedError):
        return AiError("API key ini tidak punya izin untuk permintaan tersebut.", "auth", 502)
    if isinstance(error, anthropic.NotFoundError):
        return AiError(f"Model {model} tidak tersedia. Pilih model lain di halaman Pengaturan.", "model", 502)
    if isinstance(error, anthropic.RateLimitError):
        return AiError("Terlalu banyak permintaan ke AI dalam waktu singkat. Tunggu sebentar, lalu coba lagi.", "rate", 502)
    if isinstance(error, anthropic.APIStatusError):
        if error.status_code == 402 or getattr(error, "type", None) == "billing_error":
            return AiError("Kredit akun Anthropic Anda habis. Isi ulang di platform.claude.com (menu Billing).", "billing", 502)
        if error.status_code >= 500:
            return AiError("Layanan AI sedang sibuk atau bermasalah. Coba lagi beberapa saat lagi.", "overloaded", 502)
        return AiError(f"Permintaan ke AI ditolak ({error.status_code}).", "bad_request", 502)
    if isinstance(error, anthropic.APITimeoutError):
        return AiError("Layanan AI tidak menjawab tepat waktu. Coba lagi.", "network", 502)
    if isinstance(error, anthropic.APIConnectionError):
        return AiError("Tidak bisa terhubung ke layanan AI. Periksa koneksi internet.", "network", 502)
    return AiError("Terjadi kesalahan saat menghubungi layanan AI.", "error", 502)


def ask(tier, *, system, messages, max_tokens, schema=None, effort=None):
    """Kirim satu permintaan ke Claude. Hasil: AiResult. Gagal: AiError.

    tier    "simple" (model kecil & murah) atau "smart" (model untuk perencanaan & asisten)
    schema  JSON Schema bila jawaban harus berupa data terstruktur
    effort  "low" | "medium" | "high" (diabaikan pada model yang tidak mendukungnya)

    Kirim hanya data yang dibutuhkan untuk permintaan ini, jangan seluruh database.
    """
    month = month_key()
    with connection() as conn:
        settings = read_settings(conn)
        spent = read_usage(conn, month)["cost_usd"]

    problem = _problem(settings)
    if problem:
        raise AiError(problem[1], problem[0])
    limit = settings["ai_monthly_limit_usd"]
    if spent >= limit:
        raise AiError(
            f"Batas pemakaian AI bulan ini (${limit:.2f}) sudah tercapai. "
            "Fitur AI aktif lagi awal bulan depan, atau naikkan batasnya di Pengaturan.",
            "limit",
            429,
        )

    model = settings[ai_models.TIERS[tier]["setting"]]
    info = ai_models.MODELS[model]
    request = {"model": model, "max_tokens": max_tokens, "system": system, "messages": messages}
    output_config = {}
    if schema is not None:
        output_config["format"] = {"type": "json_schema", "schema": schema}
    if effort and info["effort"]:
        output_config["effort"] = effort
    if output_config:
        request["output_config"] = output_config

    try:
        client = _make_client()
        if info["fallback"]:
            # Bila model utama menolak karena aturan keamanan, Anthropic otomatis
            # meneruskan permintaan ke model cadangan yang sesuai.
            response = client.beta.messages.create(betas=[FALLBACK_BETA], fallbacks="default", **request)
        else:
            response = client.messages.create(**request)
    except Exception as error:  # semua kegagalan SDK diterjemahkan, aplikasi tetap jalan
        record_usage(month, failed=True)
        raise _translate(error, model)

    cost, tokens_in, tokens_out = _measure(response)
    record_usage(month, cost, tokens_in, tokens_out, failed=response.stop_reason in ("refusal", "max_tokens"))

    if response.stop_reason == "refusal":
        raise AiError("AI menolak menjawab permintaan ini.", "refused", 502)
    if response.stop_reason == "max_tokens":
        raise AiError("Jawaban AI terpotong karena terlalu panjang. Coba lagi.", "truncated", 502)

    text = "".join(block.text for block in response.content if block.type == "text").strip()
    data = None
    if schema is not None:
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            raise AiError("Jawaban AI tidak bisa dibaca. Coba lagi.", "bad_output", 502)
    return AiResult(text, data, response.model, cost, tokens_in, tokens_out)
