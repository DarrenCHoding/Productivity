"""Tes otomatis. Jalankan dengan:  python3 -m unittest

Pagar pengaman fitur AI: tes TIDAK BOLEH memanggil Claude API sungguhan.
- ANTHROPIC_API_KEY dikosongkan, jadi API key di file .env Anda tidak ikut terbaca
  (file .env tidak menimpa variabel yang sudah ada).
- Alamat API diarahkan ke port lokal yang tidak dipakai, jadi kalaupun ada kode
  yang tanpa sengaja memanggil API, panggilannya langsung gagal di komputer ini
  dan tidak pernah sampai ke internet.
Tes fitur AI memakai "Claude tiruan" (lihat tests/test_ai.py).
"""

import os

os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["ANTHROPIC_BASE_URL"] = "http://127.0.0.1:9"
