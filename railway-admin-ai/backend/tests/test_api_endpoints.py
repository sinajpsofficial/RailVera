import os
import sys
import uuid
import asyncio
import httpx
import pytest

# Ensure backend root is in search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.database.connection import AsyncSessionLocal
from app.models.user import User
from app.models.case import Case
from app.models.document import Document
from app.models.eligibility_report import EligibilityReport
from sqlalchemy import select, delete

@pytest.mark.asyncio

async def test_all_api_endpoints():
    print("--- Running API Endpoints Integration Tests (AsyncClient) ---")
    
    # Generate unique emails and employee ids to avoid database conflicts
    unique_id = str(uuid.uuid4())[:8]
    email = f"testuser_{unique_id}@railway.gov.in"
    employee_id = f"EMP{unique_id}"
    password = "securepassword123"
    name = "Test Employee"
    
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        # ── Test 1: User Registration ──
        print("\n[Test 1] Registering test user...")
        register_payload = {
            "employee_id": employee_id,
            "name": name,
            "email": email,
            "password": password,
            "role": "employee",
            "division": "Howrah",
            "department": "Transportation"
        }
        
        response = await ac.post("/api/auth/register", json=register_payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 201
        user_data = response.json()
        user_id = user_data["id"]
        assert user_data["email"] == email
        
        # ── Test 2: User Login & JWT Generation ──
        print("\n[Test 2] Logging in user to obtain JWT...")
        login_payload = {
            "email": email,
            "password": password
        }
        response = await ac.post("/api/auth/login", json=login_payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        token_data = response.json()
        access_token = token_data["access_token"]
        assert token_data["token_type"] == "bearer"
        
        headers = {"Authorization": f"Bearer {access_token}"}

        async def wait_for_doc(doc_id):
            for _ in range(50):
                res = await ac.get(f"/api/documents/{doc_id}/status", headers=headers)
                assert res.status_code == 200
                data = res.json()
                if data["processing_status"] in ["done", "failed"]:
                    return data
                await asyncio.sleep(0.1)
            return data
        # ── Test 3: Get Current User (Me) ──
        print("\n[Test 3] Fetching current user details using token...")
        response = await ac.get("/api/auth/me", headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        assert response.json()["id"] == user_id
        
        # ── Test 4: Create Case ──
        print("\n[Test 4] Creating an eligibility case...")
        case_payload = {
            "domain": "Promotion",
            "query_text": "Am I eligible for promotion to Senior Driver?"
        }
        response = await ac.post("/api/cases/", json=case_payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 201
        case_data = response.json()
        case_id = case_data["id"]
        assert case_data["domain"] == "Promotion"
        assert "Service Book" in case_data["required_documents"]
        
        # ── Test 5: Upload Document ──
        print("\n[Test 5] Uploading simulated service book document...")
        dummy_filename = "service_book.pdf"
        dummy_content = b"%PDF-1.4 ... dummy content simulating a Service Book with employee name Chad and date of appointment 15-08-2020 ..."
        
        # httpx AsyncClient multipart file structure
        files = {"file": (dummy_filename, dummy_content, "application/pdf")}
        data = {"case_id": case_id}
        
        response = await ac.post("/api/documents/upload", files=files, data=data, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 201
        doc_data = response.json()
        doc_id = doc_data["id"]
        doc_data = await wait_for_doc(doc_id)
        assert doc_data["document_type"] == "Service Book"
        assert doc_data["extracted_facts"].get("employee_name") == "Chad"
        
        # ── Test 6: Check Case Status after upload ──
        print("\n[Test 6] Verification of updated case data (submitted/missing documents)...")
        response = await ac.get(f"/api/cases/{case_id}", headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        updated_case_data = response.json()
        assert "Service Book" in updated_case_data["submitted_documents"]
        assert "Service Book" not in updated_case_data["missing_documents"]
        
        # ── Test 7: Upload remaining required documents to unblock the case ──
        print("\n[Test 7] Uploading remaining documents (APAR and Exam Result)...")
        # Upload APAR
        response = await ac.post(
            "/api/documents/upload",
            files={"file": ("apar_report.pdf", b"%PDF-1.4 ... APAR Outstanding rating ...", "application/pdf")},
            data={"case_id": case_id},
            headers=headers
        )
        assert response.status_code == 201
        apar_id = response.json()["id"]
        
        # Upload Departmental Exam
        response = await ac.post(
            "/api/documents/upload",
            files={"file": ("exam_ldce.pdf", b"%PDF-1.4 ... Chad passed the examination ...", "application/pdf")},
            data={"case_id": case_id},
            headers=headers
        )
        assert response.status_code == 201
        exam_id = response.json()["id"]

        # Wait for background processing to complete
        await wait_for_doc(apar_id)
        await wait_for_doc(exam_id)
        
        # Verify case is now unblocked
        response = await ac.get(f"/api/cases/{case_id}", headers=headers)
        case_status_data = response.json()
        print(f"Case status after uploading all mandatory documents: {case_status_data['status']}")
        print(f"Missing documents list: {case_status_data['missing_documents']}")
        
        # ── Test 8: Run Eligibility Check ──
        print("\n[Test 8] Running eligibility evaluation check...")
        check_payload = {"case_id": case_id}
        response = await ac.post("/api/eligibility/check", json=check_payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        check_data = response.json()
        assert check_data["case_id"] == case_id
        assert check_data["decision"] in ["Eligible", "Not Eligible", "Cannot Determine"]
        
        # ── Test 9: Generate Report PDF ──
        print("\n[Test 9] Generating final report PDF...")
        report_payload = {"case_id": case_id}
        response = await ac.post("/api/reports/generate", json=report_payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 201
        report_data = response.json()
        report_id = report_data["id"]
        assert report_data["case_id"] == case_id
        assert report_data["report_pdf_path"] is not None
        
        # ── Test 10: Retrieve Report Metadata ──
        print("\n[Test 10] Fetching report details...")
        response = await ac.get(f"/api/reports/{report_id}", headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        assert response.json()["id"] == report_id
        
        # ── Test 10b: Download Report PDF File ──
        print("\n[Test 10b] Downloading report PDF file...")
        response = await ac.get(f"/api/reports/{report_id}/download", headers=headers)
        print(f"Status Code: {response.status_code}")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.content.startswith(b"%PDF")
        print("PDF download verification successful!")
        
        # ── Test 11: Cleanup DB ──
        print("\n[Test 11] Cleaning up created test entities from the database...")
        async with AsyncSessionLocal() as db:
            # Delete eligibility reports
            await db.execute(delete(EligibilityReport).where(EligibilityReport.case_id == uuid.UUID(case_id)))
            # Delete documents
            await db.execute(delete(Document).where(Document.case_id == uuid.UUID(case_id)))
            # Delete cases
            await db.execute(delete(Case).where(Case.id == uuid.UUID(case_id)))
            # Delete user
            await db.execute(delete(User).where(User.id == uuid.UUID(user_id)))
            await db.commit()

        # Dispose database engine to avoid event loop conflicts with subsequent tests
        from app.database.connection import engine
        await engine.dispose()
            
    print("\nAll integration tests passed successfully!")

if __name__ == "__main__":
    asyncio.run(test_all_api_endpoints())
