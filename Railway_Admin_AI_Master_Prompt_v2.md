# MASTER SYSTEM DESIGN PROMPT — VERSION 3.0
## Railway Employee Administrative Decision Support AI
### Rules.md Authority Edition · Document-Demand Enhanced · Native Installation (No Docker)

---

> **VERSION:** 3.0 — Beginner-Friendly, Native Setup  
> **CLASSIFICATION:** Principal Architecture Specification  
> **AUTHORITY SOURCE:** rules.md (sole and exclusive)  
> **DOCUMENT DEMAND:** Active — system proactively identifies and requests missing documents  
> **DEPLOYMENT:** Native installation first · Docker optional at the end  

---

## ROLE DEFINITION

You are simultaneously acting as:

- **Principal Software Architect** — system design and component integration
- **Senior AI/LLM Engineer** — RAG pipeline, prompt engineering, hallucination control
- **Knowledge Engineer** — rule extraction, normalization, dependency mapping
- **Legal Knowledge Systems Specialist** — administrative rule formalization
- **Enterprise Product Architect** — scalability, maintainability, deployment
- **Railway Personnel Administration Expert** — domain semantics and case logic
- **Decision Systems Engineer** — deterministic eligibility evaluation
- **Full-Stack Software Architect** — end-to-end implementation

Your task is to design a **complete, production-quality, beginner-developer-feasible** AI-powered Railway Employee Administrative Decision Support System that behaves like an experienced, rules-bound Railway Personnel Officer.

The system is built **natively on the developer's local machine first** — no Docker, no containers, no virtual machines. Everything runs directly. Docker is an optional step added only at the very end if deployment to a server is needed.

---

## PRIMARY CONSTRAINT — INVIOLABLE

### The One True Source: `rules.md`

**ALL** rules, eligibility conditions, exceptions, restrictions, penalties, administrative outcomes, and decision logic must originate **exclusively** from `rules.md`.

**FORBIDDEN sources:**
- Railway websites or circulars
- Government portals
- Legal databases
- External APIs
- Internet knowledge
- LLM training knowledge / parametric memory

**When rules are absent:**
> *"The rule repository does not contain sufficient information to determine this. Please consult the competent authority."*

**When facts are absent:**
> *"The following documents are required to proceed with this determination: [LIST]. Please upload them to continue."*

**The engine must NEVER guess. It must NEVER infer. It must ALWAYS cite.**

---

## SYSTEM OBJECTIVE

Build an AI assistant that:

1. Reads and internalizes all rules from `rules.md`
2. Accepts uploaded employee documents as **evidence** (not rule sources)
3. Extracts structured facts from those documents
4. **Proactively identifies missing required documents** for each case type
5. **Demands submission of missing documents** before proceeding
6. Evaluates eligibility using rules + verified facts
7. Explains its reasoning with full source citations
8. Generates formal administrative decision reports

The assistant functions as a unified:
- **Rule Repository** — normalized, searchable, versioned
- **Eligibility Engine** — deterministic, auditable
- **Document Demand Engine** — proactively manages required evidence
- **Administrative Advisor** — personalized, case-specific
- **Decision Support System** — transparent, rule-backed
- **Explainable AI System** — every output traces to a rule or a fact

---

## TECHNOLOGY STACK — NATIVE INSTALLATION

Everything runs directly on the developer's machine. No Docker required to build and use the system.

| Layer | Technology | How to Install |
|---|---|---|
| Frontend | Next.js 14 (App Router) | `npm create next-app` |
| Backend | FastAPI (Python 3.11) | `pip install fastapi uvicorn` |
| Database | PostgreSQL 15 + pgvector | Installer from postgresql.org |
| Embeddings | BAAI/bge-small-en-v1.5 | `pip install sentence-transformers` |
| Reranker | bge-reranker-base | `pip install FlagEmbedding` |
| Local LLM | Qwen3 via Ollama | Installer from ollama.com |
| OCR | Tesseract + pdf2image | OS package manager |
| File Storage | Local `uploads/` folder | Created by the app automatically |
| Environment vars | python-dotenv | `pip install python-dotenv` |

### How to run the system (native)

```
Terminal 1:  PostgreSQL runs as a background service (auto-starts after install)
Terminal 2:  ollama serve          (keeps Qwen3 running)
Terminal 3:  uvicorn app.main:app  (FastAPI backend)
Terminal 4:  npm run dev           (Next.js frontend)
```

### Environment variables — use these instead of hardcoding

Create a `.env` file in the backend folder:

```
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/railway_ai
OLLAMA_URL=http://localhost:11434
UPLOAD_DIR=./uploads
SECRET_KEY=your-secret-key-here
```

**Why this matters:** If you ever want to move to Docker later, you only change these `.env` values. Your actual Python code stays exactly the same.

---

## CRITICAL ADDITION: DOCUMENT DEMAND SYSTEM

### Core Principle
Before evaluating any case, the system must determine the **complete set of documents required** for that case type (as defined in `rules.md`) and compare it against what has been uploaded.

**If any required document is missing:**
- The system MUST NOT proceed with eligibility determination
- The system MUST generate a **Document Demand Notice**
- The notice must name each missing document specifically
- The notice must explain WHY each document is needed (which rule requires it)
- The notice must provide the format/specification for acceptable submission where available in rules.md
- The system MUST wait for document upload before continuing

**If a document is uploaded but unreadable:**
- Flag it as "unreadable/incomplete"
- Request re-upload
- Do not proceed on the basis of an illegible document

**If a document is uploaded but does not match the required type:**
- Flag the mismatch
- Specify what was received vs. what was required
- Request the correct document

### Document Demand Notice Format

```
╔══════════════════════════════════════════════════════╗
║         DOCUMENT REQUIREMENT NOTICE                  ║
║         Case: [CASE TYPE] | Employee: [ID/NAME]      ║
╚══════════════════════════════════════════════════════╝

To process your request for [CASE TYPE], the following
documents are required under [RULE REFERENCE]:

SUBMITTED ✓                   MISSING ✗
──────────────────────────    ──────────────────────────
[doc name] (verified)         [doc name] — REQUIRED
                              [doc name] — REQUIRED
                              [doc name] — REQUIRED

REASON DOCUMENTS ARE REQUIRED:
• [doc name]: Required under Rule [X] to verify [fact Y]
• [doc name]: Required under Rule [X] to confirm [fact Z]

⚠ This case cannot be evaluated until all required
  documents are submitted. Please upload the missing
  documents to continue.
```

---

## CORE DECISION LOGIC

```
Rules (rules.md)
    +
Facts (verified from documents + user inputs)
    +
Document Completeness Check (all required docs present)
    =
Decision (eligible / not eligible / cannot determine)
```

**The AI must:**
- Derive rules ONLY from `rules.md`
- Derive facts ONLY from uploaded documents or explicit user answers
- Verify document completeness BEFORE evaluating eligibility
- Demand missing documents BEFORE generating any decision
- Cite every rule and fact used

---

## EXAMPLE USER QUESTIONS AND EXPECTED SYSTEM BEHAVIOR

### Promotion
- "Am I eligible for promotion?"
- "Can I appear for the selection process?"
- "What documents are required for promotion?"

**System behavior:** Identify all promotion-related required documents from rules.md → Check which are uploaded → Demand missing ones → Extract facts from submitted documents → Ask targeted follow-up questions for missing facts → Evaluate → Report.

### Increment
- "Am I eligible for annual increment?"
- "Can my increment be withheld?"

### Leave
- "Can I avail Earned Leave?"
- "Am I eligible for Medical Leave?"
- "Can I encash my leave balance?"

### Transfer
- "Am I eligible for transfer?"
- "What approvals are required?"

### Discipline
- "What action can be taken for unauthorized absence?"
- "What penalties are applicable in my case?"

### Departmental Examination
- "Can I appear for the examination?"
- "What are the eligibility conditions?"

### Benefits and Retirement
- "What benefits am I entitled to?"
- "What retirement benefits are available to me?"

---

## PHASE 1 — ENVIRONMENT SETUP (NATIVE)

### What to install on Windows

```
Step 1: Python 3.11
  Download from: https://www.python.org/downloads/
  During install: CHECK "Add Python to PATH"
  Verify: open Command Prompt, type: python --version

Step 2: Node.js 20
  Download from: https://nodejs.org/
  Choose the LTS version
  Verify: npm --version

Step 3: PostgreSQL 15
  Download from: https://www.postgresql.org/downloads/
  During install: remember the password you set for user "postgres"
  Default port: 5432 (keep it)
  Also install pgAdmin (comes bundled) for visual database management

Step 4: pgvector extension
  After PostgreSQL is installed, open pgAdmin
  Connect to your database
  Run this SQL: CREATE EXTENSION IF NOT EXISTS vector;

Step 5: Ollama (runs Qwen3 locally)
  Download from: https://ollama.com/download
  After install, open Command Prompt and run:
  ollama pull qwen3
  This downloads the Qwen3 model (may take 10-20 minutes)

Step 6: Tesseract OCR
  Download installer from:
  https://github.com/UB-Mannheim/tesseract/wiki
  During install: add to PATH
  Verify: tesseract --version

Step 7: Git
  Download from: https://git-scm.com/
```

### What to install on Ubuntu/Linux

```bash
# Python 3.11
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip -y

# Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs -y

# PostgreSQL 15 + pgvector
sudo apt install postgresql-15 postgresql-contrib -y
sudo apt install postgresql-15-pgvector -y
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database
sudo -u postgres psql -c "CREATE DATABASE railway_ai;"
sudo -u postgres psql -d railway_ai -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3

# Tesseract OCR
sudo apt install tesseract-ocr poppler-utils -y

# pdf2image dependency
sudo apt install python3-dev libpoppler-cpp-dev pkg-config -y
```

### Project folder structure

```
railway-admin-ai/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database/
│   │   │   └── connection.py
│   │   ├── api/
│   │   │   ├── auth.py
│   │   │   ├── documents.py
│   │   │   ├── cases.py
│   │   │   ├── chat.py
│   │   │   ├── eligibility.py
│   │   │   ├── rules.py
│   │   │   ├── reports.py
│   │   │   └── admin.py
│   │   ├── core/
│   │   │   ├── rule_extractor.py
│   │   │   ├── knowledge_normalizer.py
│   │   │   ├── eligibility_engine.py
│   │   │   ├── document_demand_engine.py
│   │   │   ├── fact_extractor.py
│   │   │   ├── fact_validator.py
│   │   │   ├── rag_pipeline.py
│   │   │   ├── llm_client.py
│   │   │   ├── prompt_builder.py
│   │   │   ├── employee_profile_builder.py
│   │   │   └── report_generator.py
│   │   ├── document_intelligence/
│   │   │   ├── ocr_engine.py
│   │   │   ├── document_classifier.py
│   │   │   ├── quality_checker.py
│   │   │   └── extractors/
│   │   │       ├── service_book_extractor.py
│   │   │       ├── apar_extractor.py
│   │   │       ├── leave_extractor.py
│   │   │       ├── discipline_extractor.py
│   │   │       └── promotion_extractor.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── employee.py
│   │   │   ├── document.py
│   │   │   ├── case.py
│   │   │   ├── rule.py
│   │   │   └── conversation.py
│   │   ├── schemas/
│   │   │   └── (Pydantic schemas for all models)
│   │   ├── knowledge/
│   │   │   ├── rules.md               ← THE ONLY SOURCE OF TRUTH
│   │   │   ├── rules.json             ← auto-generated from rules.md
│   │   │   └── document_requirements.json
│   │   └── utils/
│   │       ├── security.py
│   │       ├── file_validator.py
│   │       ├── audit_logger.py
│   │       └── pii_masker.py
│   ├── uploads/                       ← uploaded documents stored here
│   ├── reports/                       ← generated PDF reports stored here
│   ├── tests/
│   │   ├── test_rule_extractor.py
│   │   ├── test_eligibility_engine.py
│   │   ├── test_document_demand.py
│   │   └── test_rag_pipeline.py
│   ├── .env                           ← environment variables (never commit this)
│   ├── .env.example                   ← template to share with others
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx                   ← Home
│   │   ├── chat/page.tsx              ← Main chat interface
│   │   ├── eligibility/page.tsx       ← Guided eligibility checker
│   │   ├── documents/page.tsx         ← Document manager
│   │   ├── rules/page.tsx             ← Rule explorer
│   │   ├── cases/page.tsx             ← Case list
│   │   └── reports/page.tsx           ← Download reports
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatWindow.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   ├── DocumentDemandNotice.tsx
│   │   │   └── CitationBadge.tsx
│   │   ├── documents/
│   │   │   ├── DocumentUploader.tsx
│   │   │   ├── DocumentStatusTracker.tsx
│   │   │   └── DocumentChecklist.tsx
│   │   └── shared/
│   │       ├── Navbar.tsx
│   │       └── Sidebar.tsx
│   ├── lib/
│   │   ├── api.ts
│   │   └── types.ts
│   ├── .env.local                     ← frontend environment variables
│   └── package.json
│
└── docs/
    ├── setup.md
    └── architecture.md
```

---

## PHASE 2 — DATABASE DESIGN

### Python requirements.txt

```
fastapi==0.111.0
uvicorn[standard]==0.30.0
sqlalchemy[asyncio]==2.0.30
asyncpg==0.29.0
pgvector==0.2.5
pydantic==2.7.0
pydantic-settings==2.3.0
python-dotenv==1.0.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
sentence-transformers==2.7.0
FlagEmbedding==1.2.10
pytesseract==0.3.10
pdf2image==1.17.0
Pillow==10.3.0
reportlab==4.2.0
httpx==0.27.0
aiofiles==23.2.1
```

### Database schema (PostgreSQL)

```sql
-- Enable vector extension (run once)
CREATE EXTENSION IF NOT EXISTS vector;

-- Users and authentication
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id VARCHAR(20) UNIQUE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'employee',
    division VARCHAR(100),
    department VARCHAR(100),
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Employee knowledge profiles
CREATE TABLE employee_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    profile_data JSONB NOT NULL DEFAULT '{}',
    completeness_pct NUMERIC(5,2) DEFAULT 0,
    last_document_upload TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Rules repository (populated from rules.md)
CREATE TABLE rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id VARCHAR(50) UNIQUE NOT NULL,
    rule_name VARCHAR(255) NOT NULL,
    domain VARCHAR(100) NOT NULL,
    source VARCHAR(50) DEFAULT 'rules.md',
    chapter VARCHAR(100),
    section VARCHAR(100),
    description TEXT NOT NULL,
    eligibility_conditions JSONB DEFAULT '[]',
    required_documents JSONB DEFAULT '[]',
    disqualifying_conditions JSONB DEFAULT '[]',
    exceptions JSONB DEFAULT '[]',
    decision_logic TEXT,
    authority VARCHAR(255),
    related_rules TEXT[] DEFAULT '{}',
    embedding vector(384),
    raw_text TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_rules_domain ON rules(domain);
CREATE INDEX idx_rules_rule_id ON rules(rule_id);
CREATE INDEX idx_rules_embedding ON rules
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Cases (each eligibility check or question is a case)
CREATE TABLE cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    domain VARCHAR(100) NOT NULL,
    query_text TEXT,
    status VARCHAR(50) DEFAULT 'open',
    required_documents JSONB DEFAULT '[]',
    submitted_documents JSONB DEFAULT '[]',
    missing_documents JSONB DEFAULT '[]',
    extracted_facts JSONB DEFAULT '{}',
    decision VARCHAR(100),
    confidence VARCHAR(50),
    decision_reasoning TEXT,
    rules_applied TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Uploaded documents
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    case_id UUID REFERENCES cases(id) ON DELETE SET NULL,
    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    document_type VARCHAR(100),
    classification_confidence NUMERIC(5,4),
    ocr_quality_score NUMERIC(5,4),
    is_readable BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    rejection_reason TEXT,
    extracted_facts JSONB DEFAULT '{}',
    raw_text TEXT,
    file_size_bytes INTEGER,
    mime_type VARCHAR(100),
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

-- Conversations
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    message_type VARCHAR(50) DEFAULT 'text',
    rules_cited TEXT[] DEFAULT '{}',
    documents_cited UUID[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Document demand tracking
CREATE TABLE document_demands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    demanded_document VARCHAR(255) NOT NULL,
    reason TEXT NOT NULL,
    rule_citations TEXT[] DEFAULT '{}',
    demanded_at TIMESTAMPTZ DEFAULT NOW(),
    fulfilled_at TIMESTAMPTZ,
    fulfilled_by_document_id UUID REFERENCES documents(id),
    status VARCHAR(50) DEFAULT 'pending'
);

-- Eligibility reports
CREATE TABLE eligibility_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    domain VARCHAR(100),
    decision VARCHAR(100),
    eligibility_status VARCHAR(50),
    supporting_rules JSONB DEFAULT '[]',
    supporting_facts JSONB DEFAULT '[]',
    missing_information JSONB DEFAULT '[]',
    risk_indicators JSONB DEFAULT '[]',
    administrative_notes TEXT,
    confidence_level VARCHAR(50),
    report_pdf_path VARCHAR(500),
    generated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit logs
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(255) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    ip_address INET,
    request_payload JSONB,
    response_status INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Rule dependencies
CREATE TABLE rule_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id VARCHAR(50) NOT NULL,
    depends_on_rule_id VARCHAR(50) NOT NULL,
    dependency_type VARCHAR(100)
);
```

### How to run this migration

```python
# backend/app/database/migrations.py
# Run this file ONCE to create all tables

import asyncio
import asyncpg
from dotenv import load_dotenv
import os

load_dotenv()

async def create_tables():
    conn = await asyncpg.connect(os.getenv("DATABASE_URL_SYNC"))
    with open("schema.sql", "r") as f:
        sql = f.read()
    await conn.execute(sql)
    await conn.close()
    print("All tables created successfully.")

asyncio.run(create_tables())
```

---

## PHASE 3 — FASTAPI BACKEND

### config.py

```python
# backend/app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    OLLAMA_URL: str = "http://localhost:11434"
    UPLOAD_DIR: str = "./uploads"
    REPORTS_DIR: str = "./reports"
    MAX_FILE_SIZE_MB: int = 20
    OCR_QUALITY_THRESHOLD: float = 0.70
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    RERANKER_MODEL: str = "BAAI/bge-reranker-base"
    LLM_MODEL: str = "qwen3"

    class Config:
        env_file = ".env"

settings = Settings()
```

### main.py

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, documents, cases, chat, eligibility, rules, reports
import os

app = FastAPI(title="Railway Admin AI", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create upload and report directories if they don't exist
os.makedirs("./uploads", exist_ok=True)
os.makedirs("./reports", exist_ok=True)

app.include_router(auth.router,        prefix="/api/auth")
app.include_router(documents.router,   prefix="/api/documents")
app.include_router(cases.router,       prefix="/api/cases")
app.include_router(chat.router,        prefix="/api/chat")
app.include_router(eligibility.router, prefix="/api/eligibility")
app.include_router(rules.router,       prefix="/api/rules")
app.include_router(reports.router,     prefix="/api/reports")

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "3.0"}
```

### How to start the backend

```bash
# Navigate to backend folder
cd railway-admin-ai/backend

# Create virtual environment (do this once)
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Activate it (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --reload --port 8000

# Test it
# Open browser at: http://localhost:8000/health
# Open API docs at: http://localhost:8000/docs
```

---

## PHASE 4 — RULE EXTRACTION ENGINE

### Rule schema (every rule extracted from rules.md)

```json
{
  "rule_id": "PROM_001",
  "rule_name": "Minimum Service for Promotion",
  "domain": "Promotion",
  "source": "rules.md",
  "chapter": "Chapter 3",
  "section": "Section 3.2",
  "description": "Full description of the rule as written in rules.md",
  "eligibility_conditions": [
    "Minimum 3 years in current grade",
    "No penalty within preceding 2 years"
  ],
  "required_documents": [
    {
      "document_type": "Service Book",
      "purpose": "Verify service period and grade",
      "mandatory": true
    },
    {
      "document_type": "APAR",
      "purpose": "Verify performance rating",
      "mandatory": true
    },
    {
      "document_type": "Departmental Exam Result",
      "purpose": "Confirm examination clearance",
      "mandatory": true
    },
    {
      "document_type": "Penalty Order (if any)",
      "purpose": "Verify clean record",
      "mandatory": "conditional"
    }
  ],
  "disqualifying_conditions": [
    "Pending disciplinary proceedings",
    "Adverse APAR entry not expunged"
  ],
  "exceptions": [],
  "decision_logic": "IF service >= 3 years AND APAR >= Good (last 3 years) AND exam_passed = true AND no_active_penalty = true THEN eligible",
  "authority": "DRM / CPO",
  "related_rules": ["PROM_002", "APAR_001", "DISC_003"]
}
```

### Domains and rule prefixes

| Domain | Prefix |
|---|---|
| Promotion | PROM_ |
| Annual Increment | INCR_ |
| Leave | LEAVE_ |
| Attendance | ATTN_ |
| Transfer | TRNF_ |
| Departmental Examination | EXAM_ |
| Discipline | DISC_ |
| Employee Benefits | BENF_ |
| Retirement | RETR_ |
| Pension | PENS_ |
| Service Conditions | SRVC_ |

### rule_extractor.py

```python
# backend/app/core/rule_extractor.py
import re
import json
from pathlib import Path
from typing import List, Dict

class RuleExtractor:
    """
    Parses rules.md and extracts every rule into a structured dictionary.
    
    Strategy:
    - Detects section headings (##, ###, numbered like "3.2")
    - Identifies rule content by keywords: shall, must, eligible,
      disqualified, prohibited, entitled, required
    - Extracts required documents by keywords: produce, submit,
      attach, furnish, provide
    - Identifies exceptions: provided that, notwithstanding, except
    - Auto-assigns domain based on heading keywords
    """

    DOMAIN_KEYWORDS = {
        "Promotion": ["promotion", "selection", "upgrade", "seniority"],
        "Leave": ["leave", "absence", "vacation", "earned leave", "medical leave"],
        "Increment": ["increment", "pay rise", "annual increment"],
        "Discipline": ["penalty", "punishment", "charge sheet", "suspension"],
        "Transfer": ["transfer", "posting", "deputation"],
        "DeptExam": ["departmental examination", "ldce", "gdce"],
        "Retirement": ["retirement", "superannuation", "voluntary retirement"],
        "Pension": ["pension", "gratuity", "commutation"],
        "Benefits": ["allowance", "entitlement", "benefit", "reimbursement"],
    }

    def extract_rules(self, rules_md_path: str) -> List[Dict]:
        text = Path(rules_md_path).read_text(encoding="utf-8")
        sections = self._split_into_sections(text)
        rules = []
        for idx, section in enumerate(sections):
            rule = self._parse_section(section, idx)
            if rule:
                rules.append(rule)
        return rules

    def _split_into_sections(self, text: str) -> List[str]:
        # Split on markdown headings or numbered sections
        pattern = r"(?=^#{1,4}\s|^\d+\.\d+)"
        return re.split(pattern, text, flags=re.MULTILINE)

    def _parse_section(self, section: str, idx: int) -> Dict | None:
        if len(section.strip()) < 50:
            return None
        lines = section.strip().split("\n")
        heading = lines[0].strip("#").strip()
        body = "\n".join(lines[1:])
        domain = self._detect_domain(section)
        return {
            "rule_id": f"{self._domain_prefix(domain)}_{idx+1:03d}",
            "rule_name": heading[:255],
            "domain": domain,
            "source": "rules.md",
            "description": body.strip(),
            "eligibility_conditions": self._extract_conditions(body),
            "required_documents": self._extract_documents(body),
            "disqualifying_conditions": self._extract_disqualifiers(body),
            "exceptions": self._extract_exceptions(body),
            "decision_logic": self._extract_decision_logic(body),
            "raw_text": section.strip(),
        }

    def _detect_domain(self, text: str) -> str:
        text_lower = text.lower()
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                return domain
        return "General"

    def _domain_prefix(self, domain: str) -> str:
        prefixes = {
            "Promotion": "PROM", "Leave": "LEAVE", "Increment": "INCR",
            "Discipline": "DISC", "Transfer": "TRNF", "DeptExam": "EXAM",
            "Retirement": "RETR", "Pension": "PENS", "Benefits": "BENF",
        }
        return prefixes.get(domain, "GEN")

    def _extract_conditions(self, text: str) -> List[str]:
        conditions = []
        patterns = [r"shall\s+(.+?)[\.\n]", r"must\s+(.+?)[\.\n]",
                    r"eligible\s+(?:if|when|provided)\s+(.+?)[\.\n]"]
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            conditions.extend([m.strip() for m in matches])
        return conditions[:10]

    def _extract_documents(self, text: str) -> List[Dict]:
        docs = []
        patterns = [r"(?:submit|produce|furnish|attach|provide)\s+(.+?)[\.\n]"]
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                docs.append({"document_type": match.strip(), "mandatory": True})
        return docs[:10]

    def _extract_disqualifiers(self, text: str) -> List[str]:
        patterns = [r"(?:disqualified|not eligible|ineligible)\s+(?:if|when|where)\s+(.+?)[\.\n]",
                    r"shall not be eligible\s+(.+?)[\.\n]"]
        disqualifiers = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            disqualifiers.extend([m.strip() for m in matches])
        return disqualifiers[:5]

    def _extract_exceptions(self, text: str) -> List[str]:
        patterns = [r"(?:provided that|notwithstanding|except where)\s+(.+?)[\.\n]"]
        exceptions = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            exceptions.extend([m.strip() for m in matches])
        return exceptions[:5]

    def _extract_decision_logic(self, text: str) -> str:
        if "if" in text.lower() and ("then" in text.lower() or "eligible" in text.lower()):
            match = re.search(r"(if.+?(?:then|eligible).+?)[\.\n]", text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""
```

---

## PHASE 5 — VECTOR SEARCH (RAG PIPELINE)

```python
# backend/app/core/rag_pipeline.py
from sentence_transformers import SentenceTransformer
from FlagEmbedding import FlagReranker
from sqlalchemy.ext.asyncio import AsyncSession
from pgvector.sqlalchemy import Vector
from typing import List, Dict
import numpy as np

class RAGPipeline:
    """
    Retrieves the most relevant rules from the database for any query.
    
    How it works:
    1. Convert the user's question into a 384-number vector (embedding)
    2. Find rules whose embeddings are closest (cosine similarity)
    3. Re-rank the top results for precision
    4. Return top 5 most relevant rules with citations
    """

    def __init__(self):
        # Load locally, no API key needed
        self.embedder = SentenceTransformer("BAAI/bge-small-en-v1.5")
        self.reranker = FlagReranker("BAAI/bge-reranker-base", use_fp16=True)

    def embed_text(self, text: str) -> List[float]:
        return self.embedder.encode(text, normalize_embeddings=True).tolist()

    async def embed_all_rules(self, db: AsyncSession):
        """
        Run this ONCE after ingesting rules.md to create embeddings.
        Stores the embedding vector in the rules.embedding column.
        """
        from app.models.rule import Rule
        from sqlalchemy import select

        result = await db.execute(select(Rule))
        rules = result.scalars().all()

        for rule in rules:
            text = f"{rule.rule_name}. {rule.description}"
            rule.embedding = self.embed_text(text)

        await db.commit()
        print(f"Embedded {len(rules)} rules successfully.")

    async def retrieve(
        self,
        query: str,
        db: AsyncSession,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Find the most relevant rules for a question.
        Returns a list of rules with rule_id, rule_name, description, score.
        """
        query_embedding = self.embed_text(query)

        # Step 1: Vector similarity search (top 20)
        from app.models.rule import Rule
        from sqlalchemy import select, text

        sql = text("""
            SELECT rule_id, rule_name, description, raw_text,
                   1 - (embedding <=> :embedding::vector) AS similarity
            FROM rules
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> :embedding::vector
            LIMIT 20
        """)
        result = await db.execute(sql, {"embedding": str(query_embedding)})
        candidates = result.fetchall()

        if not candidates:
            return []

        # Step 2: Re-rank using bge-reranker
        pairs = [[query, row.raw_text] for row in candidates]
        rerank_scores = self.reranker.compute_score(pairs, normalize=True)

        ranked = sorted(
            zip(candidates, rerank_scores),
            key=lambda x: x[1],
            reverse=True
        )

        # Step 3: Return top_k with metadata
        return [
            {
                "rule_id": row.rule_id,
                "rule_name": row.rule_name,
                "description": row.description,
                "relevance_score": float(score),
            }
            for row, score in ranked[:top_k]
            if float(score) > 0.30  # discard irrelevant results
        ]
```

---

## PHASE 6 — LOCAL LLM (QWEN3 VIA OLLAMA)

```python
# backend/app/core/llm_client.py
import httpx
from app.config import settings

class LLMClient:
    """
    Sends prompts to Qwen3 running locally via Ollama.
    Ollama must be running: open a terminal and run 'ollama serve'
    """

    async def generate(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.OLLAMA_URL}/api/generate",
                json={
                    "model": settings.LLM_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,   # Low = more factual, less creative
                        "top_p": 0.9,
                    }
                }
            )
            data = response.json()
            return data.get("response", "").strip()
```

```python
# backend/app/core/prompt_builder.py
from typing import List, Dict

class PromptBuilder:
    """
    Builds the exact prompt sent to Qwen3.

    The system section strictly forbids the LLM from using its own
    training knowledge — it can ONLY use the retrieved rules and
    the extracted facts provided to it.
    """

    SYSTEM_PROMPT = """You are a Railway Personnel Administration Officer.

STRICT RULES YOU MUST FOLLOW:
1. You answer ONLY using the rules provided in RETRIEVED RULES below.
2. You use ONLY the facts provided in EMPLOYEE FACTS below.
3. Never use your own training knowledge for any administrative rule.
4. If the answer is not in the retrieved rules, respond EXACTLY:
   "The rule repository does not contain sufficient information to determine this."
5. If required documents are listed in MISSING DOCUMENTS, respond ONLY with
   a document demand notice. Do not attempt any eligibility evaluation.
6. Every claim you make must cite its rule_id (e.g. [PROM_001]) or
   its source document (e.g. [Service Book, p.3]).
7. Use formal, professional language at all times.
8. Never guess. Never assume. Never extrapolate."""

    def build(
        self,
        question: str,
        retrieved_rules: List[Dict],
        extracted_facts: Dict,
        missing_documents: List[str],
        conversation_history: List[Dict]
    ) -> str:

        rules_text = self._format_rules(retrieved_rules)
        facts_text = self._format_facts(extracted_facts)
        missing_text = self._format_missing(missing_documents)
        history_text = self._format_history(conversation_history)

        return f"""{self.SYSTEM_PROMPT}

═══════════════════════════════════════
RETRIEVED RULES (from rules.md only):
═══════════════════════════════════════
{rules_text}

═══════════════════════════════════════
EMPLOYEE FACTS (from uploaded documents):
═══════════════════════════════════════
{facts_text}

═══════════════════════════════════════
MISSING DOCUMENTS (case cannot proceed without these):
═══════════════════════════════════════
{missing_text}

═══════════════════════════════════════
CONVERSATION HISTORY:
═══════════════════════════════════════
{history_text}

═══════════════════════════════════════
USER QUESTION:
═══════════════════════════════════════
{question}

YOUR RESPONSE:"""

    def _format_rules(self, rules: List[Dict]) -> str:
        if not rules:
            return "No relevant rules retrieved for this query."
        parts = []
        for r in rules:
            parts.append(
                f"[{r['rule_id']}] {r['rule_name']}\n{r['description']}"
            )
        return "\n\n".join(parts)

    def _format_facts(self, facts: Dict) -> str:
        if not facts:
            return "No employee facts available. Documents not yet uploaded."
        lines = []
        for key, val in facts.items():
            lines.append(f"• {key}: {val}")
        return "\n".join(lines)

    def _format_missing(self, missing: List[str]) -> str:
        if not missing:
            return "None — all required documents have been submitted."
        return "\n".join([f"✗ {doc}" for doc in missing])

    def _format_history(self, history: List[Dict]) -> str:
        if not history:
            return "No previous conversation."
        lines = []
        for msg in history[-6:]:  # last 6 messages only
            role = "User" if msg["role"] == "user" else "Assistant"
            lines.append(f"{role}: {msg['message']}")
        return "\n".join(lines)
```

---

## PHASE 7 — DOCUMENT INTELLIGENCE ENGINE

### Processing pipeline

```
User uploads file (PDF / JPG / PNG)
          ↓
File validation (type + size check)
          ↓
Save to uploads/ folder
          ↓
OCR Engine (Tesseract)
          ↓
Quality check (score < 0.70 → reject, request re-upload)
          ↓
Document classifier (what type of document is this?)
          ↓
Fact extractor (pull structured data from the text)
          ↓
Employee profile builder (merge facts from all documents)
          ↓
Document demand engine (are all required docs now present?)
          ↓
→ Missing docs: return demand notice
→ All present: proceed to eligibility engine
```

### ocr_engine.py

```python
# backend/app/document_intelligence/ocr_engine.py
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import os
from dataclasses import dataclass
from typing import List

@dataclass
class OCRResult:
    text: str
    quality_score: float
    page_count: int
    is_readable: bool
    rejection_reason: str = ""

class OCREngine:
    """
    Extracts text from uploaded PDFs and images using Tesseract.
    Returns a quality score — documents below 70% are rejected.
    """

    MIN_QUALITY = 0.70

    def process(self, file_path: str) -> OCRResult:
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".pdf":
            return self._process_pdf(file_path)
        elif ext in [".jpg", ".jpeg", ".png"]:
            return self._process_image(file_path)
        else:
            return OCRResult(
                text="", quality_score=0.0, page_count=0,
                is_readable=False,
                rejection_reason="Unsupported file type."
            )

    def _process_pdf(self, path: str) -> OCRResult:
        pages = convert_from_path(path, dpi=300)
        all_text = []
        all_scores = []

        for page in pages:
            data = pytesseract.image_to_data(
                page, output_type=pytesseract.Output.DICT
            )
            text = " ".join([
                w for w in data["text"] if w.strip()
            ])
            confidences = [
                c for c in data["conf"] if c != -1
            ]
            score = sum(confidences) / len(confidences) / 100 if confidences else 0
            all_text.append(text)
            all_scores.append(score)

        full_text = "\n".join(all_text)
        avg_score = sum(all_scores) / len(all_scores) if all_scores else 0

        readable = avg_score >= self.MIN_QUALITY
        reason = "" if readable else (
            f"Document quality score {avg_score:.0%} is below the "
            f"minimum {self.MIN_QUALITY:.0%}. "
            "Please re-upload a clearer scan or a digitally-generated PDF."
        )
        return OCRResult(
            text=full_text,
            quality_score=round(avg_score, 4),
            page_count=len(pages),
            is_readable=readable,
            rejection_reason=reason
        )

    def _process_image(self, path: str) -> OCRResult:
        image = Image.open(path)
        data = pytesseract.image_to_data(
            image, output_type=pytesseract.Output.DICT
        )
        text = " ".join([w for w in data["text"] if w.strip()])
        confidences = [c for c in data["conf"] if c != -1]
        score = sum(confidences) / len(confidences) / 100 if confidences else 0

        readable = score >= self.MIN_QUALITY
        reason = "" if readable else (
            f"Image quality score {score:.0%} is too low. "
            "Please upload a higher-resolution image."
        )
        return OCRResult(
            text=text, quality_score=round(score, 4),
            page_count=1, is_readable=readable,
            rejection_reason=reason
        )
```

### document_classifier.py

```python
# backend/app/document_intelligence/document_classifier.py
import re
from dataclasses import dataclass

@dataclass
class ClassificationResult:
    document_type: str
    confidence: float

class DocumentClassifier:
    """
    Identifies what type of document was uploaded based on
    keywords found in the OCR text.
    """

    SIGNATURES = {
        "Service Book": [
            "service book", "record of service", "date of appointment",
            "date of birth", "history of pay", "increment"
        ],
        "APAR": [
            "annual performance assessment", "apar", "appraisal",
            "assessment report", "overall grade", "integrity certificate",
            "benchmark", "adverse entry"
        ],
        "Leave Record": [
            "leave account", "earned leave", "casual leave",
            "leave without pay", "half pay leave", "leave balance"
        ],
        "Medical Certificate": [
            "medical certificate", "fit for duty", "certified sick",
            "medical officer", "hospital", "diagnosis"
        ],
        "Charge Sheet": [
            "charge sheet", "article of charge", "statement of imputation",
            "charged with", "departmental inquiry"
        ],
        "Penalty Order": [
            "penalty order", "punishment order", "penalty of",
            "reduction in pay", "censure", "withholding of increment",
            "compulsory retirement", "removal", "dismissal"
        ],
        "Promotion Order": [
            "promotion order", "promoted to", "appointed to the post",
            "with effect from", "from the post of", "to the post of"
        ],
        "Transfer Order": [
            "transfer order", "transferred to", "posted to",
            "relieved from", "joining report"
        ],
        "Departmental Exam Result": [
            "departmental examination", "ldce", "gdce",
            "examination result", "passed", "failed", "merit list"
        ],
        "Retirement Record": [
            "retirement", "superannuation", "last pay certificate",
            "no dues certificate", "settlement"
        ],
    }

    def classify(self, ocr_text: str) -> ClassificationResult:
        text_lower = ocr_text.lower()
        scores = {}

        for doc_type, keywords in self.SIGNATURES.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches > 0:
                scores[doc_type] = matches / len(keywords)

        if not scores:
            return ClassificationResult("Unknown", 0.0)

        best = max(scores, key=scores.get)
        return ClassificationResult(best, round(scores[best], 4))
```

---

## PHASE 8 — FACT EXTRACTORS

```python
# backend/app/document_intelligence/extractors/service_book_extractor.py
import re
from typing import Dict, Optional

class ServiceBookExtractor:
    """
    Pulls structured facts from a Service Book's OCR text.
    Uses regex patterns to find names, dates, designations, etc.
    """

    def extract(self, text: str) -> Dict:
        return {
            "employee_name":      self._find(text, r"name[:\s]+([A-Z][a-z]+(?:\s[A-Z][a-z]+)+)"),
            "employee_id":        self._find(text, r"(?:employee\s*id|staff\s*no|emp\s*no)[:\s#]+(\w+)", re.IGNORECASE),
            "designation":        self._find(text, r"designation[:\s]+(.+?)[\n,]", re.IGNORECASE),
            "department":         self._find(text, r"department[:\s]+(.+?)[\n,]", re.IGNORECASE),
            "pay_level":          self._find(text, r"(?:pay\s*level|level)[:\s]+(\d+)", re.IGNORECASE),
            "appointment_date":   self._find_date(text, r"(?:date of appointment|appointed on)[:\s]+"),
            "date_of_birth":      self._find_date(text, r"date of birth[:\s]+"),
            "retirement_date":    self._find_date(text, r"(?:date of retirement|due to retire)[:\s]+"),
            "promotion_history":  self._extract_promotions(text),
            "penalty_history":    self._extract_penalties(text),
        }

    def _find(self, text: str, pattern: str, flags=0) -> Optional[str]:
        match = re.search(pattern, text, flags)
        return match.group(1).strip() if match else None

    def _find_date(self, text: str, prefix_pattern: str) -> Optional[str]:
        date_pattern = prefix_pattern + r"(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})"
        return self._find(text, date_pattern, re.IGNORECASE)

    def _extract_promotions(self, text: str) -> list:
        # Look for promotion date patterns
        pattern = r"promoted.*?(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})"
        matches = re.findall(pattern, text, re.IGNORECASE)
        return [{"date": m} for m in matches]

    def _extract_penalties(self, text: str) -> list:
        pattern = r"(?:penalty|punishment|censure).*?(\d{4})"
        matches = re.findall(pattern, text, re.IGNORECASE)
        return [{"year": m} for m in matches]
```

---

## PHASE 9 — DOCUMENT DEMAND ENGINE

```python
# backend/app/core/document_demand_engine.py
import json
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class DemandResult:
    all_present: bool
    submitted: List[str]
    missing: List[str]
    demand_notice: str
    rule_citations: List[str]

class DocumentDemandEngine:
    """
    THE GATEKEEPER.

    Before ANY eligibility evaluation happens, this engine checks
    whether all required documents for the case domain have been
    submitted. If even one is missing, it blocks the case and
    returns a formal Document Demand Notice.

    The system will NOT call the LLM or run any rule evaluation
    until this check passes.
    """

    def __init__(self):
        req_path = Path(__file__).parent.parent / "knowledge" / "document_requirements.json"
        self.requirements = json.loads(req_path.read_text())

    def check(
        self,
        domain: str,
        submitted_doc_types: List[str],
        employee_facts: Dict = None
    ) -> DemandResult:

        domain_req = self.requirements.get(domain, {})
        mandatory = domain_req.get("mandatory", [])
        conditional = domain_req.get("conditional", {})
        rule_citations = domain_req.get("rule_citations", [])

        # Determine which conditional docs are needed
        required = list(mandatory)
        if employee_facts:
            for condition, docs in conditional.items():
                if self._condition_met(condition, employee_facts):
                    required.extend(docs)

        # Compare
        submitted_lower = [s.lower() for s in submitted_doc_types]
        missing = [
            doc for doc in required
            if not any(doc.lower() in s for s in submitted_lower)
        ]

        all_present = len(missing) == 0

        notice = "" if all_present else self._build_notice(
            domain, mandatory, missing, submitted_doc_types,
            rule_citations, domain_req.get("reasons", {})
        )

        return DemandResult(
            all_present=all_present,
            submitted=submitted_doc_types,
            missing=missing,
            demand_notice=notice,
            rule_citations=rule_citations
        )

    def _condition_met(self, condition: str, facts: Dict) -> bool:
        conditions = {
            "if_penalty_exists":   lambda f: bool(f.get("penalty_history")),
            "if_medical_grounds":  lambda f: f.get("leave_reason") == "medical",
            "if_hospitalized":     lambda f: f.get("hospitalized") is True,
            "if_appealing":        lambda f: f.get("appeal_filed") is True,
            "if_spouse_transfer":  lambda f: bool(f.get("spouse_transfer_order")),
        }
        evaluator = conditions.get(condition)
        return evaluator(facts) if evaluator else False

    def _build_notice(
        self,
        domain: str,
        mandatory: List[str],
        missing: List[str],
        submitted: List[str],
        citations: List[str],
        reasons: Dict
    ) -> str:

        submitted_lines = "\n".join([f"  ✓ {d}" for d in submitted]) or "  (none submitted yet)"
        missing_lines = "\n".join([f"  ✗ {d}  — REQUIRED" for d in missing])

        reason_lines = ""
        for doc in missing:
            reason = reasons.get(doc, f"Required to verify facts relevant to {domain} eligibility.")
            rule = ", ".join(citations) if citations else "applicable rule"
            reason_lines += f"\n  • {doc}: {reason} [{rule}]"

        return f"""
╔══════════════════════════════════════════════════════════════╗
║              DOCUMENT REQUIREMENT NOTICE                     ║
║              Case Type: {domain:<36}║
╚══════════════════════════════════════════════════════════════╝

To evaluate your {domain} request, the following documents
are required:

SUBMITTED ✓
{submitted_lines}

MISSING ✗ — CASE CANNOT PROCEED
{missing_lines}

WHY THESE DOCUMENTS ARE NEEDED:
{reason_lines}

⚠  This case cannot be evaluated until all required documents
   are uploaded. Please submit the missing documents to continue.
""".strip()
```

### document_requirements.json

```json
{
  "Promotion": {
    "mandatory": [
      "Service Book",
      "APAR (last 3 years)",
      "Departmental Exam Result"
    ],
    "conditional": {
      "if_penalty_exists": ["Penalty Order"]
    },
    "rule_citations": ["PROM_001", "PROM_004", "PROM_006"],
    "reasons": {
      "Service Book": "Required under Rule PROM_001 to verify service period and grade history.",
      "APAR (last 3 years)": "Required under Rule PROM_004 to verify benchmark performance rating.",
      "Departmental Exam Result": "Required under Rule PROM_006 to confirm examination clearance.",
      "Penalty Order": "Required under Rule DISC_003 to assess disciplinary status."
    }
  },
  "Leave.Earned": {
    "mandatory": ["Leave Application", "Service Book"],
    "conditional": {},
    "rule_citations": ["LEAVE_001"],
    "reasons": {
      "Leave Application": "Required to initiate the leave request.",
      "Service Book": "Required to verify leave balance and service record."
    }
  },
  "Leave.Medical": {
    "mandatory": ["Leave Application", "Medical Certificate", "Service Book"],
    "conditional": {
      "if_hospitalized": ["Hospital Discharge Summary"]
    },
    "rule_citations": ["LEAVE_005", "LEAVE_006"],
    "reasons": {
      "Leave Application": "Required to initiate the leave request.",
      "Medical Certificate": "Required under Rule LEAVE_005 from a recognized medical officer.",
      "Service Book": "Required to verify leave balance.",
      "Hospital Discharge Summary": "Required under Rule LEAVE_006 when hospitalization exceeds 48 hours."
    }
  },
  "Increment": {
    "mandatory": ["Service Book"],
    "conditional": {
      "if_penalty_exists": ["Penalty Order"]
    },
    "rule_citations": ["INCR_001"],
    "reasons": {
      "Service Book": "Required to verify service continuity and existing pay level.",
      "Penalty Order": "Required to check if increment has been withheld by order."
    }
  },
  "Discipline": {
    "mandatory": ["Service Book", "Charge Sheet"],
    "conditional": {
      "if_appealing": ["Appeal Letter", "Original Penalty Order"]
    },
    "rule_citations": ["DISC_001", "DISC_002"],
    "reasons": {
      "Service Book": "Required to verify employee's complete service and disciplinary history.",
      "Charge Sheet": "Required to review the nature and basis of the current charge.",
      "Appeal Letter": "Required to process the appeal against the penalty order.",
      "Original Penalty Order": "Required to review the order being appealed."
    }
  },
  "Transfer": {
    "mandatory": ["Service Book", "Transfer Application"],
    "conditional": {
      "if_medical_grounds": ["Medical Certificate"],
      "if_spouse_transfer": ["Spouse Transfer Order"]
    },
    "rule_citations": ["TRNF_001"],
    "reasons": {
      "Service Book": "Required to verify current posting and transfer history.",
      "Transfer Application": "Required as the formal application for transfer.",
      "Medical Certificate": "Required when transfer is sought on medical grounds.",
      "Spouse Transfer Order": "Required when seeking transfer on grounds of spouse posting."
    }
  },
  "DeptExam": {
    "mandatory": ["Service Book", "Exam Application"],
    "conditional": {},
    "rule_citations": ["EXAM_001"],
    "reasons": {
      "Service Book": "Required to verify eligibility criteria for the examination.",
      "Exam Application": "Required as the formal application to appear in the examination."
    }
  },
  "Retirement": {
    "mandatory": [
      "Service Book",
      "Pension Application",
      "Nomination Form",
      "Last Pay Certificate"
    ],
    "conditional": {},
    "rule_citations": ["RETR_001", "PENS_001"],
    "reasons": {
      "Service Book": "Required to verify qualifying service for pension.",
      "Pension Application": "Required as formal application for pension benefits.",
      "Nomination Form": "Required to designate family pension nominee.",
      "Last Pay Certificate": "Required to calculate pensionable pay."
    }
  }
}
```

---

## PHASE 10 — ELIGIBILITY ENGINE

```python
# backend/app/core/eligibility_engine.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from app.core.document_demand_engine import DocumentDemandEngine
from app.core.rag_pipeline import RAGPipeline
from app.core.llm_client import LLMClient
from app.core.prompt_builder import PromptBuilder

@dataclass
class EligibilityResult:
    decision: str                            # Eligible / Not Eligible / Cannot Determine
    eligibility_status: str
    supporting_rules: List[Dict] = field(default_factory=list)
    supporting_facts: List[Dict] = field(default_factory=list)
    missing_information: List[str] = field(default_factory=list)
    risk_indicators: List[str] = field(default_factory=list)
    administrative_notes: str = ""
    confidence_level: str = "Low"            # High / Medium / Low
    follow_up_questions: List[str] = field(default_factory=list)
    document_demand_notice: str = ""         # Set if documents are missing

class EligibilityEngine:
    """
    The main decision engine.

    Evaluation sequence (NEVER skip steps):
    1. Document completeness check → demand if missing
    2. Fact extraction from submitted documents
    3. Missing fact identification → ask follow-up questions
    4. Rule retrieval from RAG pipeline
    5. Rule evaluation against facts
    6. Decision generation with full reasoning
    """

    def __init__(self):
        self.demand_engine   = DocumentDemandEngine()
        self.rag             = RAGPipeline()
        self.llm             = LLMClient()
        self.prompt_builder  = PromptBuilder()

    async def evaluate(
        self,
        query: str,
        domain: str,
        submitted_docs: List[str],
        extracted_facts: Dict,
        conversation_history: List[Dict],
        db
    ) -> EligibilityResult:

        # ── Step 1: Document completeness gate ─────────────────────────
        demand = self.demand_engine.check(domain, submitted_docs, extracted_facts)
        if not demand.all_present:
            return EligibilityResult(
                decision="Cannot Determine",
                eligibility_status="Blocked — required documents missing",
                document_demand_notice=demand.demand_notice,
                administrative_notes="Case blocked pending document submission.",
                confidence_level="N/A"
            )

        # ── Step 2: Identify missing facts ─────────────────────────────
        missing_facts = self._identify_missing_facts(domain, extracted_facts)
        if missing_facts:
            questions = self._generate_questions(missing_facts)
            return EligibilityResult(
                decision="Cannot Determine",
                eligibility_status="Additional information required",
                missing_information=missing_facts,
                follow_up_questions=questions,
                confidence_level="N/A"
            )

        # ── Step 3: Retrieve relevant rules ────────────────────────────
        retrieved_rules = await self.rag.retrieve(query, db)
        if not retrieved_rules:
            return EligibilityResult(
                decision="Cannot Determine",
                eligibility_status="No applicable rules found",
                administrative_notes=(
                    "The rule repository does not contain sufficient "
                    "information to determine this."
                ),
                confidence_level="N/A"
            )

        # ── Step 4: Build prompt and call LLM ──────────────────────────
        prompt = self.prompt_builder.build(
            question=query,
            retrieved_rules=retrieved_rules,
            extracted_facts=extracted_facts,
            missing_documents=[],
            conversation_history=conversation_history
        )
        llm_response = await self.llm.generate(prompt)

        # ── Step 5: Parse decision from response ───────────────────────
        decision = self._parse_decision(llm_response)
        confidence = self._assess_confidence(retrieved_rules, extracted_facts)
        risks = self._identify_risks(extracted_facts)

        return EligibilityResult(
            decision=decision,
            eligibility_status=decision,
            supporting_rules=retrieved_rules,
            supporting_facts=self._format_facts(extracted_facts),
            risk_indicators=risks,
            administrative_notes=llm_response,
            confidence_level=confidence
        )

    def _identify_missing_facts(self, domain: str, facts: Dict) -> List[str]:
        required_facts = {
            "Promotion": [
                "service_years", "apar_rating", "exam_cleared", "penalty_history"
            ],
            "Leave.Medical": [
                "leave_type", "from_date", "to_date"
            ],
            "Increment": [
                "appointment_date", "pay_level", "last_increment_date"
            ],
        }
        needed = required_facts.get(domain, [])
        return [f for f in needed if not facts.get(f)]

    def _generate_questions(self, missing_facts: List[str]) -> List[str]:
        questions_map = {
            "service_years":        "How many years have you served in your current grade/post?",
            "apar_rating":          "What was your APAR rating for the last three years?",
            "exam_cleared":         "Have you cleared the required departmental examination? If yes, which one and when?",
            "penalty_history":      "Have you received any penalty or punishment in the last two years?",
            "appointment_date":     "What is your date of appointment to the current post?",
            "pay_level":            "What is your current pay level?",
            "last_increment_date":  "When was your last annual increment granted?",
            "leave_type":           "What type of leave are you applying for?",
            "from_date":            "What is the start date of the leave you are requesting?",
            "to_date":              "What is the end date of the leave you are requesting?",
        }
        return [
            questions_map.get(f, f"Please provide: {f}")
            for f in missing_facts
        ]

    def _parse_decision(self, response: str) -> str:
        r = response.lower()
        if "not eligible" in r or "ineligible" in r:
            return "Not Eligible"
        if "eligible" in r:
            return "Eligible"
        return "Cannot Determine"

    def _assess_confidence(self, rules: List, facts: Dict) -> str:
        if len(rules) >= 3 and len(facts) >= 5:
            return "High"
        if len(rules) >= 1 and len(facts) >= 2:
            return "Medium"
        return "Low"

    def _identify_risks(self, facts: Dict) -> List[str]:
        risks = []
        if facts.get("penalty_history"):
            risks.append("Active or recent disciplinary record detected.")
        if facts.get("apar_rating") in ["Average", "Poor", "Below Benchmark"]:
            risks.append("APAR rating may not meet the required benchmark.")
        return risks

    def _format_facts(self, facts: Dict) -> List[Dict]:
        return [{"fact": k, "value": v} for k, v in facts.items() if v]
```

---

## PHASE 11 — API ENDPOINTS

```
Authentication
POST   /api/auth/login
POST   /api/auth/logout
POST   /api/auth/refresh

Documents
POST   /api/documents/upload
GET    /api/documents/{id}
GET    /api/documents/case/{case_id}
DELETE /api/documents/{id}

Document Demands
GET    /api/demands/case/{case_id}
POST   /api/demands/{id}/fulfill

Cases
POST   /api/cases/
GET    /api/cases/{id}
GET    /api/cases/user/{user_id}

Chat
POST   /api/chat/message
GET    /api/chat/history/{case_id}
DELETE /api/chat/history/{case_id}

Eligibility
POST   /api/eligibility/check
GET    /api/eligibility/required-docs/{domain}

Rules
GET    /api/rules/
GET    /api/rules/{rule_id}
GET    /api/rules/domain/{domain}
POST   /api/rules/search
POST   /api/rules/ingest
POST   /api/rules/embed

Reports
POST   /api/reports/generate
GET    /api/reports/{id}

Admin
GET    /api/admin/audit-logs
GET    /api/admin/system-health
POST   /api/admin/rules/reingest

Health
GET    /health
```

---

## PHASE 12 — DECISION REPORT (PDF)

```python
# backend/app/core/report_generator.py
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from datetime import datetime
from pathlib import Path
from app.config import settings

NAVY  = colors.HexColor("#1a2744")
GOLD  = colors.HexColor("#c9a227")
WHITE = colors.white
LIGHT = colors.HexColor("#f5f5f5")

class ReportGenerator:
    """
    Generates a formal PDF administrative decision report.
    Saved to the reports/ folder and accessible via download endpoint.
    """

    def generate(self, result, case, employee) -> str:
        filename = f"report_{case.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        path = Path(settings.REPORTS_DIR) / filename
        doc = SimpleDocTemplate(str(path), pagesize=A4,
                                leftMargin=2*cm, rightMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        story = []
        styles = getSampleStyleSheet()

        # Header
        header_data = [[
            Paragraph("<font color='white'><b>RAILWAY ADMINISTRATIVE DECISION REPORT</b><br/>"
                      "CONFIDENTIAL — FOR OFFICIAL USE ONLY</font>", styles["Normal"])
        ]]
        header_table = Table(header_data, colWidths=[17*cm])
        header_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), NAVY),
            ("TEXTCOLOR",  (0,0), (-1,-1), WHITE),
            ("PADDING",    (0,0), (-1,-1), 12),
            ("ALIGN",      (0,0), (-1,-1), "CENTER"),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 0.5*cm))

        # Case details
        details = [
            ["Case Reference",  str(case.id)[:8].upper()],
            ["Date",            datetime.now().strftime("%d %B %Y")],
            ["Employee Name",   employee.get("employee_name", "—")],
            ["Employee ID",     employee.get("employee_id", "—")],
            ["Designation",     employee.get("designation", "—")],
            ["Query Type",      case.domain],
        ]
        detail_table = Table(details, colWidths=[5*cm, 12*cm])
        detail_table.setStyle(TableStyle([
            ("FONTNAME",   (0,0), (0,-1), "Helvetica-Bold"),
            ("BACKGROUND", (0,0), (0,-1), LIGHT),
            ("GRID",       (0,0), (-1,-1), 0.5, colors.grey),
            ("PADDING",    (0,0), (-1,-1), 6),
        ]))
        story.append(detail_table)
        story.append(Spacer(1, 0.5*cm))
        story.append(HRFlowable(width="100%", color=GOLD, thickness=2))
        story.append(Spacer(1, 0.3*cm))

        # Decision
        decision_color = (colors.HexColor("#1a6b2f") if result.decision == "Eligible"
                         else colors.HexColor("#8b1a1a"))
        decision_data = [[
            Paragraph(f"<font color='white'><b>DECISION: {result.decision.upper()}</b><br/>"
                      f"Confidence: {result.confidence_level}</font>", styles["Normal"])
        ]]
        decision_table = Table(decision_data, colWidths=[17*cm])
        decision_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), decision_color),
            ("PADDING",    (0,0), (-1,-1), 12),
            ("ALIGN",      (0,0), (-1,-1), "CENTER"),
        ]))
        story.append(decision_table)
        story.append(Spacer(1, 0.5*cm))

        # Rules applied
        story.append(Paragraph("<b>Rules Applied</b>", styles["Heading2"]))
        for rule in result.supporting_rules:
            story.append(Paragraph(
                f"[{rule['rule_id']}] {rule['rule_name']}",
                styles["Normal"]
            ))
        story.append(Spacer(1, 0.3*cm))

        # Supporting facts
        story.append(Paragraph("<b>Facts Established</b>", styles["Heading2"]))
        for fact in result.supporting_facts:
            story.append(Paragraph(
                f"• {fact['fact']}: {fact['value']}",
                styles["Normal"]
            ))
        story.append(Spacer(1, 0.3*cm))

        # Reasoning
        story.append(Paragraph("<b>Reasoning</b>", styles["Heading2"]))
        story.append(Paragraph(result.administrative_notes, styles["Normal"]))
        story.append(Spacer(1, 0.3*cm))

        # Disclaimer
        story.append(HRFlowable(width="100%", color=GOLD, thickness=1))
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph(
            "<i>This report is generated by the Railway Administrative AI Decision Support System. "
            "It is advisory in nature. Final administrative orders must be issued by the competent "
            "authority in accordance with extant rules. Rules authority: rules.md</i>",
            styles["Normal"]
        ))

        doc.build(story)
        return str(path)
```

---

## PHASE 13 — NEXT.JS FRONTEND

### How to create and start the frontend

```bash
# Navigate to project root
cd railway-admin-ai

# Create Next.js app
npx create-next-app@latest frontend \
  --typescript \
  --tailwind \
  --app \
  --no-src-dir

cd frontend

# Create environment file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start development server
npm run dev
# Open: http://localhost:3000
```

### Chat page with document demand notice

```tsx
// frontend/app/chat/page.tsx
"use client";
import { useState, useRef } from "react";
import DocumentStatusTracker from "@/components/documents/DocumentStatusTracker";
import DocumentDemandNotice from "@/components/chat/DocumentDemandNotice";
import MessageBubble from "@/components/chat/MessageBubble";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  type: "text" | "demand_notice" | "followup";
  rules_cited?: string[];
}

export default function ChatPage() {
  const [messages, setMessages]   = useState<Message[]>([]);
  const [input, setInput]         = useState("");
  const [loading, setLoading]     = useState(false);
  const [caseId, setCaseId]       = useState<string | null>(null);
  const [demandNotice, setDemand] = useState<string | null>(null);
  const [submittedDocs, setDocs]  = useState<string[]>([]);
  const [missingDocs, setMissing] = useState<string[]>([]);
  const fileRef = useRef<HTMLInputElement>(null);

  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMsg = input.trim();
    setInput("");
    setLoading(true);

    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      role: "user", content: userMsg, type: "text"
    }]);

    try {
      const res = await fetch("http://localhost:8000/api/chat/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg, case_id: caseId })
      });
      const data = await res.json();

      if (data.case_id) setCaseId(data.case_id);

      if (data.document_demand_notice) {
        setDemand(data.document_demand_notice);
        setMissing(data.missing_documents || []);
      } else {
        setDemand(null);
      }

      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: "assistant",
        content: data.response,
        type: data.message_type || "text",
        rules_cited: data.rules_cited || []
      }]);
    } finally {
      setLoading(false);
    }
  };

  const uploadFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !caseId) return;

    const formData = new FormData();
    formData.append("file", file);
    formData.append("case_id", caseId);

    const res = await fetch("http://localhost:8000/api/documents/upload", {
      method: "POST", body: formData
    });
    const data = await res.json();

    if (data.document_type) {
      setDocs(prev => [...prev, data.document_type]);
    }
    if (data.rejection_reason) {
      alert(`Document rejected: ${data.rejection_reason}`);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left: Document Panel */}
      <div className="w-96 border-r border-gray-200 bg-white p-4 flex flex-col gap-4">
        <h2 className="text-navy font-semibold text-lg border-b pb-2"
            style={{ color: "#1a2744" }}>
          Documents
        </h2>

        {/* Upload button */}
        <button
          onClick={() => fileRef.current?.click()}
          className="w-full py-2 px-4 border-2 border-dashed border-gray-300
                     rounded-lg text-gray-500 hover:border-blue-400 hover:text-blue-500
                     transition-colors text-sm"
        >
          + Upload Document (PDF / JPG / PNG)
        </button>
        <input ref={fileRef} type="file"
               accept=".pdf,.jpg,.jpeg,.png"
               onChange={uploadFile} className="hidden" />

        {/* Document status tracker */}
        <DocumentStatusTracker
          submitted={submittedDocs}
          missing={missingDocs}
        />
      </div>

      {/* Right: Chat */}
      <div className="flex-1 flex flex-col">
        {/* Document demand notice — shown prominently */}
        {demandNotice && (
          <DocumentDemandNotice notice={demandNotice} />
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-gray-400 mt-20">
              <p className="text-lg">Railway Administrative AI</p>
              <p className="text-sm mt-2">
                Ask about promotion, leave, increment, transfer, or discipline.
              </p>
            </div>
          )}
          {messages.map(msg => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
          {loading && (
            <div className="flex items-center gap-2 text-gray-400 text-sm">
              <div className="animate-bounce">●</div>
              <div className="animate-bounce delay-100">●</div>
              <div className="animate-bounce delay-200">●</div>
            </div>
          )}
        </div>

        {/* Input */}
        <div className="border-t bg-white p-4 flex gap-2">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && !e.shiftKey && sendMessage()}
            placeholder="Ask about promotion, leave, increment, transfer..."
            className="flex-1 border rounded-lg px-4 py-2 text-sm
                       focus:outline-none focus:ring-2 focus:ring-blue-300"
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="px-6 py-2 rounded-lg text-white text-sm font-medium
                       disabled:opacity-50 transition-colors"
            style={{ backgroundColor: "#1a2744" }}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
```

### DocumentDemandNotice component

```tsx
// frontend/components/chat/DocumentDemandNotice.tsx
interface Props { notice: string }

export default function DocumentDemandNotice({ notice }: Props) {
  return (
    <div className="mx-6 mt-4 border-2 border-red-400 rounded-lg
                    bg-red-50 p-4">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-red-600 font-bold text-sm">
          ⚠ REQUIRED DOCUMENTS MISSING — CASE CANNOT PROCEED
        </span>
      </div>
      <pre className="text-xs text-red-800 whitespace-pre-wrap font-mono">
        {notice}
      </pre>
    </div>
  );
}
```

### DocumentStatusTracker component

```tsx
// frontend/components/documents/DocumentStatusTracker.tsx
interface Props {
  submitted: string[];
  missing: string[];
}

export default function DocumentStatusTracker({ submitted, missing }: Props) {
  return (
    <div className="space-y-1">
      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
        Document Status
      </p>
      {submitted.map(doc => (
        <div key={doc}
             className="flex items-center gap-2 text-sm text-green-700 bg-green-50
                        rounded px-2 py-1">
          <span>✓</span><span>{doc}</span>
        </div>
      ))}
      {missing.map(doc => (
        <div key={doc}
             className="flex items-center gap-2 text-sm text-red-700 bg-red-50
                        rounded px-2 py-1">
          <span>✗</span><span>{doc}</span>
          <span className="text-xs text-red-400 ml-auto">required</span>
        </div>
      ))}
      {submitted.length === 0 && missing.length === 0 && (
        <p className="text-xs text-gray-400">
          No documents uploaded yet. Start a conversation first.
        </p>
      )}
    </div>
  );
}
```

---

## PHASE 14 — SECURITY

```python
# backend/app/utils/security.py
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from app.config import settings
import re

pwd_context = CryptContext(schemes=["bcrypt"])

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_minutes: int = 60) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=expires_minutes)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except JWTError:
        return {}

# PII masking for logs
PII_PATTERNS = [
    (r"\b\d{8}\b",                        "[EMP_ID]"),
    (r"\b[6-9]\d{9}\b",                  "[PHONE]"),
    (r"\b[A-Z]{5}\d{4}[A-Z]\b",          "[PAN]"),
    (r"\b\d{12}\b",                        "[AADHAAR]"),
]

def mask_pii(text: str) -> str:
    for pattern, replacement in PII_PATTERNS:
        text = re.sub(pattern, replacement, text)
    return text
```

```python
# backend/app/utils/file_validator.py
import magic   # pip install python-magic
from app.config import settings

ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}

class FileValidator:
    """
    Validates uploaded files by checking their actual content (magic bytes),
    not just their extension. Prevents malicious file uploads.
    """

    def validate(self, file_path: str, file_size: int) -> tuple[bool, str]:
        # Size check
        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            return False, f"File exceeds maximum size of {settings.MAX_FILE_SIZE_MB}MB."

        # Magic byte check (actual content, not just extension)
        mime = magic.from_file(file_path, mime=True)
        if mime not in ALLOWED_MIME_TYPES:
            return False, f"File type '{mime}' is not allowed. Only PDF, JPG, and PNG are accepted."

        return True, ""
```

---

## PHASE 15 — RUNNING THE COMPLETE SYSTEM

### Daily startup sequence (4 terminals)

```bash
# Terminal 1: Ollama (AI model server) — keep this running
ollama serve

# Terminal 2: FastAPI backend
cd railway-admin-ai/backend
source venv/bin/activate      # Windows: venv\Scripts\activate
uvicorn app.main:app --reload --port 8000

# Terminal 3: Next.js frontend
cd railway-admin-ai/frontend
npm run dev

# Terminal 4: One-time setup commands (run these only once)
# After backend starts, ingest rules.md:
curl -X POST http://localhost:8000/api/rules/ingest
# Then create embeddings:
curl -X POST http://localhost:8000/api/rules/embed
```

### Verification checklist

```
□ http://localhost:8000/health          → {"status": "ok"}
□ http://localhost:8000/docs            → FastAPI Swagger UI
□ http://localhost:3000                 → Next.js frontend loads
□ POST /api/rules/ingest                → rules.md parsed successfully
□ POST /api/rules/embed                 → embeddings created
□ POST /api/rules/search {"query":"promotion"} → returns relevant rules
□ POST /api/chat/message {"message": "Am I eligible for promotion?"}
                                        → returns document demand notice
```

---

## OPTIONAL PHASE 16 — DOCKER (ONLY WHEN READY TO DEPLOY)

When your application is fully working natively and you want to share it with others or put it on a server, you add Docker. **Your code does not change at all.**

You only add three files:

### backend/Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y \
    tesseract-ocr poppler-utils libmagic1 && \
    rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### frontend/Dockerfile

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
CMD ["npm", "start"]
```

### docker-compose.yml (root folder)

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_DB: railway_ai
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  ollama:
    image: ollama/ollama
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"

  backend:
    build: ./backend
    env_file: .env
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - ollama

  frontend:
    build: ./frontend
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  pgdata:
  ollama_data:
```

### To deploy with Docker

```bash
# Build and start everything
docker compose up --build

# Pull the Qwen3 model into the container (run once)
docker exec railway-admin-ai-ollama-1 ollama pull qwen3
```

**That's it.** The same code that ran natively now runs in Docker. The only things that changed are those three files above.

---

## HALLUCINATION PREVENTION CONTROLS

| Control | How it works |
|---|---|
| System prompt constraint | LLM is explicitly forbidden from using training knowledge |
| Retrieval threshold | Rules with similarity score below 0.30 are discarded |
| No-answer protocol | If retrieval returns nothing → standard "not in repository" message |
| Fact grounding | Every fact must cite its source document |
| Missing document gate | LLM is never called if required documents are missing |
| Citation enforcement | Every rule used in the answer must include its rule_id |

---

## DECISION REPORT FORMAT

```
╔══════════════════════════════════════════════════════════════════╗
║          RAILWAY ADMINISTRATIVE DECISION REPORT                  ║
║          CONFIDENTIAL — FOR OFFICIAL USE ONLY                    ║
╚══════════════════════════════════════════════════════════════════╝

CASE REFERENCE      : CASE-001234
DATE OF REPORT      : 15 June 2024
EMPLOYEE NAME       : Ramesh Kumar
EMPLOYEE ID         : 12345678
DESIGNATION         : Senior Section Engineer
DIVISION            : Chennai Division
QUERY TYPE          : Promotion Eligibility

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SECTION 1 — DECISION

  ELIGIBILITY STATUS : ✓ ELIGIBLE
  CONFIDENCE LEVEL   : HIGH

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SECTION 2 — DOCUMENTS VERIFIED

  ✓ Service Book (45 pages, quality: 94%)
  ✓ APAR 2021-22 (rating: Very Good)
  ✓ APAR 2022-23 (rating: Very Good)
  ✓ APAR 2023-24 (rating: Outstanding)
  ✓ LDCE Examination Result (Pass, 2009)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SECTION 3 — FACTS ESTABLISHED

  Service Period     : 19 years (Service Book, p.3)
  Grade Service      : 14 years in SSE grade
  APAR Average       : Very Good / Outstanding (last 3 years)
  Exam Cleared       : LDCE Pass, 2009
  Disciplinary Record: Clean — no active penalty
  Vigilance Status   : Clear

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SECTION 4 — RULES APPLIED

  [PROM_001] Minimum service requirement — SATISFIED
  [PROM_004] APAR benchmark requirement — SATISFIED
  [PROM_006] Departmental exam clearance — SATISFIED
  [DISC_003] No active penalty condition — SATISFIED

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SECTION 5 — REQUIRED NEXT STEPS

  1. Submit promotion application to Personnel Branch
  2. Produce original Service Book for physical verification
  3. Obtain vigilance clearance certificate
  4. Approval by competent authority: DRM (Rule PROM_011)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SECTION 6 — ADMINISTRATIVE NOTE

  This report is advisory. Final orders must be issued by the
  competent authority. Rules authority: rules.md | Version: 3.0
```

---

## FINAL QUALITY STANDARDS

Every system output must satisfy:

**Correctness** — Decision matches what rules.md mandates  
**Explainability** — Every claim traces to a rule_id or document page  
**Completeness** — All required documents identified and demanded before proceeding  
**Traceability** — Full audit trail from query to decision  
**Transparency** — Confidence levels and limitations always disclosed  
**Reliability** — System refuses to guess; prefers "cannot determine" over hallucination  
**Professionalism** — Government-grade language; formal, precise, unambiguous  

---

*This is the complete and authoritative design document for the Railway Employee Administrative Decision Support AI System — Version 3.0. Build natively first. Add Docker only when you are ready to deploy to a server. rules.md remains the sole and exclusive authority for all administrative rules, conditions, and decisions.*
