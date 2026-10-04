"""API pengaturan aplikasi.

    GET    /api/settings          semua pengaturan (nilai bawaan bila belum pernah diubah)
    PATCH  /api/settings          ubah satu atau beberapa pengaturan

Untuk fitur baru yang butuh pengaturan: tambahkan entri di SETTINGS.
"""

import json

from app.db import connection
from app.router import ApiError, route


def whole_number(label, minimum, maximum):
    """Pemeriksa untuk angka bulat dalam rentang tertentu."""

    def check(value):
        if not isinstance(value, int) or isinstance(value, bool) or not minimum <= value <= maximum:
            raise ApiError(400, f"{label} harus angka bulat {minimum}–{maximum}.")
        return value

    return check


# nama pengaturan -> (nilai bawaan, fungsi pemeriksa)
SETTINGS = {
    "focus_work_minutes": (25, whole_number("Durasi fokus (menit)", 1, 180)),
    "focus_break_minutes": (5, whole_number("Durasi istirahat (menit)", 1, 60)),
}


def read_settings(conn):
    stored = {row["key"]: json.loads(row["value"]) for row in conn.execute("SELECT key, value FROM settings")}
    return {key: stored.get(key, default) for key, (default, _) in SETTINGS.items()}


@route("GET", "/api/settings")
def get_settings(req):
    with connection() as conn:
        return read_settings(conn)


@route("PATCH", "/api/settings")
def update_settings(req):
    if not isinstance(req.body, dict) or not req.body:
        raise ApiError(400, "Data pengaturan tidak valid.")
    cleaned = {}
    for key, value in req.body.items():
        if key not in SETTINGS:
            raise ApiError(400, f"Pengaturan '{key}' tidak dikenal.")
        cleaned[key] = SETTINGS[key][1](value)

    with connection() as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            [(key, json.dumps(value)) for key, value in cleaned.items()],
        )
        return read_settings(conn)
