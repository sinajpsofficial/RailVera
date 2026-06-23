import os
import sys
from datetime import datetime
from uuid import uuid4

# Ensure backend root is in search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.utils.pdf_generator import PDFGenerator

class DummyCase:
    def __init__(self):
        self.id = uuid4()
        self.user_id = uuid4()
        self.domain = "Promotion"
        self.query_text = "Check eligibility for driver promotion."
        self.status = "evaluated"
        self.decision = "Eligible"
        self.confidence = "High"
        self.decision_reasoning = (
            "1. Verified service records demonstrate 6 continuous years of active duty in the Junior Scale, satisfying the 5-year requirement under rule PROM_001.\n"
            "2. APAR ratings for the prior 3 cycles are graded as 'Outstanding' (Rule PROM_004).\n"
            "3. Employee has successfully cleared the departmental promo exam on 01-10-2024 (Rule PROM_006)."
        )
        self.rules_applied = ["PROM_001", "PROM_004", "PROM_006"]
        self.extracted_facts = {
            "employee_name": "Chad Smith",
            "employee_id": "EMP100482",
            "department": "Transportation (Power)",
            "designation": "Locomotive Driver",
            "years_of_service": 6,
            "apar_rating": "Outstanding",
            "passed_exam": True,
            "penalty_history": []
        }
        self.created_at = datetime.now()

def test_pdf_generation():
    print("--- Running PDF Generator Verification ---")
    mock_case = DummyCase()
    
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "reports"))
    os.makedirs(output_dir, exist_ok=True)
    output_pdf_path = os.path.join(output_dir, f"test_decision_report_{mock_case.id}.pdf")
    
    # Generate PDF
    PDFGenerator.generate(mock_case, output_pdf_path)
    
    # Assertions
    print(f"Checking output file at: {output_pdf_path}")
    assert os.path.exists(output_pdf_path), "PDF file was not created!"
    file_size = os.path.getsize(output_pdf_path)
    print(f"Generated PDF File Size: {file_size} bytes")
    assert file_size > 0, "PDF file is empty!"
    
    # Verify magic bytes
    with open(output_pdf_path, 'rb') as f:
        header = f.read(4)
        assert header == b'%PDF', f"File is not a valid PDF! Header: {header}"
        
    print("PDF generation checks completed successfully!")

if __name__ == "__main__":
    test_pdf_generation()
