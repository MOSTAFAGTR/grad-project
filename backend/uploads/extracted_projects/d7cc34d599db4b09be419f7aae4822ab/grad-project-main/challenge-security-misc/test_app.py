import unittest
import requests
import time
import subprocess

class TestSecurityMiscFix(unittest.TestCase):
    BASE_URL = "http://localhost:5000"
    process = None 

    @classmethod
    def setUpClass(cls):
        # We run directly with python to capture the debug mode behavior better than gunicorn for this specific test
        cls.process = subprocess.Popen(["python", "app.py"])
        time.sleep(3)

    @classmethod
    def tearDownClass(cls):
        if cls.process: cls.process.terminate()

    def test_01_debug_mode_disabled(self):
        print("\nRunning test: Check Debug Information Leak")
        try:
            response = requests.get(f"{self.BASE_URL}/crash")
        except:
            # If connection dies, that's fine, but we expect a 500
            pass
            
        # If Debug is ON, Flask returns a formatted HTML traceback or text containing python paths
        content = response.text
        
        if "Traceback (most recent call last)" in content or "ZeroDivisionError" in content:
            self.fail("Security Misconfiguration: Stack trace detected! You must disable DEBUG mode.")
        
        self.assertEqual(response.status_code, 500, "Server should return 500 error.")
        print("Debug Mode Disabled: PASSED")

    def test_02_default_credentials_changed(self):
        print("\nRunning test: Check Default Credentials")
        response = requests.post(f"{self.BASE_URL}/login", json={"username": "admin", "password": "admin"})
        
        if response.status_code == 200:
            self.fail("You are still using the default credentials (admin:admin)!")
            
        print("Default Credentials Changed: PASSED")

if __name__ == '__main__':
    unittest.main()