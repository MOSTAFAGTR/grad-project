import unittest
import requests
import time
import subprocess
import html

class TestXSSVulnerability(unittest.TestCase):
    BASE_URL = "http://localhost:5000"
    process = None

    @classmethod
    def setUpClass(cls):
        # Start the student's Flask app
        cls.process = subprocess.Popen(["gunicorn", "--bind", "0.0.0.0:5000", "app:app"])
        time.sleep(3)

    @classmethod
    def tearDownClass(cls):
        if cls.process:
            cls.process.terminate()

    def test_01_functional_comment(self):
        print("Running test: Functional Commenting")
        payload = {"content": "Hello World"}
        response = requests.post(self.BASE_URL, data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Hello World", response.text, "Standard comments should display correctly.")
        print("Functional Commenting: PASSED")

    def test_02_security_xss_prevention(self):
        print("Running test: XSS Prevention")
        xss_payload = "<script>alert('HACKED')</script>"
        
        # Send the attack
        response = requests.post(self.BASE_URL, data={"content": xss_payload})
        
        # The response text should NOT contain the raw script tag if fixed.
        # It should be escaped like &lt;script&gt;...
        
        if xss_payload in response.text:
            self.fail("Vulnerability detected! The raw <script> tag was found in the HTML.")
        
        # Check for escaped version (which means it's safe)
        escaped_payload = html.escape(xss_payload)
        # Note: jinja2/flask escape might handle quotes differently, mostly checking for brackets
        if "&lt;script&gt;" not in response.text and "&#34;" not in response.text and "&quot;" not in response.text:
             # If it's not raw AND not standard escaped, it might have been stripped entirely (which is also valid)
             pass
        else:
             # If we find escaped characters, that's good
             pass

        print("XSS Prevention: PASSED (Payload was escaped or sanitized)")

if __name__ == '__main__':
    unittest.main()