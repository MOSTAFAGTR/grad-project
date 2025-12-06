import unittest
import requests
import time
import subprocess

class TestVulnerability(unittest.TestCase):
    BASE_URL = "http://localhost:5000"
    process = None

    @classmethod
    def setUpClass(cls):
        # Start the student's Flask app.
        # The 'app:app' tells gunicorn where to find the Flask instance.
        cls.process = subprocess.Popen(["gunicorn", "--bind", "0.0.0.0:5000", "app:app"])
        # Give the server a moment to start
        time.sleep(3)

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()

    def test_01_functional_login_works(self):
        print("Running test: Functional Login")
        payload = {"username": "admin", "password": "password123"}
        response = requests.post(f"{self.BASE_URL}/login", json=payload)
        self.assertEqual(response.status_code, 200, "A correct login with user 'admin' should succeed (200 OK).")
        self.assertIn("Login successful", response.json().get("message", ""), "Success message not found for valid login.")
        print("Functional Login: PASSED")


    def test_02_security_sql_injection_fails(self):
        print("Running test: SQL Injection Attack")
        malicious_payload = {"username": "admin' OR '1'='1' -- ", "password": "any_password"}
        response = requests.post(f"{self.BASE_URL}/login", json=malicious_payload)
        self.assertNotEqual(response.status_code, 200, "The SQL injection exploit succeeded, but it should fail. The vulnerability is still present.")
        self.assertEqual(response.status_code, 401, "The application should return 401 Unauthorized for a failed login attempt.")
        print("SQL Injection Attack: PASSED (Exploit Blocked)")

if __name__ == '__main__':
    unittest.main() 
    