import json
import os
import sqlite3
import time
from datetime import date, timedelta

from app import backup, db
from tests.helpers import ApiTestCase


class BackupApiTest(ApiTestCase):
    def add_task(self, title, **extra):
        status, task = self.request("POST", "/api/tasks", {"title": title, **extra})
        self.assertEqual(status, 201, task)
        return task

    def titles(self):
        return sorted(t["title"] for t in self.request("GET", "/api/tasks")[1])

    def export(self):
        status, headers, data = self.request_raw("GET", "/api/backup/export")
        self.assertEqual(status, 200)
        return headers, data

    def restore(self, data):
        status, _, body = self.request_raw("POST", "/api/backup/restore", data)
        return status, json.loads(body)

    def test_export_is_complete_database_file(self):
        kerja = self.request("POST", "/api/categories", {"name": "Kerja"})[1]
        self.add_task("Laporan", category_id=kerja["id"], priority="high", due_date="2026-10-10")
        headers, data = self.export()
        self.assertTrue(data.startswith(backup.SQLITE_HEADER))
        self.assertIn('attachment; filename="productivity-cadangan-', headers["Content-Disposition"])
        path = os.path.join(self._tmp.name, "ekspor.db")
        with open(path, "wb") as f:
            f.write(data)
        conn = sqlite3.connect(path)
        try:
            self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], len(db.MIGRATIONS))
            row = conn.execute("SELECT title, priority, due_date, category_id FROM tasks").fetchone()
            self.assertEqual(row, ("Laporan", "high", "2026-10-10", kerja["id"]))
        finally:
            conn.close()

    def test_round_trip_restore(self):
        self.add_task("A")
        self.add_task("B")
        self.request("PATCH", "/api/settings", {"focus_work_minutes": 40})
        _, saved = self.export()

        # Data berubah setelah ekspor...
        for t in self.request("GET", "/api/tasks")[1]:
            self.request("DELETE", f"/api/tasks/{t['id']}")
        self.add_task("C")
        self.request("PATCH", "/api/settings", {"focus_work_minutes": 10})

        # ...lalu dipulihkan: kembali persis seperti saat ekspor.
        status, result = self.restore(saved)
        self.assertEqual(status, 200, result)
        self.assertEqual(result["summary"], "2 tugas, 0 kategori, 0 sesi fokus")
        self.assertEqual(self.titles(), ["A", "B"])
        self.assertEqual(self.request("GET", "/api/settings")[1]["focus_work_minutes"], 40)

        # Data sebelum pemulihan ikut dicadangkan.
        safety = db.get_backup_dir() / result["safety_backup"]
        self.assertTrue(result["safety_backup"].endswith("-sebelum-pemulihan.db"))
        conn = sqlite3.connect(safety)
        try:
            self.assertEqual(conn.execute("SELECT title FROM tasks").fetchall(), [("C",)])
        finally:
            conn.close()

    def test_rejects_bad_files_without_touching_data(self):
        self.add_task("Aman")
        other = os.path.join(self._tmp.name, "lain.db")
        conn = sqlite3.connect(other)
        conn.execute("CREATE TABLE catatan (x)")
        conn.commit()
        conn.close()
        with open(other, "rb") as f:
            not_productivity = f.read()

        cases = {
            "kosong": b"",
            "teks": b"ini bukan database",
            "terpotong": self.export()[1][:2000],
            "database lain": not_productivity,
        }
        for label, data in cases.items():
            status, result = self.restore(data)
            self.assertEqual(status, 400, label)
            self.assertIn("error", result, label)
        self.assertEqual(self.titles(), ["Aman"])
        # Tidak ada cadangan "sebelum pemulihan" karena tidak ada yang dipulihkan.
        names = [f["name"] for f in self.request("GET", "/api/backup/automatic")[1]["files"]]
        self.assertFalse([n for n in names if "pemulihan" in n])

    def test_rejects_backup_from_newer_app_version(self):
        self.add_task("Aman")
        _, data = self.export()
        path = os.path.join(self._tmp.name, "baru.db")
        with open(path, "wb") as f:
            f.write(data)
        conn = sqlite3.connect(path)
        conn.execute(f"PRAGMA user_version = {len(db.MIGRATIONS) + 1}")
        conn.commit()
        conn.close()
        with open(path, "rb") as f:
            status, result = self.restore(f.read())
        self.assertEqual(status, 400)
        self.assertIn("versi aplikasi yang lebih baru", result["error"])
        self.assertEqual(self.titles(), ["Aman"])

    def test_restore_old_version_backup_is_upgraded(self):
        # Cadangan dari tahap 1 (versi 3, belum ada tabel sesi fokus).
        path = os.path.join(self._tmp.name, "lama.db")
        conn = sqlite3.connect(path)
        for version, script in enumerate(db.MIGRATIONS[:3], start=1):
            conn.executescript(script + f"PRAGMA user_version = {version};")
        conn.execute("INSERT INTO tasks (title, created_at, updated_at) VALUES ('Lama', '2026-01-01T00:00:00', '2026-01-01T00:00:00')")
        conn.commit()
        conn.close()
        with open(path, "rb") as f:
            status, result = self.restore(f.read())
        self.assertEqual(status, 200, result)
        self.assertEqual(self.titles(), ["Lama"])
        # Struktur sudah diperbarui: fitur fokus bisa langsung dipakai.
        task = self.request("GET", "/api/tasks")[1][0]
        self.assertEqual(task["focus_seconds"], 0)
        self.assertEqual(self.request("POST", "/api/focus/sessions", {"duration_seconds": 60, "task_id": task["id"]})[0], 201)

    def test_list_and_restore_automatic_backup(self):
        self.add_task("Kemarin")
        backup.ensure_daily_backup(date(2026, 10, 3))
        self.add_task("Hari ini")

        status, listing = self.request("GET", "/api/backup/automatic")
        self.assertEqual(status, 200)
        self.assertEqual(listing["folder"], str(db.get_backup_dir()))
        daily = [f for f in listing["files"] if f["kind"] == "harian"]
        self.assertEqual([f["name"] for f in daily], ["test-harian-2026-10-03.db"])

        status, result = self.request("POST", "/api/backup/automatic/restore", {"name": daily[0]["name"]})
        self.assertEqual(status, 200, result)
        self.assertEqual(self.titles(), ["Kemarin"])

    def test_automatic_restore_rejects_unknown_or_unsafe_names(self):
        for name in ("tidak-ada.db", "../test.db", "..\\test.db", "/etc/passwd", "", None, 5):
            status, _ = self.request("POST", "/api/backup/automatic/restore", {"name": name})
            self.assertEqual(status, 404, name)


class DailyBackupTest(ApiTestCase):
    def daily_names(self):
        return sorted(p.name for p in db.get_backup_dir().glob("*-harian-*.db"))

    def test_once_per_day(self):
        first = backup.ensure_daily_backup(date(2026, 10, 4))
        self.assertEqual(first.name, "test-harian-2026-10-04.db")
        self.assertIsNone(backup.ensure_daily_backup(date(2026, 10, 4)))
        self.assertEqual(self.daily_names(), ["test-harian-2026-10-04.db"])
        # tidak ada file sementara yang tertinggal
        self.assertEqual(list(db.get_backup_dir().glob("*.tmp")), [])

    def test_keeps_only_last_seven(self):
        start = date(2026, 9, 25)
        for i in range(10):
            backup.ensure_daily_backup(start + timedelta(days=i))
        names = self.daily_names()
        self.assertEqual(len(names), 7)
        self.assertEqual(names[0], "test-harian-2026-09-28.db")
        self.assertEqual(names[-1], "test-harian-2026-10-04.db")

    def test_other_backups_are_not_pruned(self):
        db.backup_database("sebelum-v9")
        time.sleep(0.01)
        for i in range(9):
            backup.ensure_daily_backup(date(2026, 9, 1) + timedelta(days=i))
        all_names = [p.name for p in db.get_backup_dir().glob("*.db")]
        self.assertEqual(len([n for n in all_names if "-harian-" in n]), 7)
        self.assertEqual(len([n for n in all_names if n.endswith("-sebelum-v9.db")]), 1)

    def test_backup_is_usable_copy(self):
        self.request("POST", "/api/tasks", {"title": "Penting"})
        path = backup.ensure_daily_backup(date(2026, 10, 4))
        info = backup.inspect_backup(path)
        self.assertEqual(info["counts"]["tasks"], 1)
