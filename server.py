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

from app.db import get_db_path, init_db  # noqa: E402
from app.server import make_server  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Aplikasi Productivity pribadi")
    parser.add_argument("--host", default="127.0.0.1", help="alamat server (default: 127.0.0.1, hanya komputer ini)")
    parser.add_argument("--port", type=int, default=8000, help="nomor port (default: 8000)")
    parser.add_argument("--no-browser", action="store_true", help="jangan buka browser otomatis")
    args = parser.parse_args()

    init_db()

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
    print("Tekan Ctrl+C untuk menghentikan.")

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
