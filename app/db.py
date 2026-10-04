"""Koneksi ke database SQLite dan pembuatan/pembaruan tabel.

Seluruh data aplikasi disimpan di satu file SQLite (default: data/productivity.db).

Struktur tabel dikelola lewat daftar MIGRATIONS di bawah. Setiap kali fitur
baru butuh tabel/kolom baru, TAMBAHKAN satu entri baru di akhir daftar
(jangan ubah entri lama). Saat server dijalankan, migrasi yang belum pernah
dijalankan akan dijalankan otomatis, dan data lama tetap aman.
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = PROJECT_DIR / "data" / "productivity.db"

# Lokasi file database. Bisa diganti lewat variabel lingkungan PRODUCTIVITY_DB.
_db_path = Path(os.environ.get("PRODUCTIVITY_DB", DEFAULT_DB_PATH))


# Daftar perubahan struktur database, berurutan. Nomor versi = posisi di daftar.
MIGRATIONS = [
    # 1: tabel tugas
    """
    CREATE TABLE tasks (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        title        TEXT    NOT NULL,
        done         INTEGER NOT NULL DEFAULT 0,
        created_at   TEXT    NOT NULL,
        updated_at   TEXT    NOT NULL,
        completed_at TEXT
    );
    """,
    # 2: tanggal jatuh tempo (opsional) dan prioritas
    """
    ALTER TABLE tasks ADD COLUMN due_date TEXT;
    ALTER TABLE tasks ADD COLUMN priority TEXT NOT NULL DEFAULT 'normal'
        CHECK (priority IN ('normal', 'high'));
    CREATE INDEX idx_tasks_due_date ON tasks (due_date);
    """,
]


def now():
    """Waktu lokal saat ini, contoh: '2026-10-04T14:30:00'."""
    return datetime.now().isoformat(timespec="seconds")


def set_db_path(path):
    global _db_path
    _db_path = Path(path)


def get_db_path():
    return _db_path


def connect():
    """Buka koneksi baru ke database. Hasil query bisa diakses seperti dict."""
    conn = sqlite3.connect(_db_path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def connection():
    """Pakai dengan `with connection() as conn:`.

    Perubahan disimpan otomatis bila tidak ada error (dibatalkan bila ada),
    lalu koneksi ditutup.
    """
    conn = connect()
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_db():
    """Buat folder & file database bila belum ada, lalu jalankan migrasi yang tertunda."""
    _db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = connect()
    try:
        current = conn.execute("PRAGMA user_version").fetchone()[0]
        for version, script in enumerate(MIGRATIONS, start=1):
            if version <= current:
                continue
            # Satu migrasi dijalankan utuh atau tidak sama sekali.
            conn.executescript(
                f"BEGIN;\n{script}\nPRAGMA user_version = {version};\nCOMMIT;"
            )
    finally:
        conn.close()
