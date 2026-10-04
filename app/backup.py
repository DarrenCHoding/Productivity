"""Cadangan dan pemulihan data.

- Ekspor: salinan utuh seluruh database dalam satu file .db.
- Pemulihan: mengganti seluruh data dengan isi file cadangan. Sebelum diganti,
  file diperiksa dulu, dan data saat ini dicadangkan ke data/backups/.
- Cadangan harian: sekali sehari salinan database disimpan ke data/backups/,
  dan hanya 7 cadangan harian terakhir yang disimpan.

File cadangan adalah file database SQLite biasa, jadi semua tabel ikut,
termasuk tabel dari fitur yang ditambahkan nanti.
"""

import os
import re
import sqlite3
import tempfile
import threading
import time
import traceback
from datetime import date, datetime
from pathlib import Path

from app import db
from app.router import ApiError

SQLITE_HEADER = b"SQLite format 3\x00"
DAILY_KEEP = 7  # jumlah cadangan harian yang disimpan
DAILY_CHECK_SECONDS = 30 * 60  # seberapa sering diperiksa apakah cadangan hari ini sudah ada
BACKUP_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\.db$")

# Isi yang dihitung untuk ringkasan: nama tabel -> sebutan
SUMMARY_TABLES = {
    "tasks": "tugas",
    "categories": "kategori",
    "focus_sessions": "sesi fokus",
}

# Hanya satu pemulihan boleh berjalan pada satu waktu.
_restore_lock = threading.Lock()


# ----- Ekspor -----

def export_bytes():
    """Salinan utuh database saat ini, sebagai bytes."""
    fd, tmp = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        db.copy_database(db.get_db_path(), tmp)
        return Path(tmp).read_bytes()
    finally:
        os.remove(tmp)


def export_filename():
    return f"productivity-cadangan-{datetime.now():%Y-%m-%d-%H%M}.db"


# ----- Pemeriksaan file cadangan -----

def inspect_backup(path):
    """Periksa apakah file layak dipulihkan. Hasil: ringkasan isinya.

    Melempar ApiError dengan penjelasan bila file tidak bisa dipakai.
    """
    with open(path, "rb") as f:
        if f.read(16) != SQLITE_HEADER:
            raise ApiError(400, "File ini bukan file cadangan Productivity.")

    conn = sqlite3.connect(path)
    try:
        try:
            integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
            tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
            version = conn.execute("PRAGMA user_version").fetchone()[0]
        except sqlite3.DatabaseError:
            raise ApiError(400, "File cadangan rusak dan tidak bisa dibaca.")
        if integrity != "ok":
            raise ApiError(400, "File cadangan rusak dan tidak bisa dibaca.")
        if "tasks" not in tables or version < 1:
            raise ApiError(400, "File ini bukan file cadangan Productivity.")
        if version > len(db.MIGRATIONS):
            raise ApiError(
                400,
                "File cadangan ini dibuat oleh versi aplikasi yang lebih baru. "
                "Perbarui aplikasi dulu (git pull), lalu coba lagi.",
            )
        counts = {
            table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in SUMMARY_TABLES
            if table in tables
        }
    finally:
        conn.close()
    return {"version": version, "counts": counts}


def describe_counts(counts):
    """{'tasks': 12, 'categories': 3} -> '12 tugas, 3 kategori'."""
    return ", ".join(f"{counts[t]} {label}" for t, label in SUMMARY_TABLES.items() if t in counts)


# ----- Pemulihan -----

def restore_from_file(path):
    """Ganti seluruh data dengan isi file cadangan di `path`."""
    with _restore_lock:
        info = inspect_backup(path)
        safety = db.backup_database("sebelum-pemulihan")
        db.copy_database(path, db.get_db_path())
        # Cadangan dari versi aplikasi yang lebih lama: perbarui strukturnya.
        db.init_db(make_backup=False)
    return {
        "counts": info["counts"],
        "summary": describe_counts(info["counts"]),
        "safety_backup": safety.name,
    }


def restore_upload(raw):
    """Pulihkan dari file yang diunggah dari browser."""
    if not raw:
        raise ApiError(400, "Pilih file cadangan dulu.")
    folder = db.get_db_path().parent
    fd, tmp = tempfile.mkstemp(dir=folder, prefix="unggahan-", suffix=".db")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(raw)
        return restore_from_file(tmp)
    finally:
        os.remove(tmp)


def find_backup(name):
    """Cari file di folder cadangan berdasarkan namanya (tanpa folder)."""
    folder = db.get_backup_dir()
    if not isinstance(name, str) or not BACKUP_NAME.match(name):
        raise ApiError(404, "Cadangan tidak ditemukan.")
    path = folder / name
    if not path.is_file():
        raise ApiError(404, "Cadangan tidak ditemukan.")
    return path


# ----- Daftar cadangan otomatis -----

def backup_kind(name):
    if "-harian-" in name:
        return "harian"
    if name.endswith("-sebelum-pemulihan.db"):
        return "sebelum-pemulihan"
    if re.search(r"-sebelum-v\d+\.db$", name):
        return "sebelum-pembaruan"
    return "lainnya"


def list_backups():
    folder = db.get_backup_dir()
    files = sorted(folder.glob("*.db"), key=lambda p: p.stat().st_mtime, reverse=True) if folder.is_dir() else []
    return {
        "folder": str(folder),
        "files": [
            {
                "name": p.name,
                "kind": backup_kind(p.name),
                "size": p.stat().st_size,
                "created_at": datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds"),
            }
            for p in files
        ],
    }


# ----- Cadangan harian -----

def daily_backup_path(day):
    return db.get_backup_dir() / f"{db.get_db_path().stem}-harian-{day.isoformat()}.db"


def ensure_daily_backup(today=None):
    """Buat cadangan hari ini bila belum ada, lalu hapus cadangan harian yang terlalu lama.

    Hasil: lokasi cadangan baru, atau None bila hari ini sudah ada cadangannya.
    """
    today = today or date.today()
    if not db.get_db_path().exists():
        return None
    target = daily_backup_path(today)
    created = None
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        # Ditulis ke file sementara dulu, supaya file yang setengah jadi tidak
        # pernah terlihat seperti cadangan.
        tmp = target.with_name(target.name + ".tmp")
        db.copy_database(db.get_db_path(), tmp)
        os.replace(tmp, target)
        created = target
    prune_daily_backups()
    return created


def prune_daily_backups(keep=DAILY_KEEP):
    """Simpan hanya `keep` cadangan harian terbaru. Cadangan jenis lain tidak disentuh."""
    pattern = f"{db.get_db_path().stem}-harian-*.db"
    daily = sorted(db.get_backup_dir().glob(pattern))  # nama berisi tanggal, jadi urut menurut tanggal
    for old in daily[:-keep]:
        old.unlink()


def start_daily_backups(on_created=None):
    """Jalankan pemeriksaan cadangan harian di latar belakang selama server hidup."""

    def loop():
        while True:
            try:
                created = ensure_daily_backup()
                if created and on_created:
                    on_created(created)
            except Exception:
                traceback.print_exc()
            time.sleep(DAILY_CHECK_SECONDS)

    threading.Thread(target=loop, name="cadangan-harian", daemon=True).start()
