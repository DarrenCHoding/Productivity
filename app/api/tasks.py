"""API tugas.

    GET    /api/tasks             daftar tugas  (?status=..., ?view=today, ?category=...)
    POST   /api/tasks             tambah tugas
    GET    /api/tasks/{id}        ambil satu tugas
    PATCH  /api/tasks/{id}        ubah sebagian isi tugas
    DELETE /api/tasks/{id}        hapus tugas

Kolom tugas yang bisa dikirim: title, done, due_date ("YYYY-MM-DD" atau null),
priority ("normal" atau "high"), category_id (nomor kategori atau null),
repeat ("daily", "weekly", "monthly", atau null).
Kolom yang hanya dibaca: category_name, focus_seconds (total waktu fokus),
next_task_id (jadwal berikutnya dari tugas berulang yang sudah selesai).

Tugas berulang: saat ditandai selesai, tugas untuk jadwal berikutnya dibuat
otomatis dan ikut dikirim di jawaban sebagai "next_task". Bila tanda selesai
dibatalkan, tugas berikutnya itu dihapus lagi (asal belum diubah).
"""

import re
from datetime import date

from app.db import connection, now
from app.recurrence import REPEATS, next_due
from app.router import ApiError, route

MAX_TITLE_LENGTH = 500
PRIORITIES = ("normal", "high")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def to_dict(row):
    task = dict(row)
    task["done"] = bool(task["done"])
    return task


# Data tugas selalu diambil bersama nama kategorinya dan total waktu fokusnya.
SELECT_TASK = """
    SELECT
        tasks.*,
        categories.name AS category_name,
        (SELECT COALESCE(SUM(duration_seconds), 0) FROM focus_sessions
         WHERE focus_sessions.task_id = tasks.id) AS focus_seconds
    FROM tasks
    LEFT JOIN categories ON categories.id = tasks.category_id
"""


def get_task(conn, task_id):
    row = conn.execute(SELECT_TASK + " WHERE tasks.id = ?", (task_id,)).fetchone()
    if row is None:
        raise ApiError(404, "Tugas tidak ditemukan.")
    return to_dict(row)


def clean_fields(conn, body, partial):
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

    if "repeat" in body:
        if body["repeat"] is not None and body["repeat"] not in REPEATS:
            raise ApiError(400, "Pengulangan harus daily, weekly, monthly, atau null.")
        fields["repeat"] = body["repeat"]

    # Tanggal atau pola diubah: tanggal patokan bulanan dihitung ulang dari tanggal baru.
    if "repeat" in fields or "due_date" in fields:
        fields["repeat_day"] = None

    if "category_id" in body:
        category_id = body["category_id"]
        if category_id is not None:
            if not isinstance(category_id, int) or isinstance(category_id, bool):
                raise ApiError(400, "Kategori tidak valid.")
            found = conn.execute("SELECT 1 FROM categories WHERE id = ?", (category_id,)).fetchone()
            if not found:
                raise ApiError(400, "Kategori tidak ditemukan.")
        fields["category_id"] = category_id

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
    ?category=<id>|none     hanya tugas di kategori tertentu / tanpa kategori
    """
    status = req.query.get("status", "all")
    status_filter = {
        "all": "1",
        "open": "tasks.done = 0",
        "done": "tasks.done = 1",
    }.get(status)
    if status_filter is None:
        raise ApiError(400, "Status harus open, done, atau all.")

    conditions = [status_filter]
    values = []

    view = req.query.get("view", "all")
    if view == "today":
        today = clean_date(req.query.get("today"), "Tanggal hari ini") or date.today().isoformat()
        conditions.append(
            "((tasks.done = 0 AND tasks.due_date <= ?)"
            " OR (tasks.done = 1 AND substr(tasks.completed_at, 1, 10) = ?))"
        )
        values += [today, today]
    elif view != "all":
        raise ApiError(400, "Tampilan harus today atau all.")

    category = req.query.get("category")
    if category == "none":
        conditions.append("tasks.category_id IS NULL")
    elif category:
        if not category.isdigit():
            raise ApiError(400, "Kategori tidak valid.")
        conditions.append("tasks.category_id = ?")
        values.append(int(category))

    sql = f"""
        {SELECT_TASK}
        WHERE {" AND ".join(conditions)}
        ORDER BY
            tasks.done,
            CASE WHEN tasks.done = 1 THEN tasks.completed_at END DESC,
            tasks.priority = 'high' DESC,
            tasks.due_date IS NULL,
            tasks.due_date,
            tasks.created_at, tasks.id
    """
    with connection() as conn:
        return [to_dict(row) for row in conn.execute(sql, values)]


@route("POST", "/api/tasks")
def create_task(req):
    with connection() as conn:
        fields = clean_fields(conn, req.body, partial=False)
        timestamp = now()
        fields.setdefault("done", 0)
        fields["created_at"] = timestamp
        fields["updated_at"] = timestamp
        fields["completed_at"] = timestamp if fields["done"] else None

        columns = ", ".join(fields)
        placeholders = ", ".join("?" for _ in fields)
        cur = conn.execute(
            f"INSERT INTO tasks ({columns}) VALUES ({placeholders})",
            list(fields.values()),
        )
        return 201, get_task(conn, cur.lastrowid)


@route("GET", "/api/tasks/{id}")
def read_task(req):
    with connection() as conn:
        return get_task(conn, req.params["id"])


def create_next_occurrence(conn, task):
    """Buat tugas untuk jadwal berikutnya dari tugas berulang yang baru selesai."""
    due = date.fromisoformat(task["due_date"]) if task["due_date"] else None
    anchor = task["repeat_day"] or (due or date.today()).day
    next_date = next_due(due, task["repeat"], date.today(), anchor)
    timestamp = now()
    cur = conn.execute(
        "INSERT INTO tasks (title, priority, category_id, repeat, repeat_day, due_date, done, created_at, updated_at)"
        " VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)",
        (task["title"], task["priority"], task["category_id"], task["repeat"],
         anchor if task["repeat"] == "monthly" else None, next_date.isoformat(), timestamp, timestamp),
    )
    conn.execute("UPDATE tasks SET next_task_id = ? WHERE id = ?", (cur.lastrowid, task["id"]))
    return get_task(conn, cur.lastrowid)


def remove_untouched_next(conn, task):
    """Tanda selesai dibatalkan: hapus jadwal berikutnya bila belum dikerjakan atau diubah."""
    if not task["next_task_id"]:
        return
    nxt = conn.execute("SELECT * FROM tasks WHERE id = ?", (task["next_task_id"],)).fetchone()
    if nxt and not nxt["done"] and nxt["updated_at"] == nxt["created_at"]:
        conn.execute("DELETE FROM tasks WHERE id = ?", (nxt["id"],))
    conn.execute("UPDATE tasks SET next_task_id = NULL WHERE id = ?", (task["id"],))


@route("PATCH", "/api/tasks/{id}")
def update_task(req):
    with connection() as conn:
        current = get_task(conn, req.params["id"])
        fields = clean_fields(conn, req.body, partial=True)
        # Tanggal & pola tidak benar-benar berubah: pertahankan tanggal patokan bulanan.
        if (fields.get("due_date", current["due_date"]) == current["due_date"]
                and fields.get("repeat", current["repeat"]) == current["repeat"]):
            fields.pop("repeat_day", None)
        if not fields:
            return current

        done_changed = "done" in fields and bool(fields["done"]) != current["done"]
        if done_changed:
            fields["completed_at"] = now() if fields["done"] else None
        fields["updated_at"] = now()

        assignments = ", ".join(f"{column} = ?" for column in fields)
        conn.execute(
            f"UPDATE tasks SET {assignments} WHERE id = ?",
            [*fields.values(), req.params["id"]],
        )
        task = get_task(conn, req.params["id"])

        next_task = None
        if done_changed and task["done"] and task["repeat"] and not task["next_task_id"]:
            next_task = create_next_occurrence(conn, task)
        elif done_changed and not task["done"]:
            remove_untouched_next(conn, task)

        task = get_task(conn, req.params["id"])
        if next_task:
            task["next_task"] = next_task
        return task


@route("DELETE", "/api/tasks/{id}")
def delete_task(req):
    with connection() as conn:
        get_task(conn, req.params["id"])
        conn.execute("DELETE FROM tasks WHERE id = ?", (req.params["id"],))
    return 204, None
