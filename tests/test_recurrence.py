import unittest
from datetime import date

from app.recurrence import next_due


class NextDueTest(unittest.TestCase):
    TODAY = date(2026, 10, 4)  # Minggu

    def check(self, due, repeat, expected, today=TODAY, anchor=None):
        self.assertEqual(next_due(due, repeat, today, anchor), expected)

    def test_daily(self):
        self.check(date(2026, 10, 4), "daily", date(2026, 10, 5))   # selesai tepat waktu
        self.check(date(2026, 10, 1), "daily", date(2026, 10, 5))   # terlambat: langsung besok
        self.check(date(2026, 10, 8), "daily", date(2026, 10, 9))   # selesai lebih awal
        self.check(None, "daily", date(2026, 10, 5))                # tanpa tanggal: dari hari ini

    def test_weekly_keeps_the_weekday(self):
        self.check(date(2026, 10, 4), "weekly", date(2026, 10, 11))
        self.check(date(2026, 9, 28), "weekly", date(2026, 10, 5))  # Senin lalu -> Senin depan
        self.check(date(2026, 9, 14), "weekly", date(2026, 10, 5))  # terlambat 3 minggu
        self.check(None, "weekly", date(2026, 10, 11))

    def test_monthly(self):
        self.check(date(2026, 10, 4), "monthly", date(2026, 11, 4))
        self.check(date(2026, 12, 15), "monthly", date(2027, 1, 15), today=date(2026, 12, 15))
        self.check(date(2026, 8, 10), "monthly", date(2026, 10, 10))  # terlambat 2 bulan

    def test_monthly_end_of_month_does_not_drift(self):
        self.check(date(2027, 1, 31), "monthly", date(2027, 2, 28), today=date(2027, 1, 31))
        self.check(date(2027, 2, 28), "monthly", date(2027, 3, 31), today=date(2027, 2, 28), anchor=31)
        self.check(date(2028, 1, 31), "monthly", date(2028, 2, 29), today=date(2028, 1, 31))  # kabisat
        self.check(date(2026, 10, 31), "monthly", date(2026, 11, 30), today=date(2026, 10, 31))

    def test_unknown_repeat(self):
        with self.assertRaises(ValueError):
            next_due(None, "yearly", self.TODAY)
