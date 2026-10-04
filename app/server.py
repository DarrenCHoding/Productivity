"""Server web: melayani API (/api/...) dan file tampilan (folder static/)."""

import json
import os
import traceback
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qsl, urlsplit

import app.api  # noqa: F401  (memuat & mendaftarkan semua API)
from app.db import PROJECT_DIR
from app.router import ApiError, Request, Response, match

STATIC_DIR = PROJECT_DIR / "static"
MAX_BODY_BYTES = 1_000_000  # data JSON biasa
MAX_UPLOAD_BYTES = 200_000_000  # unggahan file (misalnya file cadangan)
UPLOAD_TYPE = "application/octet-stream"


class Handler(SimpleHTTPRequestHandler):
    # Tetapkan jenis file secara eksplisit. Di Windows, pengaturan sistem kadang
    # salah menganggap .js sebagai teks biasa sehingga tampilan tidak mau jalan.
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".html": "text/html; charset=utf-8",
        ".js": "text/javascript; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".json": "application/json",
        ".svg": "image/svg+xml",
    }

    # --- Pembagian permintaan: API atau file statis ---

    def do_GET(self):
        if self._is_api():
            self._handle_api("GET")
        else:
            super().do_GET()

    def do_HEAD(self):
        if self._is_api():
            self._send_json(405, {"error": "Metode tidak didukung."})
        else:
            super().do_HEAD()

    def do_POST(self):
        self._api_only("POST")

    def do_PATCH(self):
        self._api_only("PATCH")

    def do_DELETE(self):
        self._api_only("DELETE")

    def _is_api(self):
        return self.path == "/api" or self.path.startswith("/api/")

    def _api_only(self, method):
        if self._is_api():
            self._handle_api(method)
        else:
            self._send_json(405, {"error": "Metode tidak didukung."})

    # --- API ---

    def _handle_api(self, method):
        url = urlsplit(self.path)
        func, extra = match(method, url.path)
        if func is None:
            message = "Alamat API tidak ditemukan." if extra == 404 else "Metode tidak didukung."
            self._send_json(extra, {"error": message})
            return
        try:
            body, raw = self._read_body()
            req = Request(
                method=method,
                path=url.path,
                query=dict(parse_qsl(url.query)),
                body=body,
                params=extra,
                raw=raw,
            )
            result = func(req)
            if isinstance(result, Response):
                self._send_file(result)
                return
            status, data = result if isinstance(result, tuple) else (200, result)
            self._send_json(status, data)
        except ApiError as e:
            self._send_json(e.status, {"error": e.message})
        except Exception:
            traceback.print_exc()
            self._send_json(500, {"error": "Terjadi kesalahan di server."})

    def _read_body(self):
        """Baca isi permintaan. Hasil: (data JSON atau None, isi mentah)."""
        length = int(self.headers.get("Content-Length") or 0)
        is_upload = (self.headers.get("Content-Type") or "").startswith(UPLOAD_TYPE)
        if length == 0:
            return None, b""
        if length > (MAX_UPLOAD_BYTES if is_upload else MAX_BODY_BYTES):
            raise ApiError(413, "Data yang dikirim terlalu besar.")
        raw = self.rfile.read(length)
        if is_upload:
            return None, raw
        try:
            return json.loads(raw.decode("utf-8")), raw
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ApiError(400, "Format data tidak valid (harus JSON).")

    def _send_file(self, response):
        self.send_response(response.status)
        self.send_header("Content-Type", response.content_type)
        self.send_header("Content-Length", str(len(response.body)))
        if response.filename:
            self.send_header("Content-Disposition", f'attachment; filename="{response.filename}"')
        self.end_headers()
        self.wfile.write(response.body)

    def _send_json(self, status, data):
        if status == 204:
            self.send_response(204)
            self.end_headers()
            return
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # --- Lain-lain ---

    def end_headers(self):
        # Selalu minta browser memeriksa versi terbaru, supaya perubahan kode langsung terlihat.
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, format, *args):
        # Sembunyikan log setiap permintaan supaya terminal tetap rapi.
        pass


class Server(ThreadingHTTPServer):
    # Di Windows, opsi ini membuat dua program bisa memakai port yang sama tanpa
    # error, sehingga menjalankan aplikasi dua kali tidak terdeteksi. Matikan di sana.
    allow_reuse_address = os.name != "nt"
    daemon_threads = True


def make_server(host, port):
    handler = partial(Handler, directory=str(STATIC_DIR))
    return Server((host, port), handler)
