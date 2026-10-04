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
