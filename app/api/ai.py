"""API fitur AI.

    GET    /api/ai/status     keadaan fitur AI & pemakaian bulan ini (tanpa API key)
    POST   /api/ai/test       uji koneksi dengan satu permintaan kecil  {"tier": "simple" | "smart"}

Pengaturan AI (nyala/mati, model, batas bulanan) diubah lewat /api/settings.
Logikanya ada di app/ai.py.
"""

from app import ai
from app.ai_models import TIERS
from app.router import ApiError, route


@route("GET", "/api/ai/status")
def get_status(req):
    return ai.status()


@route("POST", "/api/ai/test")
def test_connection(req):
    tier = (req.body or {}).get("tier", "simple") if isinstance(req.body, dict) else "simple"
    if tier not in TIERS:
        raise ApiError(400, "Jenis model tidak dikenal.")
    result = ai.ask(
        tier,
        system="Anda adalah bagian dari aplikasi produktivitas pribadi berbahasa Indonesia.",
        messages=[{
            "role": "user",
            "content": "Ini uji koneksi. Balas dengan satu kalimat singkat berbahasa Indonesia "
                       "yang menyatakan koneksi berhasil.",
        }],
        max_tokens=2000,  # model dengan "thinking" butuh ruang untuk berpikir sebelum menjawab
        effort="low",
    )
    return result.as_json()
