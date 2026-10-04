import sqlite3
import tempfile
import unittest
from pathlib import Path

from app import db


class MigrationTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = db.get_db_path()
        self.path = Path(self._tmp.name) / "sub" / "test.db"
        db.set_db_path(self.path)

    def tearDown(self):
        db.set_db_path(self._old)
        self._tmp.cleanup()

    def version(self):
        conn = sqlite3.connect(self.path)
        try:
            return conn.execute("PRAGMA user_version").fetchone()[0]
        finally:
            conn.close()

    def test_creates_folder_and_runs_all_migrations(self):
        backup = db.init_db()
        self.assertTrue(self.path.exists())
        self.assertEqual(self.version(), len(db.MIGRATIONS))
        self.assertIsNone(backup)  # database baru: tidak perlu cadangan

    def test_init_twice_is_safe(self):
        db.init_db()
        self.assertIsNone(db.init_db())  # tidak ada migrasi baru: tidak perlu cadangan
        self.assertEqual(self.version(), len(db.MIGRATIONS))

    def test_upgrade_keeps_existing_data(self):
        # Buat database versi 1 (seperti setelah langkah 1), isi data, lalu upgrade.
        self.path.parent.mkdir(parents=True)
        conn = sqlite3.connect(self.path)
        conn.executescript(db.MIGRATIONS[0] + "PRAGMA user_version = 1;")
        conn.execute(
            "INSERT INTO tasks (title, created_at, updated_at) VALUES ('Lama', '2026-01-01T00:00:00', '2026-01-01T00:00:00')"
        )
        conn.commit()
        conn.close()

        db.init_db()
        with db.connection() as conn:
            row = conn.execute("SELECT * FROM tasks").fetchone()
        self.assertEqual(row["title"], "Lama")
        self.assertEqual(row["priority"], "normal")
        self.assertIsNone(row["due_date"])

    def test_backup_before_migrating_existing_data(self):
        # Database versi 3 (akhir tahap 1) yang sudah berisi data.
        self.path.parent.mkdir(parents=True)
        conn = sqlite3.connect(self.path)
        for version, script in enumerate(db.MIGRATIONS[:3], start=1):
            conn.executescript(script + f"PRAGMA user_version = {version};")
        conn.execute("INSERT INTO categories (name, created_at) VALUES ('Kerja', '2026-01-01T00:00:00')")
        conn.execute(
            "INSERT INTO tasks (title, created_at, updated_at, due_date, priority, category_id)"
            " VALUES ('Laporan', '2026-01-01T00:00:00', '2026-01-01T00:00:00', '2026-02-01', 'high', 1)"
        )
        conn.commit()
        conn.close()

        backup = db.init_db()

        # Cadangan berisi data lama, dengan versi lama, dan tidak tersentuh migrasi.
        self.assertIsNotNone(backup)
        self.assertEqual(backup.parent, self.path.parent / "backups")
        old = sqlite3.connect(backup)
        try:
            self.assertEqual(old.execute("PRAGMA user_version").fetchone()[0], 3)
            self.assertEqual(old.execute("SELECT title FROM tasks").fetchall(), [("Laporan",)])
        finally:
            old.close()

        # Database utama sudah versi terbaru dan datanya utuh.
        self.assertEqual(self.version(), len(db.MIGRATIONS))
        with db.connection() as conn:
            row = conn.execute("SELECT * FROM tasks").fetchone()
        self.assertEqual(
            (row["title"], row["due_date"], row["priority"], row["category_id"]),
            ("Laporan", "2026-02-01", "high", 1),
        )
