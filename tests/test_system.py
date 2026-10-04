from tests.helpers import ApiTestCase


class SystemTest(ApiTestCase):
    def test_health(self):
        self.assertEqual(self.request("GET", "/api/health"), (200, {"status": "ok"}))

    def test_unknown_api_returns_404_in_indonesian(self):
        status, data = self.request("GET", "/api/tidak-ada")
        self.assertEqual(status, 404)
        self.assertIn("tidak ditemukan", data["error"])

    def test_wrong_method_returns_405(self):
        status, _ = self.request("DELETE", "/api/health")
        self.assertEqual(status, 405)

    def test_serves_index_page(self):
        status, html = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("<title>Productivity</title>", html)

    def test_invalid_json_returns_400(self):
        import urllib.error
        import urllib.request
        req = urllib.request.Request(
            self.base_url + "/api/health", data=b"{bukan json", method="GET"
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 400)


class ServerProtectionTest(ApiTestCase):
    def raw_get(self, path):
        """Kirim alamat apa adanya (tanpa dirapikan), seperti yang bisa dilakukan orang iseng."""
        import http.client
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_address[1], timeout=5)
        try:
            conn.request("GET", path)
            res = conn.getresponse()
            return res.status, res.getheader("Content-Type"), res.read()
        finally:
            conn.close()

    def test_static_files_have_correct_types(self):
        # Penting di Windows: .js yang dikirim sebagai teks biasa membuat tampilan tidak jalan.
        for path, expected in (
            ("/js/app.js", "text/javascript"),
            ("/css/style.css", "text/css"),
            ("/index.html", "text/html"),
        ):
            status, content_type, _ = self.raw_get(path)
            self.assertEqual(status, 200, path)
            self.assertTrue(content_type.startswith(expected), (path, content_type))

    def test_browser_always_checks_for_new_version(self):
        status, headers, _ = self.request_raw("GET", "/js/app.js")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Cache-Control"], "no-cache")

    def test_cannot_read_files_outside_static_folder(self):
        for path in (
            "/../server.py",
            "/../app/db.py",
            "/%2e%2e/app/db.py",
            "/js/../../app/db.py",
            "/../data/productivity.db",
        ):
            status, _, body = self.raw_get(path)
            self.assertNotIn(b"import ", body, path)
            self.assertNotEqual(status, 200, path)

    def test_json_body_too_large(self):
        status, data = self.request("POST", "/api/tasks", {"title": "x" * 1_100_000})
        self.assertEqual(status, 413)
        self.assertEqual(data["error"], "Data yang dikirim terlalu besar.")

    def test_upload_too_large_is_rejected_without_touching_data(self):
        from unittest import mock
        self.request("POST", "/api/tasks", {"title": "Aman"})
        with mock.patch("app.server.MAX_UPLOAD_BYTES", 100):
            status, _, _ = self.request_raw("POST", "/api/backup/restore", b"x" * 500)
        self.assertEqual(status, 413)
        self.assertEqual([t["title"] for t in self.request("GET", "/api/tasks")[1]], ["Aman"])


class OtherSiteProtectionTest(ApiTestCase):
    """Situs lain yang dibuka di browser tidak boleh bisa mengubah data aplikasi."""

    def send(self, method, path, body, origin):
        import http.client
        import json as _json
        port = self.server.server_address[1]
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        try:
            headers = {"Content-Type": "text/plain", "Host": f"127.0.0.1:{port}"}
            if origin:
                headers["Origin"] = origin
            conn.request(method, path, _json.dumps(body), headers)
            return conn.getresponse().status
        finally:
            conn.close()

    def test_request_from_other_site_is_rejected(self):
        for origin in ("http://situs-jahat.example", "null", "http://127.0.0.1:9999"):
            self.assertEqual(self.send("POST", "/api/tasks", {"title": "Dari situs jahat"}, origin), 403, origin)
        self.assertEqual(self.request("GET", "/api/tasks")[1], [])

    def test_request_from_the_app_itself_is_allowed(self):
        port = self.server.server_address[1]
        self.assertEqual(self.send("POST", "/api/tasks", {"title": "Dari aplikasi"}, f"http://127.0.0.1:{port}"), 201)

    def test_reading_is_not_affected(self):
        import http.client
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_address[1], timeout=5)
        conn.request("GET", "/api/health", headers={"Origin": "http://situs-jahat.example"})
        res = conn.getresponse()
        self.assertEqual(res.status, 200)
        # Tanpa izin CORS, browser tidak mengizinkan situs lain membaca jawabannya.
        self.assertIsNone(res.getheader("Access-Control-Allow-Origin"))
        conn.close()
