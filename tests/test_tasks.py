from tests.helpers import ApiTestCase


class TaskCrudTest(ApiTestCase):
    def add(self, title="Tugas", **extra):
        status, task = self.request("POST", "/api/tasks", {"title": title, **extra})
        self.assertEqual(status, 201, task)
        return task

    def test_create_and_list(self):
        task = self.add("  Beli   susu ")
        self.assertEqual(task["title"], "Beli susu")
        self.assertFalse(task["done"])
        self.assertIsNone(task["completed_at"])
        self.assertEqual(self.request("GET", "/api/tasks"), (200, [task]))

    def test_title_required(self):
        for body in ({}, {"title": ""}, {"title": "   "}, {"title": 5}, None, []):
            status, data = self.request("POST", "/api/tasks", body)
            self.assertEqual(status, 400, body)
            self.assertIn("error", data)

    def test_title_too_long(self):
        status, _ = self.request("POST", "/api/tasks", {"title": "a" * 501})
        self.assertEqual(status, 400)

    def test_edit_title(self):
        task = self.add("Lama")
        status, updated = self.request("PATCH", f"/api/tasks/{task['id']}", {"title": "Baru"})
        self.assertEqual(status, 200)
        self.assertEqual(updated["title"], "Baru")
        status, _ = self.request("PATCH", f"/api/tasks/{task['id']}", {"title": ""})
        self.assertEqual(status, 400)

    def test_complete_and_reopen(self):
        task = self.add()
        _, done = self.request("PATCH", f"/api/tasks/{task['id']}", {"done": True})
        self.assertTrue(done["done"])
        self.assertIsNotNone(done["completed_at"])
        _, reopened = self.request("PATCH", f"/api/tasks/{task['id']}", {"done": False})
        self.assertFalse(reopened["done"])
        self.assertIsNone(reopened["completed_at"])

    def test_done_must_be_boolean(self):
        task = self.add()
        status, _ = self.request("PATCH", f"/api/tasks/{task['id']}", {"done": "ya"})
        self.assertEqual(status, 400)

    def test_status_filter(self):
        a = self.add("A")
        b = self.add("B")
        self.request("PATCH", f"/api/tasks/{b['id']}", {"done": True})
        _, open_tasks = self.request("GET", "/api/tasks?status=open")
        _, done_tasks = self.request("GET", "/api/tasks?status=done")
        self.assertEqual([t["id"] for t in open_tasks], [a["id"]])
        self.assertEqual([t["id"] for t in done_tasks], [b["id"]])
        status, _ = self.request("GET", "/api/tasks?status=aneh")
        self.assertEqual(status, 400)

    def test_delete(self):
        task = self.add()
        self.assertEqual(self.request("DELETE", f"/api/tasks/{task['id']}"), (204, None))
        self.assertEqual(self.request("GET", "/api/tasks"), (200, []))
        status, _ = self.request("DELETE", f"/api/tasks/{task['id']}")
        self.assertEqual(status, 404)

    def test_missing_task(self):
        status, data = self.request("GET", "/api/tasks/999")
        self.assertEqual(status, 404)
        self.assertEqual(data["error"], "Tugas tidak ditemukan.")
        status, _ = self.request("PATCH", "/api/tasks/999", {"title": "x"})
        self.assertEqual(status, 404)


class DueDateAndPriorityTest(ApiTestCase):
    def add(self, title="Tugas", **extra):
        status, task = self.request("POST", "/api/tasks", {"title": title, **extra})
        self.assertEqual(status, 201, task)
        return task

    def test_defaults(self):
        task = self.add()
        self.assertIsNone(task["due_date"])
        self.assertEqual(task["priority"], "normal")

    def test_create_with_due_date_and_priority(self):
        task = self.add(due_date="2026-12-31", priority="high")
        self.assertEqual(task["due_date"], "2026-12-31")
        self.assertEqual(task["priority"], "high")

    def test_invalid_values(self):
        for extra in (
            {"due_date": "31-12-2026"},
            {"due_date": "2026-02-30"},
            {"due_date": 20261231},
            {"priority": "urgent"},
            {"priority": None},
        ):
            status, data = self.request("POST", "/api/tasks", {"title": "x", **extra})
            self.assertEqual(status, 400, extra)
            self.assertIn("error", data)

    def test_change_and_clear_due_date(self):
        task = self.add(due_date="2026-10-10")
        _, updated = self.request("PATCH", f"/api/tasks/{task['id']}", {"due_date": None, "priority": "high"})
        self.assertIsNone(updated["due_date"])
        self.assertEqual(updated["priority"], "high")
        _, updated = self.request("PATCH", f"/api/tasks/{task['id']}", {"due_date": ""})
        self.assertIsNone(updated["due_date"])

    def test_patch_title_keeps_other_fields(self):
        task = self.add(due_date="2026-10-10", priority="high")
        _, updated = self.request("PATCH", f"/api/tasks/{task['id']}", {"title": "Baru"})
        self.assertEqual(updated["due_date"], "2026-10-10")
        self.assertEqual(updated["priority"], "high")

    def test_sort_order(self):
        # Penting dulu, lalu yang deadline-nya paling dekat, tanpa deadline paling bawah.
        self.add("biasa-tanpa")
        self.add("biasa-nanti", due_date="2026-12-01")
        self.add("penting-nanti", due_date="2026-12-01", priority="high")
        self.add("biasa-dekat", due_date="2026-10-01")
        self.add("penting-tanpa", priority="high")
        _, tasks = self.request("GET", "/api/tasks?status=open")
        self.assertEqual(
            [t["title"] for t in tasks],
            ["penting-nanti", "penting-tanpa", "biasa-dekat", "biasa-nanti", "biasa-tanpa"],
        )


class TodayViewTest(ApiTestCase):
    TODAY = "2026-10-04"

    def add(self, title, **extra):
        status, task = self.request("POST", "/api/tasks", {"title": title, **extra})
        self.assertEqual(status, 201, task)
        return task

    def today_titles(self):
        status, tasks = self.request("GET", f"/api/tasks?view=today&today={self.TODAY}")
        self.assertEqual(status, 200, tasks)
        return [t["title"] for t in tasks]

    def test_shows_today_and_overdue_with_important_first(self):
        self.add("tanpa-deadline")
        self.add("besok", due_date="2026-10-05", priority="high")
        self.add("hari-ini-biasa", due_date="2026-10-04")
        self.add("terlambat-biasa", due_date="2026-10-01")
        self.add("hari-ini-penting", due_date="2026-10-04", priority="high")
        self.add("terlambat-penting", due_date="2026-09-30", priority="high")
        self.assertEqual(
            self.today_titles(),
            ["terlambat-penting", "hari-ini-penting", "terlambat-biasa", "hari-ini-biasa"],
        )

    def test_includes_tasks_completed_today(self):
        task = self.add("selesai", due_date="2026-10-04")
        _, done = self.request("PATCH", f"/api/tasks/{task['id']}", {"done": True})
        # completed_at memakai jam server; uji dengan tanggal penyelesaiannya
        completed_day = done["completed_at"][:10]
        _, tasks = self.request("GET", f"/api/tasks?view=today&today={completed_day}")
        self.assertEqual([t["title"] for t in tasks], ["selesai"])
        _, tasks = self.request("GET", "/api/tasks?view=today&today=2000-01-01")
        self.assertEqual(tasks, [])

    def test_invalid_params(self):
        self.assertEqual(self.request("GET", "/api/tasks?view=minggu")[0], 400)
        self.assertEqual(self.request("GET", "/api/tasks?view=today&today=kemarin")[0], 400)

    def test_default_today_is_server_date(self):
        from datetime import date
        self.add("hari-ini", due_date=date.today().isoformat())
        _, tasks = self.request("GET", "/api/tasks?view=today")
        self.assertEqual([t["title"] for t in tasks], ["hari-ini"])
