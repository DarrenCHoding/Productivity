"""API tugas.

    GET    /api/tasks             daftar tugas  (?status=..., ?view=today)

Kolom tugas yang bisa dikirim: title, done, due_date ("YYYY-MM-DD" atau null),
priority ("normal" atau "high").
    POST   /api/tasks             tambah tugas
    GET    /api/tasks/{id}        ambil satu tugas
    PATCH  /api/tasks/{id}        ubah sebagian isi tugas
    DELETE /api/tasks/{id}        hapus tugas
"""

import re
from datetime import date

from app.db import connection, now
from app.router import ApiError, route

MAX_TITLE_LENGTH = 500
PRIORITIES = ("normal", "high")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def to_dict(row):
    task = dict(row)
    task["done"] = bool(task["done"])
    return task


def get_task(conn, task_id):
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        raise ApiError(404, "Tugas tidak ditemukan.")
    return to_dict(row)


def clean_fields(body, partial):
    """Periksa data dari tampilan. Hasil: dict kolom -> nilai yang siap disimpan.

    partial=True (untuk PATCH): hanya kolom yang dikirim yang diperiksa.
    """
    if not isinstance(body, dict):
        raise ApiError(400, "Data tugas tidak valid.")

    fields = {}

    if "title" in body or not partial:
        title = body.get("title")
        if not isinstance(title, str) or not title.strip():
            raise ApiError(400, "Judul tugas tidak boleh kosong.")
        title = " ".join(title.split())  # rapikan spasi berlebih
        if len(title) > MAX_TITLE_LENGTH:
            raise ApiError(400, f"Judul tugas maksimal {MAX_TITLE_LENGTH} karakter.")
        fields["title"] = title

    if "done" in body:
        if not isinstance(body["done"], bool):
            raise ApiError(400, "Status selesai harus true atau false.")
        fields["done"] = int(body["done"])

    if "due_date" in body:
        fields["due_date"] = clean_date(body["due_date"], "Tanggal jatuh tempo")

    if "priority" in body or not partial:
        priority = body.get("priority", "normal")
        if priority not in PRIORITIES:
            raise ApiError(400, "Prioritas harus 'normal' atau 'high'.")
        fields["priority"] = priority

    return fields


def clean_date(value, label, required=False):
    """Terima tanggal 'YYYY-MM-DD'. Nilai kosong/null berarti tanpa tanggal."""
    if value is None or value == "":
        if required:
            raise ApiError(400, f"{label} wajib diisi.")
        return None
    if not isinstance(value, str) or not DATE_PATTERN.match(value):
        raise ApiError(400, f"{label} harus berformat TTTT-BB-HH, contoh 2026-12-31.")
    try:
        date.fromisoformat(value)
    except ValueError:
        raise ApiError(400, f"{label} tidak valid.")
    return value


@route("GET", "/api/tasks")
def list_tasks(req):
    """Daftar tugas.

    ?status=open|done|all   (default: all)
    ?view=today             hanya tugas belum selesai yang jatuh tempo hari ini
                            atau terlambat, ditambah tugas yang diselesaikan hari ini
    ?today=YYYY-MM-DD       tanggal "hari ini" menurut perangkat pengguna
                            (default: tanggal di komputer server)
    """
    status = req.query.get("status", "all")
    status_filter = {
        "all": "1",
        "open": "done = 0",
        "done": "done = 1",
    }.get(status)
    if status_filter is None:
        raise ApiError(400, "Status harus open, done, atau all.")

    conditions = [status_filter]
    values = []

    view = req.query.get("view", "all")
    if view == "today":
        today = clean_date(req.query.get("today"), "Tanggal hari ini") or date.today().isoformat()
        conditions.append(
            "((done = 0 AND due_date <= ?) OR (done = 1 AND substr(completed_at, 1, 10) = ?))"
        )
        values += [today, today]
    elif view != "all":
        raise ApiError(400, "Tampilan harus today atau all.")

    sql = f"""
        SELECT * FROM tasks
        WHERE {" AND ".join(conditions)}
        ORDER BY
            done,
            CASE WHEN done = 1 THEN completed_at END DESC,
            priority = 'high' DESC,
            due_date IS NULL,
            due_date,
            created_at, id
    """
    with connection() as conn:
        return [to_dict(row) for row in conn.execute(sql, values)]


@route("POST", "/api/tasks")
def create_task(req):
    fields = clean_fields(req.body, partial=False)
    timestamp = now()
    fields.setdefault("done", 0)
    fields["created_at"] = timestamp
    fields["updated_at"] = timestamp
    fields["completed_at"] = timestamp if fields["done"] else None

    columns = ", ".join(fields)
    placeholders = ", ".join("?" for _ in fields)
    with connection() as conn:
        cur = conn.execute(
            f"INSERT INTO tasks ({columns}) VALUES ({placeholders})",
            list(fields.values()),
        )
        return 201, get_task(conn, cur.lastrowid)


@route("GET", "/api/tasks/{id}")
def read_task(req):
    with connection() as conn:
        return get_task(conn, req.params["id"])


@route("PATCH", "/api/tasks/{id}")
def update_task(req):
    fields = clean_fields(req.body, partial=True)
    with connection() as conn:
        current = get_task(conn, req.params["id"])
        if not fields:
            return current

        if "done" in fields and bool(fields["done"]) != current["done"]:
            fields["completed_at"] = now() if fields["done"] else None
        fields["updated_at"] = now()

        assignments = ", ".join(f"{column} = ?" for column in fields)
        conn.execute(
            f"UPDATE tasks SET {assignments} WHERE id = ?",
            [*fields.values(), req.params["id"]],
        )
        return get_task(conn, req.params["id"])


@route("DELETE", "/api/tasks/{id}")
def delete_task(req):
    with connection() as conn:
        get_task(conn, req.params["id"])
        conn.execute("DELETE FROM tasks WHERE id = ?", (req.params["id"],))
    return 204, None
