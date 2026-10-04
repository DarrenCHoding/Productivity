"""Jalankan aplikasi Productivity.

    python3 server.py              (Mac / Linux / Raspberry Pi)
    python server.py               (Windows)

Pilihan tambahan:
    --port 8000        ganti nomor port
    --host 0.0.0.0     izinkan perangkat lain di jaringan rumah membuka aplikasi
    --no-browser       jangan buka browser otomatis
"""

import argparse
import sys
import threading
import webbrowser

if sys.version_info < (3, 8):
    sys.exit("Aplikasi ini butuh Python 3.8 atau lebih baru.")

from app.env import load_env  # noqa: E402

# Baca file .env (API key, dll.) sebelum modul lain dimuat.
load_env()

from app.backup import start_daily_backups  # noqa: E402
from app.db import get_backup_dir, get_db_path, init_db  # noqa: E402
from app.server import make_server  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Aplikasi Productivity pribadi")
    parser.add_argument("--host", default="127.0.0.1", help="alamat server (default: 127.0.0.1, hanya komputer ini)")
    parser.add_argument("--port", type=int, default=8000, help="nomor port (default: 8000)")
    parser.add_argument("--no-browser", action="store_true", help="jangan buka browser otomatis")
    args = parser.parse_args()

    backup = init_db()
    if backup:
        print("Database diperbarui untuk fitur baru. Cadangan data lama disimpan di:")
        print(f"  {backup}")

    try:
        server = make_server(args.host, args.port)
    except OSError:
        sys.exit(
            f"Port {args.port} sedang dipakai program lain (mungkin aplikasi ini sudah berjalan).\n"
            "Tutup program itu, atau jalankan dengan port lain, misalnya:\n"
            "  python3 server.py --port 8001     (Windows: python server.py --port 8001)"
        )

    url = f"http://localhost:{args.port}"
    print("Aplikasi Productivity berjalan.")
    print(f"  Buka di browser : {url}")
    if args.host == "0.0.0.0":
        print(f"  Dari perangkat lain di jaringan rumah: http://<alamat-IP-komputer-ini>:{args.port}")
    print(f"  File data       : {get_db_path()}")
    print(f"  Cadangan        : {get_backup_dir()}  (otomatis setiap hari, 7 terakhir)")
    print("Tekan Ctrl+C untuk menghentikan.")

    start_daily_backups(on_created=lambda path: print(f"Cadangan harian dibuat: {path.name}"))

    if not args.no_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        print("\nServer dihentikan. Data Anda sudah tersimpan.")


if __name__ == "__main__":
    main()
