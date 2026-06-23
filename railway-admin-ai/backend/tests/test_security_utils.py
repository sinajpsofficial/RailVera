import os
import sys

# Ensure backend root is in search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.utils.security_logging import mask_pii
from app.utils.file_validator import FileValidator
from app.config import settings

def test_pii_masking():
    print("--- Testing PII Masking ---")
    
    # 1. Test Aadhaar masking
    assert mask_pii("My Aadhaar is 1234-5678-9012.") == "My Aadhaar is [AADHAAR]."
    assert mask_pii("Aadhaar: 9876 5432 1098") == "Aadhaar: [AADHAAR]"
    assert mask_pii("Aadhaar: 111122223333") == "Aadhaar: [AADHAAR]"
    
    # 2. Test PAN card masking
    assert mask_pii("My PAN card number is ABCDE1234F.") == "My PAN card number is [PAN]."
    assert mask_pii("PAN: XYZWP0987A") == "PAN: [PAN]"
    
    # 3. Test Mobile number masking
    assert mask_pii("Call me on +919876543210.") == "Call me on [PHONE]."
    assert mask_pii("My phone number is 9876543210") == "My phone number is [PHONE]"
    assert mask_pii("08765432109") == "[PHONE]"
    assert mask_pii("Call 9112345678") == "Call [PHONE]"
    
    # 4. Test Email masking
    assert mask_pii("Email us at contact@railway.gov.in.") == "Email us at [EMAIL]."
    assert mask_pii("test.user+alias@gmail.com") == "[EMAIL]"
    
    # 5. Test Employee ID masking
    assert mask_pii("Employee EMP123456 has joined.") == "Employee [EMPLOYEE_ID] has joined."
    assert mask_pii("ID is emp789_abc") == "ID is [EMPLOYEE_ID]"
    
    print("PII masking tests passed!")

def test_file_validator():
    print("--- Testing File Validator ---")
    
    validator = FileValidator()
    
    # Paths for dummy test files
    temp_pdf_path = "temp_test_valid.pdf"
    temp_png_path = "temp_test_valid.png"
    temp_jpeg_path = "temp_test_valid.jpeg"
    temp_bad_path = "temp_test_malicious.pdf"
    
    # 1. Test non-existent file
    valid, err_msg = validator.validate("non_existent_file.pdf", 100)
    assert not valid
    assert "does not exist" in err_msg
    
    try:
        # Create valid PDF dummy file
        with open(temp_pdf_path, "wb") as f:
            f.write(b"%PDF-1.4\n%EOF")
            
        # Create valid PNG dummy file
        with open(temp_png_path, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\nExtra png data")
            
        # Create valid JPEG dummy file
        with open(temp_jpeg_path, "wb") as f:
            f.write(b"\xff\xd8\xff\xe0Extra jpeg data")
            
        # Create disguised/malicious text file renamed to .pdf
        with open(temp_bad_path, "wb") as f:
            f.write(b"#!/bin/bash\necho 'Malicious script pretending to be pdf'")
            
        # 2. Test valid PDF validation
        valid, err_msg = validator.validate(temp_pdf_path, 15)
        assert valid, f"Valid PDF failed: {err_msg}"
        
        # 3. Test valid PNG validation
        valid, err_msg = validator.validate(temp_png_path, 25)
        assert valid, f"Valid PNG failed: {err_msg}"
        
        # 4. Test valid JPEG validation
        valid, err_msg = validator.validate(temp_jpeg_path, 30)
        assert valid, f"Valid JPEG failed: {err_msg}"
        
        # 5. Test disguised file validation (magic bytes mismatch)
        valid, err_msg = validator.validate(temp_bad_path, 55)
        assert not valid, "Disguised file was incorrectly validated as valid!"
        assert "Actual content header does not match" in err_msg
        
        # 6. Test file size validation limits
        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        valid, err_msg = validator.validate(temp_pdf_path, max_bytes + 1)
        assert not valid, "File exceeding max size limit was validated as valid!"
        assert "exceeds maximum allowed size" in err_msg
        
        print("File validator tests passed!")
        
    finally:
        # Clean up temporary test files
        for path in [temp_pdf_path, temp_png_path, temp_jpeg_path, temp_bad_path]:
            if os.path.exists(path):
                os.remove(path)

if __name__ == "__main__":
    test_pii_masking()
    test_file_validator()
    print("\nAll security utility tests passed successfully!")
