"""Membaca file .env (pengaturan rahasia seperti API key) ke variabel lingkungan.

Format file .env: satu pengaturan per baris, misalnya
    ANTHROPIC_API_KEY=sk-ant-...
Baris kosong dan baris yang diawali # diabaikan.

Variabel yang sudah diatur di luar (misalnya lewat terminal) tidak ditimpa.
File .env tidak pernah ikut ke Git (lihat .gitignore).
"""

import os

from app.db import PROJECT_DIR

ENV_FILE = PROJECT_DIR / ".env"


def parse_env(text):
    """Ubah isi file .env menjadi dict."""
    values = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key.startswith("export "):
            key = key[len("export "):].strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if key:
            values[key] = value
    return values


def load_env(path=ENV_FILE):
    """Baca file .env bila ada. Hasil: daftar nama variabel yang dimuat (tanpa nilainya)."""
    try:
        text = path.read_text(encoding="utf-8-sig")  # -sig: aman untuk file dari Notepad Windows
    except FileNotFoundError:
        return []
    loaded = []
    for key, value in parse_env(text).items():
        if key not in os.environ:
            os.environ[key] = value
            loaded.append(key)
    return loaded
