import subprocess
import time
import unittest

import requests


def _response_suggests_file_leak(data: dict) -> bool:
    blob = f"{data.get('parsed_output') or ''}{data.get('sensitive_data') or ''}"
    return "root:" in blob or "/bin/bash" in blob or "/bin/sh" in blob


class TestXxeFix(unittest.TestCase):
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

    def test_01_normal_xml_parses(self):
        xml_payload = "<root><a>ok</a></root>"
        r = requests.post(f"{self.BASE_URL}/parse", json={"xml": xml_payload}, timeout=8)
        self.assertEqual(r.status_code, 200, "Normal XML should parse successfully")
        self.assertFalse(_response_suggests_file_leak(r.json()), "Normal XML must not expose system file content")

    def test_02_external_entity_blocked(self):
        xml_payload = """<?xml version='1.0'?>
<!DOCTYPE foo [ <!ENTITY xxe SYSTEM 'file:///etc/passwd'> ]>
<root>&xxe;</root>"""
        r = requests.post(f"{self.BASE_URL}/parse", json={"xml": xml_payload}, timeout=8)
        if r.status_code == 200 and _response_suggests_file_leak(r.json()):
            self.fail("XXE payload still returns system file markers. External entities must be blocked.")
        self.assertIn(r.status_code, [200, 400, 403], "Endpoint should handle malicious XML safely")


if __name__ == "__main__":
    unittest.main()
