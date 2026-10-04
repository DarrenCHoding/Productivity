"""API umum: memeriksa apakah server berjalan."""

from app.router import route


@route("GET", "/api/health")
def health(req):
    return {"status": "ok"}
