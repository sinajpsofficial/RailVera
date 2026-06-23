import requests
import json

payload = {
    "employee_id": "TEST_EMP_999",
    "name": "Test User",
    "email": "test999@test.com",
    "password": "Password123",
    "role": "employee",
    "division": "Howrah",
    "department": "Mechanical"
}

try:
    print("Sending POST request to register...")
    response = requests.post("http://localhost:8000/api/auth/register", json=payload, timeout=30)
    print("Response Status Code:", response.status_code)
    print("Response Body:", response.text)
except Exception as e:
    print("Error occurred:", e)
