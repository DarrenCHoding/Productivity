"""Perhitungan jadwal berikutnya untuk tugas berulang.

Aturan:
- Jadwal berikutnya dihitung dari tanggal jatuh tempo tugas, maju satu langkah
  (1 hari / 1 minggu / 1 bulan), dan terus maju sampai tanggalnya SETELAH hari ini.
  Jadi tugas yang terlambat tidak menumpuk: tugas harian yang terlambat 3 hari,
  lalu diselesaikan hari ini, muncul lagi besok.
- Tugas yang selesai lebih awal maju satu langkah saja dari tanggal jatuh temponya.
- Tugas berulang tanpa tanggal jatuh tempo dihitung dari hari ini.
- Bulanan memakai "tanggal patokan" (anchor_day), supaya tugas tanggal 31 tetap
  kembali ke tanggal 31: 31 Jan -> 28/29 Feb -> 31 Mar.
"""

import calendar
from datetime import date, timedelta

REPEATS = ("daily", "weekly", "monthly")


def add_months(day, months, anchor_day):
    """Maju `months` bulan, ke tanggal `anchor_day` (atau akhir bulan bila bulannya lebih pendek)."""
    index = day.month - 1 + months
    year, month = day.year + index // 12, index % 12 + 1
    last = calendar.monthrange(year, month)[1]
    return date(year, month, min(anchor_day, last))


def step(day, repeat, anchor_day):
    if repeat == "daily":
        return day + timedelta(days=1)
    if repeat == "weekly":
        return day + timedelta(days=7)
    if repeat == "monthly":
        return add_months(day, 1, anchor_day)
    raise ValueError(f"Jenis pengulangan tidak dikenal: {repeat}")


def next_due(due, repeat, today, anchor_day=None):
    """Tanggal jatuh tempo berikutnya (objek date).

    due         tanggal jatuh tempo tugas yang baru selesai (date atau None)
    anchor_day  tanggal patokan untuk bulanan (default: tanggal dari `due`)
    """
    base = due or today
    anchor = anchor_day or base.day
    result = step(base, repeat, anchor)
    while result <= today:
        result = step(result, repeat, anchor)
    return result
