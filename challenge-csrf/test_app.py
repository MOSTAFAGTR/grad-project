import unittest
import requests
import time
import subprocess
import os

class TestCSRFFix(unittest.TestCase):
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

    def test_01_functional_transfer_works(self):
        print("\nRunning test: Legitimate Transfer (with Token)")
        session = requests.Session()
        
        # 1. Get form (should set session token)
        try:
            get_res = session.get(f"{self.BASE_URL}/form")
            data = get_res.json()
            token = data.get("csrf_token")
        except:
            self.fail("Could not parse JSON from /form")

        if not token or token == "TODO_IMPLEMENT_ME":
            self.fail("You must generate a random CSRF token in /form and return it.")

        # 2. Submit with token
        payload = {"to_user": "Bob", "amount": 10, "csrf_token": token}
        post_res = session.post(f"{self.BASE_URL}/transfer", data=payload)
        
        self.assertEqual(post_res.status_code, 200, "Valid transfer with token failed.")
        print("Legitimate Transfer: PASSED")

    def test_02_security_csrf_attack_fails(self):
        print("\nRunning test: CSRF Attack (No Token)")
        
        # Attack: Submit WITHOUT token
        payload = {"to_user": "Bob", "amount": 100}
        
        # The app should reject this because 'csrf_token' is missing
        response = requests.post(f"{self.BASE_URL}/transfer", data=payload)
        
        if response.status_code == 200:
            self.fail("Attack SUCCESSFUL! You failed to block the request missing the token.")
        
        if response.status_code not in [400, 401, 403]:
             self.fail(f"Expected 403 Forbidden, got {response.status_code}")

        print("CSRF Attack: PASSED (Blocked)")

if __name__ == '__main__':
    unittest.main()