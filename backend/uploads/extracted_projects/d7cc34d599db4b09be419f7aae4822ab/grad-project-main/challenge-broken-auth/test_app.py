import unittest
import requests
import time
import subprocess

class TestBrokenAuthFix(unittest.TestCase):
    BASE_URL = "http://localhost:5000"
    process = None 

    @classmethod
    def setUpClass(cls):
        cls.process = subprocess.Popen(["gunicorn", "--bind", "0.0.0.0:5000", "app:app"])
        time.sleep(3)

    @classmethod
    def tearDownClass(cls):
        if cls.process: cls.process.terminate()

    def test_01_brute_force_protection(self):
        print("\nRunning test: Brute Force Simulation")
        
        # 1. Send 5 bad requests rapidly
        for i in range(5):
            requests.post(f"{self.BASE_URL}/login", json={"username": "admin", "password": f"wrong{i}"})
        
        # 2. Immediately send a CORRECT request
        # If vulnerability exists: This returns 200 OK (Test Fails)
        # If fixed: This should return 429 (Too Many Requests) or 403 (Forbidden)
        response = requests.post(f"{self.BASE_URL}/login", json={"username": "admin", "password": "complex_password_123"})
        
        if response.status_code == 200:
            self.fail("Brute Force Attack Succeeded! You allowed the attacker to login immediately after 5 failed attempts.")
        
        print("Brute Force Blocked (Good job!)")
        
        # 3. Wait for cooldown (assuming student set ~2 seconds)
        print("Waiting for cooldown...")
        time.sleep(3)
        
        # 4. Try again - should succeed now
        response_retry = requests.post(f"{self.BASE_URL}/login", json={"username": "admin", "password": "complex_password_123"})
        self.assertEqual(response_retry.status_code, 200, "Valid login failed after cooldown period.")
        print("Login recovered after cooldown: PASSED")

if __name__ == '__main__':
    unittest.main()