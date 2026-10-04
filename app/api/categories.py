"""API kategori.

    GET    /api/categories        daftar kategori (beserta jumlah tugasnya)
    POST   /api/categories        buat kategori       {"name": "Kerja"}
    PATCH  /api/categories/{id}   ganti nama kategori {"name": "Kantor"}
    DELETE /api/categories/{id}   hapus kategori (tugasnya tetap ada, tanpa kategori)
"""

import sqlite3

from app.db import connection, now
from app.router import ApiError, route

MAX_NAME_LENGTH = 50

SELECT_CATEGORY = """
    SELECT
        c.id, c.name, c.created_at,
        COALESCE(SUM(CASE WHEN t.done = 0 THEN 1 ELSE 0 END), 0) AS open_count,
        COUNT(t.id) AS total_count
    FROM categories c
    LEFT JOIN tasks t ON t.category_id = c.id
"""


def get_category(conn, category_id):
    row = conn.execute(
        SELECT_CATEGORY + " WHERE c.id = ? GROUP BY c.id", (category_id,)
    ).fetchone()
    if row is None:
        raise ApiError(404, "Kategori tidak ditemukan.")
    return dict(row)


def clean_name(body):
    if not isinstance(body, dict):
        raise ApiError(400, "Data kategori tidak valid.")
    name = body.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ApiError(400, "Nama kategori tidak boleh kosong.")
    name = " ".join(name.split())
    if len(name) > MAX_NAME_LENGTH:
        raise ApiError(400, f"Nama kategori maksimal {MAX_NAME_LENGTH} karakter.")
    return name


DUPLICATE_MESSAGE = "Kategori dengan nama itu sudah ada."


@route("GET", "/api/categories")
def list_categories(req):
    with connection() as conn:
        rows = conn.execute(SELECT_CATEGORY + " GROUP BY c.id ORDER BY c.name COLLATE NOCASE")
        return [dict(row) for row in rows]


@route("POST", "/api/categories")
def create_category(req):
    name = clean_name(req.body)
    try:
        with connection() as conn:
            cur = conn.execute(
                "INSERT INTO categories (name, created_at) VALUES (?, ?)", (name, now())
            )
            return 201, get_category(conn, cur.lastrowid)
    except sqlite3.IntegrityError:
        raise ApiError(409, DUPLICATE_MESSAGE)


@route("PATCH", "/api/categories/{id}")
def rename_category(req):
    name = clean_name(req.body)
    try:
        with connection() as conn:
            get_category(conn, req.params["id"])
            conn.execute("UPDATE categories SET name = ? WHERE id = ?", (name, req.params["id"]))
            return get_category(conn, req.params["id"])
    except sqlite3.IntegrityError:
        raise ApiError(409, DUPLICATE_MESSAGE)


@route("DELETE", "/api/categories/{id}")
def delete_category(req):
    with connection() as conn:
        get_category(conn, req.params["id"])
        # Tugas di kategori ini otomatis menjadi "tanpa kategori" (ON DELETE SET NULL).
        conn.execute("DELETE FROM categories WHERE id = ?", (req.params["id"],))
    return 204, None
