from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
from sqlalchemy import select, func
from pathlib import Path
import logging
import asyncio
import os

from app.api import auth, documents, cases, chat, eligibility, rules, reports, admin
from app.config import settings

logger = logging.getLogger(__name__)

RULES_MD_PATH = Path(__file__).parent / "knowledge" / "rules.md"


async def _bootstrap_rules():
    """
    Run on every startup:
    1. If the rules table is empty  → ingest + embed.
    2. If rules exist but some have no embedding → embed only.
    3. If everything is already present → skip (fast path).
    """
    from app.database.connection import AsyncSessionLocal
    from app.models.rule import Rule
    from app.core.rule_extractor import RuleExtractor
    from app.core.rag_pipeline import RAGPipeline

    async with AsyncSessionLocal() as db:
        # Count total rules and rules with embeddings
        total_res   = await db.execute(select(func.count()).select_from(Rule))
        total       = total_res.scalar_one()

        embedded_res = await db.execute(
            select(func.count()).select_from(Rule).where(Rule.embedding.isnot(None))
        )
        embedded = embedded_res.scalar_one()

        if total == 0:
            # ── Full bootstrap: ingest then embed ──────────────────────────
            if not RULES_MD_PATH.exists():
                logger.warning(
                    f"[startup] rules.md not found at {RULES_MD_PATH}. "
                    "Skipping auto-ingest. Place rules.md in backend/app/knowledge/ "
                    "and restart the server."
                )
                return

            logger.info("[startup] Rules table is empty — ingesting rules.md ...")
            extractor = RuleExtractor()
            extracted = extractor.extract_rules(str(RULES_MD_PATH))

            for rule_data in extracted:
                from app.models.rule import Rule as RuleModel
                rule = RuleModel(
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

            await db.commit()
            logger.info(f"[startup] Ingested {len(extracted)} rules. Now generating embeddings ...")

            rag = RAGPipeline()
            count = await rag.embed_all_rules(db)
            logger.info(f"[startup] Embedded {count} rules. Bootstrap complete ✓")

        elif embedded < total:
            # ── Partial: rules exist but some lack embeddings ──────────────
            logger.info(
                f"[startup] {embedded}/{total} rules have embeddings. "
                "Generating missing embeddings ..."
            )
            rag = RAGPipeline()
            count = await rag.embed_all_rules(db)
            logger.info(f"[startup] Embedded {count} rules ✓")

        else:
            # ── All good: nothing to do ────────────────────────────────────
            logger.info(
                f"[startup] Rules OK: {total} rules, {embedded} embeddings. "
                "Skipping bootstrap."
            )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: run bootstrap on startup, clean up on shutdown."""
    logger.info("[startup] Railway Admin AI starting up ...")

    # Run rule bootstrap in background so the server starts immediately
    # and is not blocked while embeddings are being generated.
    asyncio.create_task(_bootstrap_rules())

    yield  # Server is now running and handling requests

    logger.info("[shutdown] Railway Admin AI shutting down.")


# ── App factory ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Railway Admin AI",
    version="3.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure upload/report directories exist
os.makedirs("./uploads", exist_ok=True)
os.makedirs("./reports", exist_ok=True)

# Register routers
app.include_router(auth.router,        prefix="/api/auth")
app.include_router(documents.router,   prefix="/api/documents")
app.include_router(cases.router,       prefix="/api/cases")
app.include_router(chat.router,        prefix="/api/chat")
app.include_router(eligibility.router, prefix="/api/eligibility")
app.include_router(rules.router,       prefix="/api/rules")
app.include_router(reports.router,     prefix="/api/reports")
app.include_router(admin.router,       prefix="/api/admin")


@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "3.0"}
