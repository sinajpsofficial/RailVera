"""
audit_service.py — Centralised audit logging service.

Writes immutable entries to the audit_logs table for every significant
system action. Required for legal compliance in government HR systems.

Usage:
    await AuditService.log(
        db=db,
        user_id=current_user.id,
        action="CASE_EVALUATED",
        resource_type="case",
        resource_id=case_obj.id,
        payload={"decision": "Eligible", "domain": "Promotion"},
        response_status=200,
        request=request,   # optional FastAPI Request for IP capture
    )
"""

import logging
from typing import Optional, Any, Dict
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)

# ── Action constants (prevents typos across the codebase) ─────────────────────
class AuditAction:
    # Authentication
    USER_LOGIN            = "USER_LOGIN"
    USER_LOGOUT           = "USER_LOGOUT"
    USER_REGISTERED       = "USER_REGISTERED"

    # Cases
    CASE_CREATED          = "CASE_CREATED"
    CASE_EVALUATED        = "CASE_EVALUATED"
    CASE_STATUS_CHANGED   = "CASE_STATUS_CHANGED"

    # HITL Review
    CASE_REVIEW_APPROVED  = "CASE_REVIEW_APPROVED"
    CASE_REVIEW_REJECTED  = "CASE_REVIEW_REJECTED"
    CASE_REVIEW_REQUESTED = "CASE_REVIEW_REQUESTED"

    # Documents
    DOCUMENT_UPLOADED     = "DOCUMENT_UPLOADED"
    DOCUMENT_DELETED      = "DOCUMENT_DELETED"
    DOCUMENT_PROCESSED    = "DOCUMENT_PROCESSED"

    # Reports
    REPORT_GENERATED      = "REPORT_GENERATED"
    REPORT_DOWNLOADED     = "REPORT_DOWNLOADED"

    # Rules
    RULES_INGESTED        = "RULES_INGESTED"
    RULES_EMBEDDED        = "RULES_EMBEDDED"


class AuditService:
    """
    Provides a single `log()` class method for writing audit entries.
    All writes are fire-and-forget — failures are logged but never raise,
    so that an audit failure never disrupts the main request flow.
    """

    @classmethod
    async def log(
        cls,
        db: AsyncSession,
        action: str,
        user_id: Optional[UUID] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[UUID] = None,
        payload: Optional[Dict[str, Any]] = None,
        response_status: Optional[int] = None,
        ip_address: Optional[str] = None,
        request=None,   # FastAPI Request — used to auto-extract IP if provided
    ) -> None:
        """
        Write a single audit log entry. Safe to call from any async context.
        Never raises — failures are swallowed with a warning log.
        """
        try:
            # Auto-extract IP from the FastAPI request object if provided
            if request is not None and ip_address is None:
                ip_address = cls._extract_ip(request)

            entry = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                request_payload=cls._sanitise_payload(payload),
                response_status=response_status,
            )
            db.add(entry)
            await db.commit()
            logger.debug(f"[Audit] {action} | user={user_id} | {resource_type}={resource_id}")
        except Exception as e:
            # Audit failure must NEVER crash the main request
            logger.error(f"[Audit] Failed to write audit log for action '{action}': {e}")

    @staticmethod
    def _extract_ip(request) -> Optional[str]:
        """Extract real client IP, honouring X-Forwarded-For proxy headers."""
        try:
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                return forwarded_for.split(",")[0].strip()
            return str(request.client.host) if request.client else None
        except Exception:
            return None

    @staticmethod
    def _sanitise_payload(payload: Optional[Dict]) -> Optional[Dict]:
        """
        Remove sensitive fields before storing in audit_logs.
        Truncates large text fields to avoid bloating the audit table.
        """
        if not payload:
            return payload
        SENSITIVE_KEYS = {"password", "password_hash", "token", "secret_key", "authorization"}
        MAX_STR_LEN = 2000
        cleaned = {}
        for k, v in payload.items():
            if k.lower() in SENSITIVE_KEYS:
                continue
            if isinstance(v, str) and len(v) > MAX_STR_LEN:
                v = v[:MAX_STR_LEN] + "... [truncated]"
            cleaned[k] = v
        return cleaned
