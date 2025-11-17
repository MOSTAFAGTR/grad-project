import unittest
import requests
import time
import subprocess


class TestXSSChallenge(unittest.TestCase):
    BASE_URL = "http://localhost:5000"
    process = None

    @classmethod
    def setUpClass(cls):
        cls.process = subprocess.Popen(["gunicorn", "--bind", "0.0.0.0:5000", "app:app"])
        time.sleep(3)

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()

    def test_01_post_and_get_works(self):
        print("Running test: Functional message post and retrieve")
        payload = {"message": "Hello world"}
        r = requests.post(f"{self.BASE_URL}/post", json=payload)
        self.assertEqual(r.status_code, 200)

        r2 = requests.get(f"{self.BASE_URL}/messages")
        self.assertEqual(r2.status_code, 200)
        self.assertIn("Hello world", r2.text)
        print("Functional message: PASSED")

    def test_02_xss_attack_fails(self):
        """This test tries to post a script tag and asserts that the rendered
        page does not contain the script unescaped.
        """
        print("Running test: XSS Attack")
        malicious = {"message": "<script>alert('XSS')</script>"}
        r = requests.post(f"{self.BASE_URL}/post", json=malicious)
        self.assertEqual(r.status_code, 200)

        r2 = requests.get(f"{self.BASE_URL}/messages")
        self.assertEqual(r2.status_code, 200)

        # If the app is vulnerable, the raw script tag will appear on the page
        self.assertNotIn("<script>alert('XSS')</script>", r2.text,
                         "The XSS payload was rendered raw on the page. The vulnerability is still present.")

        print("XSS Attack: PASSED (Exploit Blocked)")


if __name__ == '__main__':
    unittest.main()
