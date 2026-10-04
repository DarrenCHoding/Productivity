from tests.helpers import ApiTestCase


class CategoryTest(ApiTestCase):
    def add_category(self, name):
        status, cat = self.request("POST", "/api/categories", {"name": name})
        self.assertEqual(status, 201, cat)
        return cat

    def add_task(self, title, **extra):
        status, task = self.request("POST", "/api/tasks", {"title": title, **extra})
        self.assertEqual(status, 201, task)
        return task

    def test_create_list_sorted(self):
        self.add_category("Pribadi")
        self.add_category("  kuliah ")
        self.add_category("Kerja")
        _, cats = self.request("GET", "/api/categories")
        self.assertEqual([c["name"] for c in cats], ["Kerja", "kuliah", "Pribadi"])
        self.assertEqual(cats[0]["open_count"], 0)
        self.assertEqual(cats[0]["total_count"], 0)

    def test_name_validation_and_duplicates(self):
        self.add_category("Kerja")
        for body in ({}, {"name": " "}, {"name": "x" * 51}, {"name": 1}):
            self.assertEqual(self.request("POST", "/api/categories", body)[0], 400, body)
        status, data = self.request("POST", "/api/categories", {"name": "kerja"})
        self.assertEqual(status, 409)
        self.assertEqual(data["error"], "Kategori dengan nama itu sudah ada.")

    def test_rename(self):
        kerja = self.add_category("Kerja")
        self.add_category("Pribadi")
        status, renamed = self.request("PATCH", f"/api/categories/{kerja['id']}", {"name": "Kantor"})
        self.assertEqual((status, renamed["name"]), (200, "Kantor"))
        # ganti huruf besar/kecil nama sendiri boleh
        status, _ = self.request("PATCH", f"/api/categories/{kerja['id']}", {"name": "KANTOR"})
        self.assertEqual(status, 200)
        status, _ = self.request("PATCH", f"/api/categories/{kerja['id']}", {"name": "pribadi"})
        self.assertEqual(status, 409)
        self.assertEqual(self.request("PATCH", "/api/categories/999", {"name": "X"})[0], 404)

    def test_task_with_category_and_counts(self):
        kerja = self.add_category("Kerja")
        task = self.add_task("Laporan", category_id=kerja["id"])
        self.assertEqual(task["category_id"], kerja["id"])
        self.assertEqual(task["category_name"], "Kerja")
        done = self.add_task("Rapat", category_id=kerja["id"])
        self.request("PATCH", f"/api/tasks/{done['id']}", {"done": True})
        _, cats = self.request("GET", "/api/categories")
        self.assertEqual((cats[0]["open_count"], cats[0]["total_count"]), (1, 2))
        # nama kategori di tugas ikut berubah saat kategori diganti nama
        self.request("PATCH", f"/api/categories/{kerja['id']}", {"name": "Kantor"})
        _, fetched = self.request("GET", f"/api/tasks/{task['id']}")
        self.assertEqual(fetched["category_name"], "Kantor")

    def test_invalid_category_on_task(self):
        for value in (999, "1", True, 1.5):
            status, _ = self.request("POST", "/api/tasks", {"title": "x", "category_id": value})
            self.assertEqual(status, 400, value)

    def test_change_and_remove_category_of_task(self):
        kerja = self.add_category("Kerja")
        task = self.add_task("Laporan")
        self.assertIsNone(task["category_id"])
        _, task = self.request("PATCH", f"/api/tasks/{task['id']}", {"category_id": kerja["id"]})
        self.assertEqual(task["category_name"], "Kerja")
        _, task = self.request("PATCH", f"/api/tasks/{task['id']}", {"category_id": None})
        self.assertIsNone(task["category_id"])
        self.assertIsNone(task["category_name"])

    def test_delete_category_keeps_tasks(self):
        kerja = self.add_category("Kerja")
        task = self.add_task("Laporan", category_id=kerja["id"])
        self.assertEqual(self.request("DELETE", f"/api/categories/{kerja['id']}"), (204, None))
        _, fetched = self.request("GET", f"/api/tasks/{task['id']}")
        self.assertIsNone(fetched["category_id"])
        self.assertEqual(self.request("GET", "/api/categories"), (200, []))
        self.assertEqual(self.request("DELETE", f"/api/categories/{kerja['id']}")[0], 404)

    def test_filter_tasks_by_category(self):
        kerja = self.add_category("Kerja")
        kuliah = self.add_category("Kuliah")
        self.add_task("A", category_id=kerja["id"], due_date="2026-10-04")
        self.add_task("B", category_id=kuliah["id"], due_date="2026-10-04")
        self.add_task("C", due_date="2026-10-04")
        self.add_task("D", category_id=kerja["id"])

        def titles(query):
            status, tasks = self.request("GET", "/api/tasks" + query)
            self.assertEqual(status, 200, tasks)
            return [t["title"] for t in tasks]

        self.assertEqual(titles(f"?category={kerja['id']}"), ["A", "D"])
        self.assertEqual(titles("?category=none"), ["C"])
        self.assertEqual(titles(f"?view=today&today=2026-10-04&category={kerja['id']}"), ["A"])
        self.assertEqual(titles("?category=999"), [])
        self.assertEqual(self.request("GET", "/api/tasks?category=abc")[0], 400)
