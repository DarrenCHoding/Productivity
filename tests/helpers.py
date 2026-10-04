"""Alat bantu uji: menjalankan server sungguhan dengan database sementara."""

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from app import db
from app.server import make_server


class ApiTestCase(unittest.TestCase):
    """Setiap tes mendapat server & database baru yang kosong."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old_db_path = db.get_db_path()
        db.set_db_path(Path(self._tmp.name) / "test.db")
        db.init_db()
        self.server = make_server("127.0.0.1", 0)
        self.base_url = f"http://127.0.0.1:{self.server.server_address[1]}"
        self._thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self._thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        db.set_db_path(self._old_db_path)
        self._tmp.cleanup()

    def request(self, method, path, body=None):
        """Kirim permintaan; hasil: (kode_status, data_json_atau_teks)."""
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base_url + path, data=data, method=method)
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req) as res:
                return res.status, self._decode(res)
        except urllib.error.HTTPError as e:
            return e.code, self._decode(e)

    @staticmethod
    def _decode(res):
        raw = res.read()
        if not raw:
            return None
        if "json" in (res.headers.get("Content-Type") or ""):
            return json.loads(raw)
        return raw.decode("utf-8")
