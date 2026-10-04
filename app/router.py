"""Pengatur alamat (router) kecil untuk API.

Cara pakai di file API:

    from app.router import route, ApiError

    @route("GET", "/api/contoh/{id}")
    def ambil_contoh(req):
        return {"id": req.params["id"]}

Fungsi menerima objek Request dan mengembalikan data (dict/list) yang akan
dikirim sebagai JSON, atau tuple (status, data) untuk kode status lain.
Untuk mengirim file (misalnya unduhan cadangan), kembalikan objek Response.
"""

import re

_routes = []


class ApiError(Exception):
    """Lempar error ini untuk mengirim pesan kesalahan ke tampilan."""

    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


class Request:
    def __init__(self, method, path, query, body, params, raw=b""):
        self.method = method
        self.path = path
        self.query = query  # dict: nama -> nilai (string)
        self.body = body  # hasil JSON dari isi permintaan (atau None)
        self.params = params  # dict: bagian {nama} dari alamat
        self.raw = raw  # isi permintaan apa adanya (untuk unggahan file)


class Response:
    """Jawaban berupa file, bukan JSON.

    filename diisi bila browser harus menyimpannya sebagai unduhan.
    """

    def __init__(self, body, content_type, filename=None, status=200):
        self.body = body
        self.content_type = content_type
        self.filename = filename
        self.status = status


def route(method, pattern):
    """Daftarkan fungsi untuk metode HTTP + pola alamat tertentu."""
    # "{id}" di pola alamat hanya menerima angka.
    regex = "^" + re.sub(r"\{(\w+)\}", r"(?P<\1>\\d+)", pattern) + "$"
    compiled = re.compile(regex)

    def decorator(func):
        _routes.append((method, compiled, func))
        return func

    return decorator


def match(method, path):
    """Cari fungsi yang cocok. Hasil: (fungsi, params) atau (None, kode_status)."""
    path_found = False
    for route_method, regex, func in _routes:
        m = regex.match(path)
        if not m:
            continue
        path_found = True
        if route_method == method:
            params = {k: int(v) for k, v in m.groupdict().items()}
            return func, params
    return None, (405 if path_found else 404)
