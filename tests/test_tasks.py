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
