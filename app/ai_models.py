"""Daftar model Claude yang bisa dipilih, beserta harganya.

Sumber: dokumentasi resmi Anthropic (platform.claude.com/docs, "Models overview"
dan "Pricing"), diperiksa 4 Oktober 2026. Harga dalam dolar AS per 1 juta token.
Bila Anthropic mengubah harga atau model baru keluar, cukup perbarui file ini.
"""

# id model -> keterangan
MODELS = {
    "claude-haiku-4-5": {
        "label": "Haiku 4.5 — tercepat & termurah",
        "input": 1.00, "output": 5.00, "cache_read": 0.10,
        "effort": False,     # parameter effort tidak didukung
        "fallback": False,   # cadangan otomatis (fallbacks) tidak dipakai
    },
    "claude-sonnet-5-5": {
        "label": "Sonnet 5.5 — seimbang",
        "input": 2.00, "output": 10.00, "cache_read": 0.20,
        "effort": True,
        "fallback": True,
    },
    "claude-opus-5-5": {
        "label": "Opus 5.5 — paling cerdas",
        "input": 4.00, "output": 20.00, "cache_read": 0.20,
        "effort": True,
        "fallback": True,
    },
}

# Model yang mungkin menjawab sebagai "cadangan" bila model utama menolak
# (fitur fallbacks). Hanya untuk menghitung perkiraan biaya.
FALLBACK_PRICES = {
    "claude-opus-4-8": {"input": 5.00, "output": 25.00, "cache_read": 0.50},
    "claude-opus-5": {"input": 5.00, "output": 25.00, "cache_read": 0.50},
    "claude-sonnet-5": {"input": 2.00, "output": 10.00, "cache_read": 0.20},
}

# Dua jenis pekerjaan AI, masing-masing dengan model sendiri (bisa diganti di Pengaturan).
TIERS = {
    "simple": {"setting": "ai_model_simple", "default": "claude-haiku-4-5",
               "label": "Tugas sederhana (misalnya menafsirkan input cepat)"},
    "smart": {"setting": "ai_model_smart", "default": "claude-opus-5-5",
              "label": "Perencanaan & asisten"},
}

CACHE_WRITE_MULTIPLIER = 1.25  # menulis ke cache: 1,25x harga input


def price_of(model):
    """Harga per 1 juta token untuk model ini (model tak dikenal: pakai harga termahal yang dikenal)."""
    if model in MODELS:
        return MODELS[model]
    for known, prices in FALLBACK_PRICES.items():
        if model.startswith(known):
            return prices
    return {"input": 10.00, "output": 50.00, "cache_read": 1.00}


def cost_usd(model, input_tokens=0, output_tokens=0, cache_read_tokens=0, cache_write_tokens=0):
    """Perkiraan biaya (dolar AS) untuk sejumlah token."""
    p = price_of(model)
    return (
        input_tokens * p["input"]
        + output_tokens * p["output"]
        + cache_read_tokens * p["cache_read"]
        + cache_write_tokens * p["input"] * CACHE_WRITE_MULTIPLIER
    ) / 1_000_000
