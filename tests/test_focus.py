from datetime import date

from tests.helpers import ApiTestCase


class SettingsTest(ApiTestCase):
    def test_defaults(self):
        status, settings = self.request("GET", "/api/settings")
        self.assertEqual(status, 200)
        self.assertEqual(settings["focus_work_minutes"], 25)
        self.assertEqual(settings["focus_break_minutes"], 5)

    def test_update_and_keep(self):
        status, settings = self.request("PATCH", "/api/settings", {"focus_work_minutes": 50})
        self.assertEqual(status, 200)
        self.assertEqual(settings["focus_work_minutes"], 50)
        self.assertEqual(settings["focus_break_minutes"], 5)
        self.request("PATCH", "/api/settings", {"focus_work_minutes": 45, "focus_break_minutes": 10})
        _, settings = self.request("GET", "/api/settings")
        self.assertEqual((settings["focus_work_minutes"], settings["focus_break_minutes"]), (45, 10))

    def test_invalid(self):
        for body in (
            {"focus_work_minutes": 0},
            {"focus_work_minutes": 181},
            {"focus_work_minutes": "25"},
            {"focus_work_minutes": 2.5},
            {"focus_break_minutes": True},
            {"tidak_ada": 1},
            {},
            None,
        ):
            self.assertEqual(self.request("PATCH", "/api/settings", body)[0], 400, body)


class FocusSessionTest(ApiTestCase):
    def add_task(self, title="Tugas"):
        return self.request("POST", "/api/tasks", {"title": title})[1]

    def log(self, **body):
        return self.request("POST", "/api/focus/sessions", body)

    def test_log_session_and_task_total(self):
        task = self.add_task()
        self.assertEqual(task["focus_seconds"], 0)
        status, session = self.log(task_id=task["id"], duration_seconds=1500)
        self.assertEqual(status, 201, session)
        self.assertEqual(session["task_title"], "Tugas")
        self.assertTrue(session["completed"])
        self.log(task_id=task["id"], duration_seconds=600, completed=False)
        _, fetched = self.request("GET", f"/api/tasks/{task['id']}")
        self.assertEqual(fetched["focus_seconds"], 2100)
        # total juga muncul di daftar tugas
        _, tasks = self.request("GET", "/api/tasks")
        self.assertEqual(tasks[0]["focus_seconds"], 2100)

    def test_session_without_task(self):
        status, session = self.log(duration_seconds=300)
        self.assertEqual(status, 201)
        self.assertIsNone(session["task_id"])

    def test_invalid_sessions(self):
        for body in (
            {"duration_seconds": 0},
            {"duration_seconds": 6 * 3600 + 1},
            {"duration_seconds": "60"},
            {"duration_seconds": 60, "task_id": 999},
            {"duration_seconds": 60, "task_id": "1"},
            {"duration_seconds": 60, "completed": "ya"},
        ):
            self.assertEqual(self.log(**body)[0], 400, body)

    def test_list_by_date(self):
        task = self.add_task("Laporan")
        self.log(task_id=task["id"], duration_seconds=1500)
        self.log(duration_seconds=300)
        _, today = self.request("GET", f"/api/focus/sessions?date={date.today().isoformat()}")
        self.assertEqual(len(today), 2)
        self.assertEqual(sum(s["duration_seconds"] for s in today), 1800)
        _, other = self.request("GET", "/api/focus/sessions?date=2000-01-01")
        self.assertEqual(other, [])
        _, all_sessions = self.request("GET", "/api/focus/sessions")
        self.assertEqual(len(all_sessions), 2)

    def test_deleting_task_keeps_history(self):
        task = self.add_task()
        self.log(task_id=task["id"], duration_seconds=1500)
        self.request("DELETE", f"/api/tasks/{task['id']}")
        _, sessions = self.request("GET", "/api/focus/sessions")
        self.assertEqual(len(sessions), 1)
        self.assertIsNone(sessions[0]["task_id"])

    def test_delete_session(self):
        _, session = self.log(duration_seconds=60)
        self.assertEqual(self.request("DELETE", f"/api/focus/sessions/{session['id']}"), (204, None))
        self.assertEqual(self.request("DELETE", f"/api/focus/sessions/{session['id']}")[0], 404)
