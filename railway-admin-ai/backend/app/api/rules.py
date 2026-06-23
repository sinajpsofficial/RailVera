"""
rules.py — API endpoints for rule ingestion, search, and retrieval.

POST /api/rules/ingest  — reads rules.md and stores all rules in the DB
GET  /api/rules/        — list all rules (paginated)
GET  /api/rules/{rule_id} — get a single rule by its rule_id string
GET  /api/rules/domain/{domain} — get all rules for a domain
POST /api/rules/search  — keyword search over rule descriptions
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, delete
from typing import List, Optional
from pathlib import Path
import logging

from app.database.connection import get_db
from app.models.rule import Rule
from app.core.rule_extractor import RuleExtractor
from app.core.rag_pipeline import RAGPipeline

logger = logging.getLogger(__name__)
router = APIRouter()

# Shared RAG pipeline instance (lazy loaded)
rag_pipeline = None

def get_rag_pipeline() -> RAGPipeline:
    global rag_pipeline
    if rag_pipeline is None:
        rag_pipeline = RAGPipeline()
    return rag_pipeline


# Path to the knowledge base (rules.md lives here)
RULES_MD_PATH = Path(__file__).parent.parent / "knowledge" / "rules.md"


# ── Helper: rule record to dict ────────────────────────────────────────────────

def rule_to_dict(rule: Rule) -> dict:
    return {
        "rule_id": rule.rule_id,
        "rule_name": rule.rule_name,
        "domain": rule.domain,
        "source": rule.source,
        "chapter": rule.chapter,
        "section": rule.section,
        "description": rule.description,
        "eligibility_conditions": rule.eligibility_conditions,
        "required_documents": rule.required_documents,
        "disqualifying_conditions": rule.disqualifying_conditions,
        "exceptions": rule.exceptions,
        "decision_logic": rule.decision_logic,
        "authority": rule.authority,
        "related_rules": rule.related_rules,
        "created_at": str(rule.created_at) if rule.created_at else None,
    }


# ── Ingest rules.md ────────────────────────────────────────────────────────────

@router.post("/ingest")
async def ingest_rules(db: AsyncSession = Depends(get_db)):
    """
    Parse rules.md and store all extracted rules in the database.
    Clears all existing rules first, then performs a fresh ingestion.
    """
    if not RULES_MD_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail=f"rules.md not found at {RULES_MD_PATH}. "
                   "Please ensure it is placed in backend/app/knowledge/rules.md"
        )

    logger.info("Clearing existing rules from database for fresh ingestion")
    await db.execute(delete(Rule))
    await db.commit()

    logger.info(f"Starting rule ingestion from {RULES_MD_PATH}")
    extractor = RuleExtractor()
    extracted = extractor.extract_rules(str(RULES_MD_PATH))

    inserted = 0
    skipped = 0

    for rule_data in extracted:
        rule = Rule(
            rule_id=rule_data["rule_id"],
            rule_name=rule_data["rule_name"],
            domain=rule_data["domain"],
            source=rule_data.get("source", "rules.md"),
            chapter=rule_data.get("chapter"),
            section=rule_data.get("section"),
            description=rule_data["description"],
            eligibility_conditions=rule_data.get("eligibility_conditions", []),
            required_documents=rule_data.get("required_documents", []),
            disqualifying_conditions=rule_data.get("disqualifying_conditions", []),
            exceptions=rule_data.get("exceptions", []),
            decision_logic=rule_data.get("decision_logic", ""),
            authority=rule_data.get("authority"),
            related_rules=rule_data.get("related_rules", []),
            raw_text=rule_data["raw_text"],
        )
        db.add(rule)
        inserted += 1

    await db.commit()

    logger.info(f"Ingestion complete: {inserted} inserted, {skipped} skipped")
    return {
        "status": "success",
        "rules_extracted": len(extracted),
        "rules_inserted": inserted,
        "rules_skipped_duplicates": skipped,
        "source": str(RULES_MD_PATH),
    }


# ── List all rules ─────────────────────────────────────────────────────────────

@router.get("/")
async def list_rules(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Return a paginated list of all ingested rules."""
    result = await db.execute(
        select(Rule).order_by(Rule.domain, Rule.rule_id).offset(skip).limit(limit)
    )
    rules = result.scalars().all()

    total_result = await db.execute(select(func.count()).select_from(Rule))
    total = total_result.scalar_one()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "rules": [rule_to_dict(r) for r in rules],
    }


# ── Get single rule by rule_id ─────────────────────────────────────────────────

@router.get("/{rule_id}")
async def get_rule(rule_id: str, db: AsyncSession = Depends(get_db)):
    """Fetch a single rule by its string rule_id (e.g., PROM_001)."""
    result = await db.execute(select(Rule).where(Rule.rule_id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule '{rule_id}' not found.")
    return rule_to_dict(rule)


# ── Get rules by domain ────────────────────────────────────────────────────────

@router.get("/domain/{domain}")
async def get_rules_by_domain(
    domain: str,
    db: AsyncSession = Depends(get_db),
):
    """Return all rules for a specific domain (e.g., Promotion, Leave)."""
    result = await db.execute(
        select(Rule).where(Rule.domain == domain).order_by(Rule.rule_id)
    )
    rules = result.scalars().all()
    return {"domain": domain, "count": len(rules), "rules": [rule_to_dict(r) for r in rules]}


# ── Semantic search ────────────────────────────────────────────────────────────

@router.post("/search")
async def search_rules(
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """
    Semantic search over rules using vector embeddings and re-ranking.
    Body: { "query": "promotion eligibility" }
    """
    query_text: Optional[str] = body.get("query", "").strip()
    if not query_text:
        raise HTTPException(status_code=400, detail="Query text is required.")

    logger.info(f"Performing semantic search for query: {query_text}")
    try:
        pipeline = get_rag_pipeline()
        results = await pipeline.retrieve(query_text, db)
        return {
            "query": query_text,
            "count": len(results),
            "rules": results,
        }
    except Exception as e:
        logger.exception("Semantic search failed")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


# ── Embed all rules ────────────────────────────────────────────────────────────

@router.post("/embed")
async def embed_rules(db: AsyncSession = Depends(get_db)):
    """
    Generate vector embeddings for all ingested rules.
    """
    logger.info("Starting rule embedding generation...")
    try:
        pipeline = get_rag_pipeline()
        count = await pipeline.embed_all_rules(db)
        return {
            "status": "success",
            "message": f"Embedded {count} rules successfully.",
        }
    except Exception as e:
        logger.exception("Embedding generation failed")
        raise HTTPException(status_code=500, detail=f"Embedding failed: {str(e)}")

