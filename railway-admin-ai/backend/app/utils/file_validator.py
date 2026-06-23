import os
from app.config import settings

ALLOWED_MAGIC_SIGNATURES = {
    b"%PDF": "application/pdf",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
}

class FileValidator:
    """
    Validates uploaded files by verifying actual content (magic bytes/file signatures)
    instead of relying solely on the file extension. Prevents disguised malicious uploads.
    """

    def validate(self, file_path: str, file_size: int) -> tuple[bool, str]:
        # 1. Size Validation
        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            return False, f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB."

        # 2. File Signature (Magic Bytes) Validation
        if not os.path.exists(file_path):
            return False, "File does not exist on disk for validation."

        try:
            with open(file_path, "rb") as f:
                # Read the first 8 bytes (longest signature is PNG at 8 bytes)
                header = f.read(8)
        except Exception as e:
            return False, f"Failed to read file content: {str(e)}"

        # Check signatures
        matched_mime = None
        for sig, mime in ALLOWED_MAGIC_SIGNATURES.items():
            if header.startswith(sig):
                matched_mime = mime
                break

        if not matched_mime:
            return False, "File type is not allowed. Actual content header does not match PDF, JPG, or PNG signatures."

        return True, ""
