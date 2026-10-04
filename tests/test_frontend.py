"""Tes kode tampilan (JavaScript) di folder tests/js/.

Tes ini butuh Node.js versi 22 atau lebih baru. Node.js TIDAK wajib untuk
menjalankan aplikasi; bila belum terpasang, tes ini dilewati (skipped) dan tes
lainnya tetap berjalan seperti biasa.

Tes dijalankan beberapa kali dengan zona waktu berbeda, supaya perhitungan
tanggal terbukti benar di mana pun, termasuk di zona waktu yang memakai
pergantian jam musim panas.
"""

import os
import re
import shutil
import subprocess
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
NODE_MIN_MAJOR = 22
TIME_ZONES = ["Asia/Jakarta", "Europe/Amsterdam"]


def find_node():
    """Hasil: (lokasi node, None) atau (None, alasan dilewati)."""
    node = shutil.which("node")
    if not node:
        return None, "Node.js tidak terpasang, tes JavaScript dilewati (opsional)."
    version = subprocess.run([node, "--version"], capture_output=True, text=True).stdout.strip()
    match = re.match(r"v(\d+)", version)
    if not match or int(match.group(1)) < NODE_MIN_MAJOR:
        return None, f"Tes JavaScript butuh Node.js {NODE_MIN_MAJOR}+, yang terpasang {version or 'tidak dikenal'}. Dilewati."
    return node, None


class FrontendTest(unittest.TestCase):
    def test_javascript(self):
        node, reason = find_node()
        if not node:
            self.skipTest(reason)
        for tz in TIME_ZONES:
            with self.subTest(zona_waktu=tz):
                result = subprocess.run(
                    [node, "--test", "tests/js/*.test.mjs"],
                    cwd=PROJECT_DIR,
                    env={**os.environ, "TZ": tz},
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if result.returncode != 0:
                    failures = "\n".join(line for line in result.stdout.splitlines() if line.startswith("not ok"))
                    self.fail(
                        f"Tes JavaScript gagal (zona waktu {tz}):\n{failures}\n\n"
                        f"Detail lengkap: jalankan  node --test \"tests/js/*.test.mjs\"\n\n{result.stdout[-3000:]}"
                    )
