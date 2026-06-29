# 🖥 RailVera Backend

FastAPI-powered REST API backend for the RailVera Decision Support AI Portal.

---

## Overview

This backend is responsible for:
- **Authentication** — JWT-based login for employees and personnel officers
- **Case Management** — Create and track administrative cases
- **Document Pipeline** — Upload → OCR → Classify → Extract facts
- **AI Eligibility Engine** — RAG + Gemini 2.5-flash for rule-grounded decisions
- **PDF Report Generation** — Signed decision reports using ReportLab
- **Rule Ingestion** — Auto-parses `rules.md` and stores vector embeddings in PostgreSQL

---

## Requirements

- Python **3.11 or higher**
- pip (comes with Python)
- A PostgreSQL database with the **pgvector** extension enabled
  - Easiest option: [Supabase](https://supabase.com/) free tier (pgvector is pre-enabled)
- A **Google Gemini API key** from [aistudio.google.com](https://aistudio.google.com/apikey) *(or a local Ollama setup)*

---

## Setup

### 1. Create a virtual environment

```bash
cd backend

# Create the environment
python -m venv .venv

# Activate it
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS/Linux
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
copy .env.example .env    # Windows
cp .env.example .env      # macOS/Linux
```

Edit `.env` with your values:

```env
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
SECRET_KEY=any-long-random-string
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIzaSy...
GEMINI_MODEL=gemini-2.5-flash
```

### 4. Run the server

```bash
python -m uvicorn app.main:app --reload --port 8000
```

**On first startup**, the server automatically:
1. Connects to the database
2. Reads `app/knowledge/rules.md`
3. Parses all rules and stores them in the DB
4. Generates vector embeddings for semantic rule search

This takes about **30–60 seconds** on first run. Subsequent starts are instant.

---

## API Explorer

Once running, visit:

- **Swagger UI** → http://localhost:8000/docs  
- **ReDoc** → http://localhost:8000/redoc  
- **Health Check** → http://localhost:8000/health

All API endpoints require a JWT token in the `Authorization: Bearer <token>` header (except `/api/auth/login` and `/api/auth/register`).

---

## Key Modules

### `app/core/llm_client.py`
The unified LLM interface. Automatically selects the best available provider:

```
1. GeminiLLMClient    — Google Gemini via REST API (no SDK needed)
2. OllamaLLMClient    — Local Ollama daemon (fallback)
3. Programmatic engine — Deterministic rule engine (always works)
```

### `app/core/rag_pipeline.py`
Retrieval-Augmented Generation pipeline:
- Embeds rules using `BAAI/bge-small-en-v1.5`
- Reranks results using `BAAI/bge-reranker-base`
- Retrieves the top relevant rules for any user question

### `app/document_intelligence/`
Three-stage document processing:
1. **OCR Engine** — Extracts text from PDFs and images using Tesseract
2. **Document Classifier** — Identifies the document type (Service Book, APAR, etc.)
3. **LLM Extractor** — Pulls structured facts from the text (years of service, APAR rating, etc.)

### `app/knowledge/rules.md`
The single source of truth for all administrative rules. Written in structured Markdown. The `RuleExtractor` parses it and loads it into the database automatically.

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | ✅ | — | Async PostgreSQL URL |
| `DATABASE_URL_SYNC` | No | — | Sync URL (for migrations only) |
| `SECRET_KEY` | ✅ | — | JWT secret key |
| `LLM_PROVIDER` | No | `gemini` | `gemini` or `ollama` |
| `GEMINI_API_KEY` | If Gemini | — | Google AI Studio key |
| `GEMINI_MODEL` | No | `gemini-2.5-flash` | Model name |
| `OLLAMA_URL` | If Ollama | `http://localhost:11434` | Ollama endpoint |
| `UPLOAD_DIR` | No | `./uploads` | Document storage directory |
| `REPORTS_DIR` | No | `./reports` | PDF output directory |
| `MAX_FILE_SIZE_MB` | No | `20` | Upload size limit |

---

## Project Structure

```
backend/
├── app/
│   ├── api/                  # HTTP route handlers
│   │   ├── auth.py
│   │   ├── cases.py
│   │   ├── chat.py
│   │   ├── documents.py
│   │   ├── eligibility.py
│   │   ├── reports.py
│   │   └── rules.py
│   │
│   ├── core/                 # Business logic
│   │   ├── eligibility_engine.py
│   │   ├── llm_client.py
│   │   ├── prompt_builder.py
│   │   ├── rag_pipeline.py
│   │   ├── rule_extractor.py
│   │   └── document_demand_engine.py
│   │
│   ├── document_intelligence/
│   │   ├── ocr_engine.py
│   │   ├── document_classifier.py
│   │   └── llm_extractor.py
│   │
│   ├── models/               # Database table definitions
│   ├── schemas/              # Pydantic data models
│   ├── database/             # DB connection setup
│   ├── knowledge/
│   │   └── rules.md          # ← Administrative rulebook (edit this)
│   ├── config.py             # Settings loader
│   └── main.py               # Application entry point
│
├── .env                      # 🔒 Your secrets (never commit this)
├── .env.example              # Template
└── requirements.txt
```

---

## Adding or Editing Rules

1. Open `app/knowledge/rules.md`
2. Add or modify rules following the existing format
3. Restart the backend
4. The system will detect new rules and generate embeddings automatically

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError` | Make sure your virtual environment is **activated** before running |
| `getaddrinfo failed` | Temporary DNS issue — wait a moment and retry |
| `Quota exceeded` | Switch to `GEMINI_MODEL=gemini-2.5-flash` in `.env` |
| `OCR running in simulation mode` | Install Tesseract OCR and add to system PATH |
| Database errors on startup | Double-check `DATABASE_URL` format and that pgvector extension is enabled |
