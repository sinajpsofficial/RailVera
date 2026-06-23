import os
import sys
import asyncio
import uuid
import pytest

# Ensure backend root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import httpx
from app.main import app
from app.config import settings

@pytest.mark.asyncio
async def test_malicious_upload():
    # Register a user
    unique = str(uuid.uuid4())[:8]
    email = f'testuser_{unique}@railway.gov.in'
    payload = {
        "employee_id": f'EMP{unique}',
        "name": "Test Employee",
        "email": email,
        "password": "securepassword123",
        "role": "employee",
        "division": "Howrah",
        "department": "Transportation"
    }
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        resp = await client.post('/api/auth/register', json=payload)
        assert resp.status_code == 201
        # Login to get token
        login_resp = await client.post('/api/auth/login', json={"email": email, "password": "securepassword123"})
        assert login_resp.status_code == 200
        token = login_resp.json()['access_token']
        headers = {"Authorization": f"Bearer {token}"}
        # Create a case
        case_resp = await client.post('/api/cases/', json={"domain": "Promotion", "query_text": "Test"}, headers=headers)
        assert case_resp.status_code == 201
        case_id = case_resp.json()['id']
        # Create malicious file (text content, renamed to .pdf)
        malicious_path = 'malicious.pdf'
        # Create malicious file
        with open(malicious_path, 'wb') as f:
            f.write(b'#!/bin/bash\necho malicious')
        # Upload malicious file using context manager to ensure closure
        with open(malicious_path, 'rb') as file_handle:
            files = {"file": ("malicious.pdf", file_handle, "application/pdf")}
            data = {"case_id": case_id}
            upload_resp = await client.post('/api/documents/upload', files=files, data=data, headers=headers)
        # Clean up file after upload
        os.remove(malicious_path)
        # Expect rejection
        assert upload_resp.status_code == 400
        assert "File type is not allowed" in upload_resp.json().get('detail', '') or "File type is not allowed" in upload_resp.text
        print('Malicious upload correctly rejected')

if __name__ == '__main__':
    asyncio.run(test_malicious_upload())
