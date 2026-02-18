import unittest
import requests
import time
import subprocess

class TestCommandInjectionFix(unittest.TestCase):
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

    def test_01_allowed_ping_works(self):
        """Pinging an allowed host (8.8.8.8) should return 200 and some output."""
        r = requests.post(f"{self.BASE_URL}/ping", json={"host": "8.8.8.8"}, timeout=10)
        self.assertEqual(r.status_code, 200, "Allowed host 8.8.8.8 should return 200")
        data = r.json()
        self.assertIn("output", data, "Response must contain 'output'")
        # May be "1 packets transmitted" or "Unreachable" etc.
        self.assertTrue(isinstance(data["output"], str), "output must be string")
        print("Allowed ping 8.8.8.8: PASSED")

    def test_02_command_injection_blocked(self):
        """Injection like '8.8.8.8; id' must not execute 'id' (no 'uid=' in output)."""
        r = requests.post(
            f"{self.BASE_URL}/ping",
            json={"host": "8.8.8.8; id"},
            timeout=10
        )
        # Should still return 200 for ping part, but output must NOT contain uid= (from id command)
        data = r.json()
        self.assertIn("output", data)
        output = data["output"]
        if "uid=" in output or "gid=" in output:
            self.fail("Command injection succeeded: 'id' command ran. Block injection (use allowlist + no shell).")
        print("Command injection blocked: PASSED")

    def test_03_unknown_host_rejected(self):
        """Host not in allowlist (e.g. evil.com) should be rejected with 400 or 403."""
        r = requests.post(f"{self.BASE_URL}/ping", json={"host": "evil.com"}, timeout=5)
        self.assertIn(r.status_code, [400, 403], f"Disallowed host should be rejected, got {r.status_code}")
        print("Disallowed host rejected: PASSED")

if __name__ == '__main__':
    unittest.main()
