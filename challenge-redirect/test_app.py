import unittest
import requests
import time
import subprocess

class TestRedirectFix(unittest.TestCase):
    BASE_URL = "http://localhost:5000"
    process = None

    @classmethod
    def setUpClass(cls):
        cls.process = subprocess.Popen(["gunicorn", "--bind", "0.0.0.0:5000", "app:app"])
        time.sleep(3)

    @classmethod
    def tearDownClass(cls):
        if cls.process:
            cls.process.terminate()

    def test_01_allowed_redirect_works(self):
        """Allowed path /dashboard should redirect (302) and Location should be /dashboard."""
        r = requests.get(f"{self.BASE_URL}/go", params={"next": "/dashboard"}, allow_redirects=False)
        self.assertEqual(r.status_code, 302, "Allowed path /dashboard should return 302 redirect")
        self.assertIn("Location", r.headers, "Redirect must set Location header")
        loc = r.headers["Location"]
        self.assertTrue(loc.endswith("/dashboard") or loc == "/dashboard",
                        f"Location should be /dashboard, got {loc}")
        print("Allowed redirect /dashboard: PASSED")

    def test_02_external_redirect_blocked(self):
        """Redirect to https://evil.com must be rejected (400 or 403), not 302."""
        r = requests.get(f"{self.BASE_URL}/go", params={"next": "https://evil.com"}, allow_redirects=False)
        if r.status_code == 302:
            loc = r.headers.get("Location", "")
            if "evil.com" in loc or "http" in loc:
                self.fail("Open redirect to external URL must be blocked (got 302 to " + loc + ")")
        self.assertIn(r.status_code, [400, 403], f"Expected 400/403 for external URL, got {r.status_code}")
        print("External redirect blocked: PASSED")

    def test_03_relative_path_only(self):
        """Only relative paths from allowlist should be accepted; protocol-relative or absolute rejected."""
        r = requests.get(f"{self.BASE_URL}/go", params={"next": "//evil.com"}, allow_redirects=False)
        self.assertIn(r.status_code, [400, 403], f"//evil.com must be rejected, got {r.status_code}")
        print("Protocol-relative blocked: PASSED")

if __name__ == '__main__':
    unittest.main()
