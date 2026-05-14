import subprocess
import time
import unittest

import requests


class TestStorageFix(unittest.TestCase):
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

    def test_01_register_works(self):
        r = requests.post(
            f"{self.BASE_URL}/register",
            json={"username": "alice", "password": "password123"},
            timeout=8,
        )
        self.assertEqual(r.status_code, 200, "Register endpoint should work")

    def test_02_dump_does_not_expose_plaintext(self):
        plain = "supersecret"
        requests.post(
            f"{self.BASE_URL}/register",
            json={"username": "bob", "password": plain},
            timeout=8,
        )
        r = requests.get(f"{self.BASE_URL}/dump", timeout=8)
        self.assertEqual(r.status_code, 200)
        users = (r.json() or {}).get("users", {})
        bob = users.get("bob", {})
        stored = bob.get("password") or bob.get("password_hash")
        self.assertTrue(stored, "Stored credential value is missing")
        self.assertNotEqual(stored, plain, "Plaintext password is still exposed in storage dump")


if __name__ == "__main__":
    unittest.main()
