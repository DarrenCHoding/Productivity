"""API timer fokus.

    GET    /api/focus/sessions    riwayat sesi fokus  (?date=YYYY-MM-DD: hanya hari itu)
    POST   /api/focus/sessions    catat satu sesi fokus yang sudah selesai
    DELETE /api/focus/sessions/{id}  hapus satu sesi dari riwayat

Timer-nya sendiri berjalan di browser. Setelah satu sesi fokus selesai (atau
dihentikan), browser mengirim lamanya ke sini untuk dicatat. Total waktu fokus
per tugas ikut tampil di data tugas (kolom focus_seconds).
"""

from datetime import datetime, timedelta

from app.api.tasks import clean_date
from app.db import connection
from app.router import ApiError, route

MAX_SESSION_SECONDS = 6 * 60 * 60  # sesi terpanjang yang diterima: 6 jam

SELECT_SESSION = """
    SELECT focus_sessions.*, tasks.title AS task_title
    FROM focus_sessions
    LEFT JOIN tasks ON tasks.id = focus_sessions.task_id
"""


def to_dict(row):
    session = dict(row)
    session["completed"] = bool(session["completed"])
    return session


@route("GET", "/api/focus/sessions")
def list_sessions(req):
    day = clean_date(req.query.get("date"), "Tanggal")
    with connection() as conn:
        if day:
            rows = conn.execute(
                SELECT_SESSION + " WHERE substr(focus_sessions.ended_at, 1, 10) = ?"
                " ORDER BY focus_sessions.ended_at DESC, focus_sessions.id DESC",
                (day,),
            )
        else:
            rows = conn.execute(
                SELECT_SESSION + " ORDER BY focus_sessions.ended_at DESC, focus_sessions.id DESC LIMIT 100"
            )
        return [to_dict(row) for row in rows]


@route("POST", "/api/focus/sessions")
def create_session(req):
    body = req.body
    if not isinstance(body, dict):
        raise ApiError(400, "Data sesi fokus tidak valid.")

    seconds = body.get("duration_seconds")
    if not isinstance(seconds, int) or isinstance(seconds, bool) or not 1 <= seconds <= MAX_SESSION_SECONDS:
        raise ApiError(400, "Lama sesi fokus tidak valid.")

    completed = body.get("completed", True)
    if not isinstance(completed, bool):
        raise ApiError(400, "Status sesi harus true atau false.")

    task_id = body.get("task_id")
    with connection() as conn:
        if task_id is not None:
            if not isinstance(task_id, int) or isinstance(task_id, bool):
                raise ApiError(400, "Tugas tidak valid.")
            if not conn.execute("SELECT 1 FROM tasks WHERE id = ?", (task_id,)).fetchone():
                raise ApiError(400, "Tugas tidak ditemukan.")

        ended = datetime.now().replace(microsecond=0)
        started = ended - timedelta(seconds=seconds)
        cur = conn.execute(
            "INSERT INTO focus_sessions (task_id, started_at, ended_at, duration_seconds, completed)"
            " VALUES (?, ?, ?, ?, ?)",
            (task_id, started.isoformat(), ended.isoformat(), seconds, int(completed)),
        )
        row = conn.execute(SELECT_SESSION + " WHERE focus_sessions.id = ?", (cur.lastrowid,)).fetchone()
        return 201, to_dict(row)


@route("DELETE", "/api/focus/sessions/{id}")
def delete_session(req):
    with connection() as conn:
        cur = conn.execute("DELETE FROM focus_sessions WHERE id = ?", (req.params["id"],))
        if cur.rowcount == 0:
            raise ApiError(404, "Sesi fokus tidak ditemukan.")
    return 204, None
