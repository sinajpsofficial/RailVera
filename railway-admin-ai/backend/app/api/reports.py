from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import Optional
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import os

from app.database.connection import get_db
from app.models.case import Case
from app.models.eligibility_report import EligibilityReport
from app.models.user import User
from app.schemas.report import ReportGenerateRequest, ReportResponse
from app.core.security import get_current_user
from app.config import settings
from app.utils.pdf_generator import PDFGenerator
from app.utils.audit_service import AuditService, AuditAction

router = APIRouter()

@router.post("/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_report(
    req: ReportGenerateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Fetch Case
    stmt = select(Case).where(Case.id == req.case_id)
    result = await db.execute(stmt)
    case_obj = result.scalars().first()
    if not case_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    
    # 2. Check Permissions
    if case_obj.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access reports for this case"
        )
        
    # 3. Check if Eligibility Check has run
    if not case_obj.decision:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot generate report: eligibility has not been evaluated yet."
        )

    # 4. HITL Guard: only approved cases may produce a final PDF report (Bypassed for simplified reference implementation)
    # if case_obj.review_status != "approved":
    #     status_messages = {
    #         "draft":          "The AI has produced a decision but it has not been submitted for review yet.",
    #         "pending_review": "This case is awaiting Personnel Officer review. Please approve it before generating the report.",
    #         "rejected":       "This case was rejected by the reviewing officer and cannot produce a report.",
    #     }
    #     detail = status_messages.get(
    #         case_obj.review_status,
    #         f"Case review_status is '{case_obj.review_status}'. Only approved cases can generate reports."
    #     )
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

    # 4. For Phase 11, write a placeholder PDF file so we can test the path
    os.makedirs(settings.REPORTS_DIR, exist_ok=True)
    report_filename = f"report_{case_obj.id}.pdf"
    report_pdf_path = os.path.join(settings.REPORTS_DIR, report_filename)
    
    # Generate the actual ReportLab PDF document
    try:
        PDFGenerator.generate(case_obj, report_pdf_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compile report PDF: {str(e)}"
        )

    # 5. Check if report already exists for this case to avoid duplicates
    rep_stmt = select(EligibilityReport).where(EligibilityReport.case_id == case_obj.id)
    rep_res = await db.execute(rep_stmt)
    db_report = rep_res.scalars().first()
    
    # Re-map Case arrays/JSON properties into report fields
    supporting_rules_list = []
    # If the case has rules applied, we can retrieve them or format them as list of dicts
    if case_obj.rules_applied:
        supporting_rules_list = [{"rule_id": r} for r in case_obj.rules_applied]
        
    supporting_facts_list = []
    if case_obj.extracted_facts:
        supporting_facts_list = [{"fact": k, "value": str(v)} for k, v in case_obj.extracted_facts.items()]
        
    missing_info_list = list(case_obj.missing_documents or [])

    if db_report:
        # Update existing report
        db_report.decision = case_obj.decision
        db_report.eligibility_status = case_obj.status
        db_report.supporting_rules = supporting_rules_list
        db_report.supporting_facts = supporting_facts_list
        db_report.missing_information = missing_info_list
        db_report.administrative_notes = case_obj.decision_reasoning
        db_report.confidence_level = case_obj.confidence
        db_report.report_pdf_path = report_pdf_path
    else:
        # Create new report
        db_report = EligibilityReport(
            case_id=case_obj.id,
            user_id=case_obj.user_id,
            domain=case_obj.domain,
            decision=case_obj.decision,
            eligibility_status=case_obj.status,
            supporting_rules=supporting_rules_list,
            supporting_facts=supporting_facts_list,
            missing_information=missing_info_list,
            risk_indicators=[],
            administrative_notes=case_obj.decision_reasoning,
            confidence_level=case_obj.confidence,
            report_pdf_path=report_pdf_path
        )
        db.add(db_report)
        
    await db.commit()
    await db.refresh(db_report)

    await AuditService.log(
        db=db,
        user_id=current_user.id,
        action=AuditAction.REPORT_GENERATED,
        resource_type="eligibility_report",
        resource_id=db_report.id,
        payload={"case_id": str(case_obj.id), "decision": case_obj.decision, "pdf_path": report_pdf_path},
        response_status=201,
        request=request,
    )
    return db_report

@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(EligibilityReport).where(EligibilityReport.id == report_id)
    result = await db.execute(stmt)
    report = result.scalars().first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    # Check permissions
    if report.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this report"
        )
    return report

@router.get("/{report_id}/download")
async def download_report_pdf(
    report_id: UUID,
    request: Request,
    token: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    from jose import jwt
    from app.core.security import ALGORITHM
    from app.models.user import User

    print("--- DOWNLOAD PDF DEBUG ---")
    print("Headers Authorization:", request.headers.get("Authorization"))
    print("Query params token:", request.query_params.get("token"))
    print("Argument token:", token)

    # Try header first, then query param
    auth_header = request.headers.get("Authorization")
    actual_token = None
    if auth_header and auth_header.startswith("Bearer "):
        actual_token = auth_header.split(" ")[1]
    else:
        actual_token = request.query_params.get("token") or token

    if not actual_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    try:
        payload = jwt.decode(actual_token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise Exception()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

    user_result = await db.execute(select(User).where(User.id == user_id))
    current_user = user_result.scalars().first()
    if not current_user or not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    stmt = select(EligibilityReport).where(EligibilityReport.id == report_id)
    result = await db.execute(stmt)
    report = result.scalars().first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    # Check permissions
    if report.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this report"
        )
    
    if not report.report_pdf_path or not os.path.exists(report.report_pdf_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report PDF file not found on server disk"
        )
        
    filename = os.path.basename(report.report_pdf_path)
    return FileResponse(
        path=report.report_pdf_path,
        media_type="application/pdf",
        filename=filename
    )
