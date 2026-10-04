"""Koneksi ke database SQLite dan pembuatan/pembaruan tabel.

Seluruh data aplikasi disimpan di satu file SQLite (default: data/productivity.db).

Struktur tabel dikelola lewat daftar MIGRATIONS di bawah. Setiap kali fitur
baru butuh tabel/kolom baru, TAMBAHKAN satu entri baru di akhir daftar
(jangan ubah entri lama). Saat server dijalankan, migrasi yang belum pernah
dijalankan akan dijalankan otomatis, dan data lama tetap aman.

Sebelum migrasi dijalankan pada database yang sudah berisi, salinan cadangan
file database dibuat dulu di folder data/backups/.
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
    # 3: kategori. Bila kategori dihapus, tugasnya tetap ada tanpa kategori.
    """
    CREATE TABLE categories (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        name       TEXT NOT NULL UNIQUE COLLATE NOCASE,
        created_at TEXT NOT NULL
    );
    ALTER TABLE tasks ADD COLUMN category_id INTEGER
        REFERENCES categories (id) ON DELETE SET NULL;
    CREATE INDEX idx_tasks_category ON tasks (category_id);
    """,
    # 4: timer fokus. Setiap sesi fokus dicatat; total waktu fokus per tugas
    #    dihitung dari sini. Bila tugas dihapus, riwayat sesinya tetap ada.
    #    Tabel settings menyimpan pengaturan aplikasi (misalnya durasi timer).
    """
    CREATE TABLE focus_sessions (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id          INTEGER REFERENCES tasks (id) ON DELETE SET NULL,
        started_at       TEXT    NOT NULL,
        ended_at         TEXT    NOT NULL,
        duration_seconds INTEGER NOT NULL CHECK (duration_seconds > 0),
        completed        INTEGER NOT NULL DEFAULT 1
    );
    CREATE INDEX idx_focus_sessions_task ON focus_sessions (task_id);
    CREATE INDEX idx_focus_sessions_ended ON focus_sessions (ended_at);

    CREATE TABLE settings (
        key   TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );
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


def get_backup_dir():
    """Folder cadangan: data/backups/ (di sebelah file database)."""
    return _db_path.parent / "backups"


def copy_database(source_path, target_path):
    """Salin isi satu database SQLite ke database lain.

    Memakai fitur backup bawaan SQLite, sehingga salinannya selalu utuh walaupun
    aplikasi sedang dipakai. Isi database tujuan diganti seluruhnya.
    """
    source = sqlite3.connect(source_path, timeout=10)
    target = sqlite3.connect(target_path, timeout=10)
    try:
        source.backup(target)
    finally:
        target.close()
        source.close()


def backup_database(label):
    """Salin file database ke data/backups/. Hasil: lokasi file cadangan."""
    backup_dir = get_backup_dir()
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = backup_dir / f"{_db_path.stem}-{stamp}-{label}.db"
    copy_database(_db_path, target)
    return target


def init_db(make_backup=True):
    """Buat folder & file database bila belum ada, lalu jalankan migrasi yang tertunda.

    Hasil: lokasi file cadangan bila migrasi dijalankan pada database lama,
    atau None bila tidak ada yang perlu dicadangkan.
    """
    _db_path.parent.mkdir(parents=True, exist_ok=True)
    backup = None
    conn = connect()
    try:
        current = conn.execute("PRAGMA user_version").fetchone()[0]
        if make_backup and 0 < current < len(MIGRATIONS):
            backup = backup_database(f"sebelum-v{len(MIGRATIONS)}")
        for version, script in enumerate(MIGRATIONS, start=1):
            if version <= current:
                continue
            # Satu migrasi dijalankan utuh atau tidak sama sekali.
            conn.executescript(
                f"BEGIN;\n{script}\nPRAGMA user_version = {version};\nCOMMIT;"
            )
    finally:
        conn.close()
    return backup
