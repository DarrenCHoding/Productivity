"""API cadangan & pemulihan data.

    GET    /api/backup/export              unduh seluruh data (satu file .db)
    POST   /api/backup/restore             pulihkan dari file yang diunggah
                                           (Content-Type: application/octet-stream)
    GET    /api/backup/automatic           daftar cadangan di folder data/backups/
    POST   /api/backup/automatic/restore   pulihkan dari salah satu cadangan itu  {"name": "..."}

Logikanya ada di app/backup.py.
"""

from app import backup
from app.router import ApiError, Response, route


@route("GET", "/api/backup/export")
def export_data(req):
    return Response(backup.export_bytes(), "application/octet-stream", filename=backup.export_filename())


@route("POST", "/api/backup/restore")
def restore_upload(req):
    return backup.restore_upload(req.raw)


@route("GET", "/api/backup/automatic")
def list_automatic(req):
    return backup.list_backups()


@route("POST", "/api/backup/automatic/restore")
def restore_automatic(req):
    if not isinstance(req.body, dict):
        raise ApiError(400, "Pilih cadangan yang ingin dipulihkan.")
    return backup.restore_from_file(backup.find_backup(req.body.get("name")))
