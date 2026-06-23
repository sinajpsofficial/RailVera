import os
import uuid
import shutil
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.database.connection import get_db
from app.models.document import Document
from app.models.case import Case
from app.schemas.document import DocumentResponse
from app.core.security import get_current_user
from app.models.user import User
from app.config import settings

from app.document_intelligence.ocr_engine import OCREngine
from app.document_intelligence.document_classifier import DocumentClassifier
from app.document_intelligence.extractors.service_book_extractor import ServiceBookExtractor
from app.core.document_demand_engine import DocumentDemandEngine
from app.utils.file_validator import FileValidator

router = APIRouter()

# Mapping from classifier doc type to standard requirement doc type
DOC_TYPE_MAPPING = {
    "Service Book": "Service Book",
    "APAR": "APAR (last 3 years)",
    "Departmental Exam Result": "Departmental Exam Result",
    "Medical Certificate": "Medical Certificate",
    "Charge Sheet": "Charge Sheet",
    "Penalty Order": "Penalty Order",
    "Promotion Order": "Promotion Order",
    "Transfer Order": "Transfer Order",
    "Retirement Record": "Retirement Record",
    "Leave Record": "Leave Application",
}

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    case_id: Optional[UUID] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Validate File Size
    # We read content first to calculate size
    content = await file.read()
    file_size = len(content)
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB."
        )
    
    # Reset read cursor of the file
    await file.seek(0)
    
    # 2. Validate File Type / Extension
    ext = os.path.splitext(file.filename)[1].lower()
    allowed_exts = [".pdf", ".jpg", ".jpeg", ".png"]
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed types: {', '.join(allowed_exts)}"
        )
    
    # 3. Save File to Uploads Directory
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    orig_name_clean = "".join([c if c.isalnum() or c in ".-_" else "_" for c in file.filename])
    stored_filename = f"{uuid.uuid4()}_{orig_name_clean}"
    storage_path = os.path.join(settings.UPLOAD_DIR, stored_filename)
    
    try:
        with open(storage_path, "wb") as buffer:
            buffer.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

    # Validate Magic Signature and Size Verification Checks
    validator = FileValidator()
    valid, err_msg = validator.validate(storage_path, file_size)
    if not valid:
        # Secure cleanup: remove file from disk
        if os.path.exists(storage_path):
            try:
                os.remove(storage_path)
            except Exception:
                pass
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err_msg
        )

    # 4. OCR text extraction
    ocr_engine = OCREngine()
    ocr_result = ocr_engine.process(storage_path)
    
    # 5. Classify Document Type
    classifier = DocumentClassifier()
    classification = classifier.classify(ocr_result.text)
    classified_type = classification.document_type
    
    # Normalize the doc type
    normalized_type = DOC_TYPE_MAPPING.get(classified_type, classified_type)
    
    # 6. Extract Facts (e.g. Service Book Extractor)
    extracted_facts = {}
    if classified_type == "Service Book":
        extractor = ServiceBookExtractor()
        extracted_facts = extractor.extract(ocr_result.text)
    
    # 7. Persist Document in DB
    db_doc = Document(
        user_id=current_user.id,
        case_id=case_id,
        original_filename=file.filename,
        stored_filename=stored_filename,
        storage_path=storage_path,
        document_type=normalized_type,
        classification_confidence=classification.confidence,
        ocr_quality_score=ocr_result.quality_score,
        is_readable=ocr_result.is_readable,
        is_verified=ocr_result.is_readable and classification.confidence > 0.50,
        rejection_reason=ocr_result.rejection_reason,
        extracted_facts=extracted_facts,
        raw_text=ocr_result.text,
        file_size_bytes=file_size,
        mime_type=file.content_type,
        processed_at=datetime.utcnow()
    )
    db.add(db_doc)
    await db.commit()
    await db.refresh(db_doc)
    
    # 8. If case_id is supplied, update Case state
    if case_id:
        case_stmt = select(Case).where(Case.id == case_id)
        case_result = await db.execute(case_stmt)
        case_obj = case_result.scalars().first()
        if case_obj:
            # Add to submitted documents list if not already present
            submitted = list(case_obj.submitted_documents or [])
            if normalized_type not in submitted:
                submitted.append(normalized_type)
                case_obj.submitted_documents = submitted
            
            # Merge facts
            facts = dict(case_obj.extracted_facts or {})
            facts.update(extracted_facts)
            case_obj.extracted_facts = facts
            
            # Recalculate missing documents
            demand_engine = DocumentDemandEngine()
            demand_res = demand_engine.check(
                domain=case_obj.domain,
                submitted_doc_types=submitted,
                employee_facts=facts
            )
            case_obj.missing_documents = demand_res.missing
            
            # If documents are missing, status can be 'blocked', otherwise if it was blocked it goes back to 'open'
            if not demand_res.all_present:
                case_obj.status = "blocked"
            elif case_obj.status == "blocked":
                case_obj.status = "open"
                
            db.add(case_obj)
            await db.commit()
            
    return db_doc

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(Document).where(Document.id == document_id)
    result = await db.execute(stmt)
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    # Check authorization (only owner or admin can access)
    if doc.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden"
        )
    return doc

@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(document_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(Document).where(Document.id == document_id)
    result = await db.execute(stmt)
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    if doc.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden"
        )
        
    # Delete physical file
    if os.path.exists(doc.storage_path):
        try:
            os.remove(doc.storage_path)
        except Exception as e:
            # Log error but proceed with database deletion
            pass
            
    # Remove from Case submitted list if attached to a case
    if doc.case_id:
        case_stmt = select(Case).where(Case.id == doc.case_id)
        case_res = await db.execute(case_stmt)
        case_obj = case_res.scalars().first()
        if case_obj:
            submitted = list(case_obj.submitted_documents or [])
            if doc.document_type in submitted:
                submitted.remove(doc.document_type)
                case_obj.submitted_documents = submitted
                # Re-evaluate missing
                demand_engine = DocumentDemandEngine()
                demand_res = demand_engine.check(
                    domain=case_obj.domain,
                    submitted_doc_types=submitted,
                    employee_facts=case_obj.extracted_facts
                )
                case_obj.missing_documents = demand_res.missing
                if not demand_res.all_present:
                    case_obj.status = "blocked"
                db.add(case_obj)

    await db.execute(delete(Document).where(Document.id == document_id))
    await db.commit()
    return {"detail": "Document deleted successfully"}
