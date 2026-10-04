from datetime import date, timedelta
from unittest import mock

from app import db
from tests.helpers import ApiTestCase

TODAY = date.today()


def iso(days=0):
    return (TODAY + timedelta(days=days)).isoformat()


class RecurringTaskTest(ApiTestCase):
    def add(self, title="Siram tanaman", **extra):
        status, task = self.request("POST", "/api/tasks", {"title": title, **extra})
        self.assertEqual(status, 201, task)
        return task

    def patch(self, task_id, **body):
        status, task = self.request("PATCH", f"/api/tasks/{task_id}", body)
        self.assertEqual(status, 200, task)
        return task

    def open_titles(self):
        return [(t["title"], t["due_date"]) for t in self.request("GET", "/api/tasks?status=open")[1]]

    def test_repeat_is_saved_and_validated(self):
        task = self.add(repeat="weekly", due_date=iso())
        self.assertEqual(task["repeat"], "weekly")
        self.assertEqual(self.request("POST", "/api/tasks", {"title": "x", "repeat": "yearly"})[0], 400)
        self.assertEqual(self.patch(task["id"], repeat=None)["repeat"], None)

    def test_completing_creates_next_occurrence(self):
        kerja = self.request("POST", "/api/categories", {"name": "Rumah"})[1]
        task = self.add(repeat="daily", due_date=iso(), priority="high", category_id=kerja["id"])
        done = self.patch(task["id"], done=True)
        nxt = done["next_task"]
        self.assertEqual(done["next_task_id"], nxt["id"])
        self.assertEqual((nxt["title"], nxt["due_date"], nxt["priority"], nxt["category_name"], nxt["repeat"]),
                         ("Siram tanaman", iso(1), "high", "Rumah", "daily"))
        self.assertFalse(nxt["done"])
        self.assertEqual(self.open_titles(), [("Siram tanaman", iso(1))])

    def test_overdue_task_does_not_pile_up(self):
        task = self.add(repeat="daily", due_date=iso(-3))
        self.assertEqual(self.patch(task["id"], done=True)["next_task"]["due_date"], iso(1))

    def test_weekly_without_due_date(self):
        task = self.add(repeat="weekly")
        self.assertEqual(self.patch(task["id"], done=True)["next_task"]["due_date"], iso(7))

    def test_non_recurring_task_creates_nothing(self):
        task = self.add("Sekali saja", due_date=iso())
        done = self.patch(task["id"], done=True)
        self.assertNotIn("next_task", done)
        self.assertEqual(self.open_titles(), [])

    def test_undo_removes_the_untouched_next_task(self):
        task = self.add(repeat="daily", due_date=iso())
        self.patch(task["id"], done=True)
        reopened = self.patch(task["id"], done=False)
        self.assertIsNone(reopened["next_task_id"])
        self.assertEqual(self.open_titles(), [("Siram tanaman", iso())])
        # Selesai lagi: tetap hanya satu jadwal berikutnya.
        self.patch(task["id"], done=True)
        self.assertEqual(self.open_titles(), [("Siram tanaman", iso(1))])

    def test_undo_keeps_next_task_that_was_edited(self):
        task = self.add(repeat="daily", due_date=iso())
        nxt = self.patch(task["id"], done=True)["next_task"]
        with mock.patch("app.api.tasks.now", return_value="2099-01-01T00:00:00"):
            self.patch(nxt["id"], title="Siram tanaman (pakai pupuk)")
        self.patch(task["id"], done=False)
        titles = sorted(t for t, _ in self.open_titles())
        self.assertEqual(titles, ["Siram tanaman", "Siram tanaman (pakai pupuk)"])

    def test_completing_twice_does_not_duplicate(self):
        task = self.add(repeat="daily", due_date=iso())
        self.patch(task["id"], done=True)
        self.patch(task["id"], done=True)  # dikirim dua kali (misalnya klik ganda)
        self.assertEqual(len(self.open_titles()), 1)

    def test_chain_continues(self):
        task = self.add(repeat="weekly", due_date=iso())
        second = self.patch(task["id"], done=True)["next_task"]
        third = self.patch(second["id"], done=True)["next_task"]
        self.assertEqual(third["due_date"], iso(14))

    def test_monthly_keeps_anchor_day_through_edits(self):
        task = self.add(repeat="monthly", due_date="2027-01-31")
        with mock.patch("app.api.tasks.date") as fake_date:
            fake_date.today.return_value = date(2027, 1, 31)
            fake_date.fromisoformat = date.fromisoformat
            feb = self.patch(task["id"], done=True)["next_task"]
            self.assertEqual(feb["due_date"], "2027-02-28")
            # Mengedit judul (jendela edit mengirim ulang tanggal yang sama) tidak menghapus patokan 31.
            self.patch(feb["id"], title="Bayar kos", due_date="2027-02-28", repeat="monthly")
            fake_date.today.return_value = date(2027, 2, 28)
            mar = self.patch(feb["id"], done=True)["next_task"]
        self.assertEqual(mar["due_date"], "2027-03-31")

    def test_deleting_tasks_in_a_chain(self):
        task = self.add(repeat="daily", due_date=iso())
        nxt = self.patch(task["id"], done=True)["next_task"]
        self.assertEqual(self.request("DELETE", f"/api/tasks/{nxt['id']}")[0], 204)
        self.assertIsNone(self.request("GET", f"/api/tasks/{task['id']}")[1]["next_task_id"])
        self.assertEqual(self.patch(task["id"], done=False)["done"], False)

    def test_migration_from_previous_version_keeps_tasks(self):
        with db.connection() as conn:
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            columns = {row[1] for row in conn.execute("PRAGMA table_info(tasks)")}
        self.assertEqual(version, len(db.MIGRATIONS))
        self.assertTrue({"repeat", "repeat_day", "next_task_id"} <= columns)
