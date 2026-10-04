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
        db.init_db()
        self.assertTrue(self.path.exists())
        self.assertEqual(self.version(), len(db.MIGRATIONS))

    def test_init_twice_is_safe(self):
        db.init_db()
        db.init_db()
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
