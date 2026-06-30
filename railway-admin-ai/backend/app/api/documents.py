import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.database.connection import get_db, AsyncSessionLocal
from app.models.document import Document
from app.models.case import Case
from app.schemas.document import DocumentResponse, DocumentStatusResponse
from app.core.security import get_current_user
from app.models.user import User
from app.config import settings

from app.document_intelligence.ocr_engine import OCREngine
from app.document_intelligence.document_classifier import DocumentClassifier
from app.document_intelligence.llm_extractor import LLMExtractor
from app.core.document_demand_engine import DocumentDemandEngine
from app.utils.file_validator import FileValidator
from app.utils.audit_service import AuditService, AuditAction

logger = logging.getLogger(__name__)

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


# ── Background processing task ────────────────────────────────────────────────

async def _process_document_background(document_id: UUID, storage_path: str, case_id: Optional[UUID]):
    """
    All heavy work (OCR, classification, LLM extraction) runs here AFTER
    the upload endpoint has already returned 201 to the client.

    State machine:
      pending → processing → done
                           → failed (on error, with error message saved)
    """
    async with AsyncSessionLocal() as db:
        try:
            # ── Mark as processing ──────────────────────────────────────────
            result = await db.execute(select(Document).where(Document.id == document_id))
            doc = result.scalars().first()
            if not doc:
                logger.error(f"[BgTask] Document {document_id} not found in DB.")
                return

            doc.processing_status = "processing"
            await db.commit()
            logger.info(f"[BgTask] Processing started for document {document_id} ({doc.original_filename})")

            # ── Step 1: OCR ─────────────────────────────────────────────────
            ocr_engine = OCREngine()
            ocr_result = ocr_engine.process(storage_path)

            # ── Step 2: Classify ────────────────────────────────────────────
            classifier = DocumentClassifier()
            classification = classifier.classify(ocr_result.text)
            classified_type = classification.document_type
            normalized_type = DOC_TYPE_MAPPING.get(classified_type, classified_type)

            # ── Step 3: LLM Fact Extraction ─────────────────────────────────
            extracted_facts = {}
            if classified_type != "Unknown":
                extractor = LLMExtractor()
                extracted_facts = extractor.extract(ocr_result.text, classified_type)
                logger.info(
                    f"[BgTask] Extracted {len(extracted_facts)} facts from "
                    f"'{classified_type}' (doc: {document_id})"
                )

            # ── Step 4: Update Document record ──────────────────────────────
            doc.document_type = normalized_type
            doc.classification_confidence = classification.confidence
            doc.ocr_quality_score = ocr_result.quality_score
            doc.is_readable = ocr_result.is_readable
            doc.is_verified = ocr_result.is_readable and classification.confidence > 0.30
            doc.rejection_reason = ocr_result.rejection_reason or None
            doc.extracted_facts = extracted_facts
            doc.raw_text = ocr_result.text
            doc.processed_at = datetime.now(timezone.utc)
            doc.processing_status = "done"
            await db.commit()
            logger.info(f"[BgTask] Document {document_id} processing complete. Status: done.")

            # Audit: document fully processed
            await AuditService.log(
                db=db,
                user_id=doc.user_id,
                action=AuditAction.DOCUMENT_PROCESSED,
                resource_type="document",
                resource_id=document_id,
                payload={
                    "document_type": normalized_type,
                    "classification_confidence": classification.confidence,
                    "ocr_quality_score": ocr_result.quality_score,
                    "facts_extracted": len(extracted_facts),
                },
                response_status=200,
            )

            # ── Step 5: Update linked Case if present ───────────────────────
            if case_id:
                case_result = await db.execute(select(Case).where(Case.id == case_id))
                case_obj = case_result.scalars().first()
                if case_obj:
                    submitted = list(case_obj.submitted_documents or [])
                    # Only append to submitted list if it is a valid classified type and verified
                    if normalized_type != "Unknown" and doc.is_verified:
                        if normalized_type not in submitted:
                            submitted.append(normalized_type)
                            case_obj.submitted_documents = submitted

                    facts = dict(case_obj.extracted_facts or {})
                    facts.update(extracted_facts)
                    case_obj.extracted_facts = facts

                    demand_engine = DocumentDemandEngine()
                    demand_res = demand_engine.check(
                        domain=case_obj.domain,
                        submitted_doc_types=submitted,
                        employee_facts=facts
                    )
                    case_obj.missing_documents = demand_res.missing

                    if not demand_res.all_present:
                        case_obj.status = "blocked"
                    elif case_obj.status == "blocked":
                        case_obj.status = "open"

                    db.add(case_obj)
                    await db.commit()
                    logger.info(f"[BgTask] Case {case_id} updated after document processing.")

        except Exception as e:
            logger.exception(f"[BgTask] Processing failed for document {document_id}: {e}")
            # ── Mark as failed — save error message ──────────────────────
            try:
                async with AsyncSessionLocal() as err_db:
                    err_result = await err_db.execute(select(Document).where(Document.id == document_id))
                    err_doc = err_result.scalars().first()
                    if err_doc:
                        err_doc.processing_status = "failed"
                        err_doc.processing_error = str(e)[:1000]
                        err_doc.processed_at = datetime.now(timezone.utc)
                        await err_db.commit()
            except Exception as inner_e:
                logger.error(f"[BgTask] Failed to mark document as failed: {inner_e}")


# ── Upload endpoint ───────────────────────────────────────────────────────────

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    case_id: Optional[UUID] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a document and immediately return 201.
    OCR, classification, and extraction run in the background.
    Poll GET /{document_id}/status to check when processing is complete.
    """
    # 1. Read content & validate size
    content = await file.read()
    file_size = len(content)
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB."
        )

    await file.seek(0)

    # 2. Validate extension
    ext = os.path.splitext(file.filename)[1].lower()
    allowed_exts = [".pdf", ".jpg", ".jpeg", ".png"]
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed types: {', '.join(allowed_exts)}"
        )

    # 3. Save file to disk
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

    # 4. Magic-byte file validation (sync — fast)
    validator = FileValidator()
    valid, err_msg = validator.validate(storage_path, file_size)
    if not valid:
        if os.path.exists(storage_path):
            try:
                os.remove(storage_path)
            except Exception:
                pass
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

    # 5. Create Document record immediately with processing_status='pending'
    db_doc = Document(
        user_id=current_user.id,
        case_id=case_id,
        original_filename=file.filename,
        stored_filename=stored_filename,
        storage_path=storage_path,
        file_size_bytes=file_size,
        mime_type=file.content_type,
        # These will be filled in by the background task
        document_type=None,
        is_readable=True,
        is_verified=False,
        extracted_facts={},
        processing_status="pending",
    )
    db.add(db_doc)
    await db.commit()
    await db.refresh(db_doc)

    # 6. Kick off heavy processing in the background
    background_tasks.add_task(
        _process_document_background,
        document_id=db_doc.id,
        storage_path=storage_path,
        case_id=case_id,
    )

    logger.info(
        f"[Upload] Document {db_doc.id} saved. Background processing enqueued. "
        f"(user={current_user.id}, file={file.filename})"
    )

    return db_doc


# ── Status polling endpoint ───────────────────────────────────────────────────

@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Poll this endpoint to check whether background OCR/extraction has completed.

    Response processing_status values:
      - pending    : queued, not started yet
      - processing : OCR/extraction actively running
      - done       : all facts extracted, document ready
      - failed     : an error occurred (see processing_error for details)
    """
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if doc.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden")
    return doc


# ── Existing endpoints ────────────────────────────────────────────────────────

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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
        except Exception:
            pass

    # Remove from Case submitted list if attached
    if doc.case_id:
        case_stmt = select(Case).where(Case.id == doc.case_id)
        case_res = await db.execute(case_stmt)
        case_obj = case_res.scalars().first()
        if case_obj:
            submitted = list(case_obj.submitted_documents or [])
            if doc.document_type in submitted:
                submitted.remove(doc.document_type)
                case_obj.submitted_documents = submitted
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
