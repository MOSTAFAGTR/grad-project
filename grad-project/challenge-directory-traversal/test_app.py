import subprocess
import time
import unittest

import requests


class TestDirectoryTraversalFix(unittest.TestCase):
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

    def test_01_normal_file_works(self):
        r = requests.get(f"{self.BASE_URL}/file", params={"name": "report.txt"}, timeout=8)
        self.assertEqual(r.status_code, 200, "Reading normal file should work")
        self.assertIn("content", r.json())

    def test_02_traversal_blocked(self):
        r = requests.get(f"{self.BASE_URL}/file", params={"name": "../../etc/passwd"}, timeout=8)
        self.assertIn(r.status_code, [400, 403], "Traversal payload must be blocked")


if __name__ == "__main__":
    unittest.main()
