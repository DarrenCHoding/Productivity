"""Uji bahwa data tetap ada setelah server dimatikan lalu dijalankan lagi.

Uji ini menjalankan server.py sungguhan (seperti saat Anda memakainya),
dengan file database sementara supaya data asli tidak tersentuh.
"""

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class PersistenceTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmp.name) / "productivity.db"
        self.port = free_port()
        self.proc = None

    def tearDown(self):
        self.stop_server()
        self._tmp.cleanup()

    def start_server(self):
        env = {**os.environ, "PRODUCTIVITY_DB": str(self.db_path)}
        self.proc = subprocess.Popen(
            [sys.executable, "server.py", "--port", str(self.port), "--no-browser"],
            cwd=PROJECT_DIR,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.time() + 10
        while time.time() < deadline:
            try:
                self.call("GET", "/api/health")
                return
            except OSError:
                time.sleep(0.1)
        self.fail("Server tidak mau menyala.")

    def stop_server(self):
        """Matikan server secara paksa, seperti komputer yang tiba-tiba mati."""
        if self.proc and self.proc.poll() is None:
            self.proc.kill()
            self.proc.wait(timeout=10)

    def call(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}", data=data, method=method,
            headers={"Content-Type": "application/json"} if data else {},
        )
        with urllib.request.urlopen(req, timeout=5) as res:
            raw = res.read()
            return json.loads(raw) if raw else None

    def test_data_survives_restart(self):
        self.start_server()
        kerja = self.call("POST", "/api/categories", {"name": "Kerja"})
        self.call("POST", "/api/tasks", {
            "title": "Laporan bulanan", "due_date": "2026-10-31",
            "priority": "high", "category_id": kerja["id"],
        })
        selesai = self.call("POST", "/api/tasks", {"title": "Sudah beres"})
        self.call("PATCH", f"/api/tasks/{selesai['id']}", {"done": True})
        before = self.call("GET", "/api/tasks")

        self.stop_server()
        self.start_server()

        after = self.call("GET", "/api/tasks")
        self.assertEqual(after, before)
        laporan = next(t for t in after if t["title"] == "Laporan bulanan")
        self.assertEqual(laporan["due_date"], "2026-10-31")
        self.assertEqual(laporan["priority"], "high")
        self.assertEqual(laporan["category_name"], "Kerja")
        self.assertTrue(next(t for t in after if t["title"] == "Sudah beres")["done"])
        self.assertEqual([c["name"] for c in self.call("GET", "/api/categories")], ["Kerja"])
