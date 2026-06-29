# 🚂 RailVera — Indian Railways Decision Support AI Portal

<div align="center">

![RailVera](https://img.shields.io/badge/RailVera-v3.0-1A365D?style=for-the-badge&logo=railway&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_2.5_Flash-AI-4285F4?style=for-the-badge&logo=google&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-336791?style=for-the-badge&logo=postgresql&logoColor=white)

**An AI-powered administrative decision support system for Indian Railways Personnel management.**  
Upload employee documents, ask eligibility questions in plain English, and receive instant, rule-grounded decisions.

[🚀 Quick Start](#-quick-start) • [📖 Features](#-features) • [🏗 Architecture](#-architecture) • [📁 Project Structure](#-project-structure) • [🔧 Configuration](#-configuration)

</div>

---

## 📖 What is RailVera?

RailVera is a full-stack web application designed to assist **Indian Railways HR and Personnel Officers** in making accurate, rule-based administrative decisions — such as promotions, transfers, retirements, and disciplinary reviews.

Instead of manually searching through rulebooks, an officer can:
1. **Open a case** for an employee in a specific domain (e.g. *Promotion*, *Transfer*)
2. **Upload scanned documents** (Service Book, APAR, Medical Certificates, etc.)
3. **Ask a question** in plain English — *"Is this employee eligible for promotion?"*
4. **Receive an instant AI decision** citing the exact rules that apply
5. **Generate a signed PDF report** for official records

The system uses **Google Gemini 2.5-flash** for reasoning, with a built-in deterministic fallback that works even without internet access.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **AI Chat Interface** | Conversational eligibility decisions powered by Gemini 2.5-flash |
| 📄 **Document OCR Pipeline** | Upload PDFs/images — automatically read, classified, and fact-extracted |
| ⚖️ **Rule-Grounded Decisions** | RAG pipeline retrieves relevant rules from a structured rulebook |
| 🗂 **Case Management** | Create, track, and close administrative cases |
| 👮 **HR Officer Review** | Human-in-the-loop: Officers can approve/reject AI decisions |
| 📊 **PDF Report Generation** | Auto-generate official decision reports with rule citations |
| 🔐 **JWT Authentication** | Secure login with role-based access (Employee / Personnel Officer) |
| 🔁 **Smart Fallback Chain** | Gemini → Ollama → Deterministic engine: always produces a decision |
| 🌐 **Cloud-Ready** | Supabase (PostgreSQL + pgvector) for zero-config cloud database |

---

## 🏗 Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js 14)                      │
│   Chat UI · Case Manager · Document Upload · PDF Viewer       │
└────────────────────────┬─────────────────────────────────────┘
                         │ REST API (HTTP/JSON)
┌────────────────────────▼─────────────────────────────────────┐
│                   Backend (FastAPI v3.0)                      │
│                                                               │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ Auth / JWT  │  │ Case Manager │  │  Eligibility Engine  │ │
│  └─────────────┘  └──────────────┘  └──────────┬───────────┘ │
│                                                 │             │
│  ┌──────────────────────┐         ┌─────────────▼──────────┐  │
│  │  Document Pipeline   │         │      RAG Pipeline      │  │
│  │  OCR → Classify →    │         │  Embed → Search Rules  │  │
│  │  Fact Extraction     │         └─────────────┬──────────┘  │
│  └──────────────────────┘                       │             │
│                                      ┌──────────▼──────────┐  │
│                                      │    LLM Client       │  │
│                                      │  Gemini 2.5-flash   │  │
│                                      │  → Ollama fallback  │  │
│                                      │  → Deterministic    │  │
│                                      └─────────────────────┘  │
└───────────────────────────────────┬──────────────────────────┘
                                    │
┌───────────────────────────────────▼──────────────────────────┐
│              PostgreSQL + pgvector (Supabase)                 │
│   Users · Cases · Documents · Rules (with embeddings) ·      │
│   Conversation History · Audit Logs                          │
└──────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
railway-admin-ai/
│
├── backend/                        # FastAPI Python backend
│   ├── app/
│   │   ├── api/                    # REST API endpoints
│   │   │   ├── auth.py             # Login, register, JWT refresh
│   │   │   ├── cases.py            # Case CRUD + conversation
│   │   │   ├── documents.py        # Upload + OCR pipeline
│   │   │   ├── eligibility.py      # Run eligibility check
│   │   │   ├── rules.py            # Rules management
│   │   │   ├── reports.py          # PDF report generation
│   │   │   └── chat.py             # Chat history
│   │   │
│   │   ├── core/                   # Business logic
│   │   │   ├── llm_client.py       # Gemini + Ollama + fallback
│   │   │   ├── prompt_builder.py   # LLM system prompt
│   │   │   ├── eligibility_engine.py # Main decision loop
│   │   │   ├── rag_pipeline.py     # Rule retrieval (vector search)
│   │   │   ├── rule_extractor.py   # Parse rules.md → DB
│   │   │   └── document_demand_engine.py # Required doc checker
│   │   │
│   │   ├── document_intelligence/  # OCR + classification
│   │   │   ├── ocr_engine.py       # Tesseract OCR
│   │   │   ├── document_classifier.py # Rule-based classifier
│   │   │   └── llm_extractor.py    # Fact extraction from text
│   │   │
│   │   ├── models/                 # SQLAlchemy DB models
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   ├── database/               # DB connection + session
│   │   ├── knowledge/              # rules.md (the rulebook)
│   │   ├── config.py               # App settings (reads .env)
│   │   └── main.py                 # FastAPI app entry point
│   │
│   ├── .env                        # 🔒 Your environment variables
│   ├── .env.example                # Template — copy this to .env
│   └── requirements.txt            # Python dependencies
│
├── frontend/                       # Next.js 14 frontend
│   ├── app/
│   │   ├── page.tsx                # Landing / login page
│   │   └── chat/
│   │       └── page.tsx            # Main chat + case UI
│   ├── components/
│   │   └── chat/
│   │       └── MessageBubble.tsx   # Chat message renderer
│   ├── lib/
│   │   └── api.ts                  # All API calls to backend
│   ├── .env.local                  # Frontend environment vars
│   └── package.json
│
└── README.md                       # You are here
```

---

## 🚀 Quick Start

> **Prerequisites:** Python 3.11+, Node.js 18+, a Supabase account (free), and a Google AI Studio API key (free).

### Step 1 — Clone the repository

```bash
git clone https://github.com/your-org/railVera.git
cd railVera/railway-admin-ai
```

### Step 2 — Set up the Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate it
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3 — Configure environment variables

```bash
# Copy the template
copy .env.example .env    # Windows
cp .env.example .env      # macOS/Linux
```

Now open `.env` and fill in your values:

```env
# Your Supabase PostgreSQL connection string
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname

# A long random string for JWT signing (any random text works)
SECRET_KEY=your-super-secret-key-here

# Google Gemini API key (get one free at https://aistudio.google.com/apikey)
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIzaSy...your-key-here
GEMINI_MODEL=gemini-2.5-flash
```

> 📌 See the [full configuration guide](#-configuration) for all options.

### Step 4 — Start the backend server

```bash
# Make sure you're in the backend/ folder and venv is active
python -m uvicorn app.main:app --reload --port 8000
```

On first start, it will automatically:
- Connect to the database
- Read and embed all rules from `app/knowledge/rules.md`
- Be ready at **http://localhost:8000**

You can verify it's working by opening **http://localhost:8000/docs** — the interactive API explorer.

### Step 5 — Set up the Frontend

Open a **new terminal** window:

```bash
cd frontend

# Install dependencies
npm install

# Configure the frontend
# Create a .env.local file with:
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start the development server
npm run dev
```

The frontend will be available at **http://localhost:3000** ✅

---

## 🔧 Configuration

All backend configuration is done via the `.env` file in the `backend/` folder.

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | ✅ Yes | — | PostgreSQL async connection string |
| `SECRET_KEY` | ✅ Yes | — | JWT signing secret (make it long and random) |
| `LLM_PROVIDER` | No | `gemini` | `gemini` or `ollama` |
| `GEMINI_API_KEY` | If using Gemini | — | Key from [aistudio.google.com](https://aistudio.google.com/apikey) |
| `GEMINI_MODEL` | No | `gemini-2.5-flash` | Gemini model to use |
| `OLLAMA_URL` | If using Ollama | `http://localhost:11434` | Local Ollama server URL |
| `UPLOAD_DIR` | No | `./uploads` | Where uploaded documents are stored |
| `REPORTS_DIR` | No | `./reports` | Where generated PDFs are saved |
| `MAX_FILE_SIZE_MB` | No | `20` | Maximum upload file size |

### Frontend `.env.local`

| Variable | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` |

---

## 🤖 LLM Provider Options

RailVera supports three LLM modes with automatic fallback:

```
Primary → Secondary → Always-on fallback
```

### Option A — Google Gemini (Recommended, cloud)
- Works on **any device**, no GPU required
- Get a free API key at [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)
- Set `LLM_PROVIDER=gemini` and `GEMINI_API_KEY=AIzaSy...`

### Option B — Ollama (Local, no internet required)
- Runs on your own machine, **completely private**
- Requires [Ollama](https://ollama.ai) installed and running
- Pull a model: `ollama pull qwen3`
- Set `LLM_PROVIDER=ollama`

### Option C — Deterministic Fallback (Always available)
- Activates automatically if both Gemini and Ollama are unreachable
- Rule-based engine — no AI, no network required
- Always produces a valid decision

---

## 📄 Supported Document Types

| Document | Auto-Classified | Facts Extracted |
|---|---|---|
| Service Book | ✅ | Service years, grade, pay scale |
| APAR (last 3 years) | ✅ | Annual rating, benchmark status |
| Departmental Exam Result | ✅ | Pass/fail, exam type |
| Medical Certificate | ✅ | Fitness status |
| Charge Sheet | ✅ | Disciplinary action type |
| Penalty Order | ✅ | Penalty imposed |
| Transfer Order | ✅ | Transfer details |
| Retirement Record | ✅ | Retirement date, type |

> **Note:** OCR runs using Tesseract. Install Tesseract on your system for best results.  
> On Windows: [Tesseract Installer](https://github.com/UB-Mannheim/tesseract/wiki)  
> Without Tesseract, the system runs in simulation mode.

---

## 🌐 API Reference

The full interactive API documentation is auto-generated at:  
**http://localhost:8000/docs** (Swagger UI)  
**http://localhost:8000/redoc** (ReDoc)

### Key Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/login` | Log in and receive a JWT token |
| `POST` | `/api/auth/register` | Register a new user |
| `GET` | `/api/cases/me` | List all your cases |
| `POST` | `/api/cases` | Create a new case |
| `POST` | `/api/documents/upload` | Upload a document to a case |
| `POST` | `/api/eligibility/check` | Run eligibility evaluation |
| `POST` | `/api/cases/{id}/reply` | Send a follow-up message |
| `POST` | `/api/reports/generate` | Generate a PDF decision report |
| `GET` | `/health` | Health check |

---

## 🔒 Security Notes

- **Never commit your `.env` file** — it contains secrets. It is already in `.gitignore`.
- The `SECRET_KEY` should be a long, random string. Generate one with:
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
- All passwords are hashed using `bcrypt`.
- All API endpoints (except login/register) require a valid JWT token.

---

## 🐛 Troubleshooting

| Problem | Solution |
|---|---|
| `[Errno 11001] getaddrinfo failed` | Intermittent DNS issue. Wait a moment and retry. |
| `API key not valid` | Ensure your Gemini key starts with `AIzaSy`. Re-copy from AI Studio. |
| `Quota exceeded for gemini-2.0-flash` | Use `GEMINI_MODEL=gemini-2.5-flash` in your `.env` |
| `OCR running in simulation mode` | Install [Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) and add it to PATH |
| Backend shows `Database connection failed` | Check your `DATABASE_URL` in `.env` is correct |
| Frontend shows blank page | Make sure backend is running on port 8000 and `.env.local` is set |

---

## 🛠 Tech Stack

**Backend**
- [FastAPI](https://fastapi.tiangolo.com/) — High-performance Python web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) + [asyncpg](https://github.com/MagicStack/asyncpg) — Async database ORM
- [pgvector](https://github.com/pgvector/pgvector) — Vector similarity search in PostgreSQL
- [Sentence Transformers](https://www.sbert.net/) + [FlagEmbedding](https://github.com/FlagOpen/FlagEmbedding) — Rule embeddings & reranking
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) via pytesseract — Document text extraction
- [ReportLab](https://www.reportlab.com/) — PDF generation
- [httpx](https://www.python-httpx.org/) — Async HTTP client (Gemini API)

**Frontend**
- [Next.js 14](https://nextjs.org/) — React framework with App Router
- [TypeScript](https://www.typescriptlang.org/) — Type-safe JavaScript
- [Tailwind CSS](https://tailwindcss.com/) — Utility-first styling
- [Lucide React](https://lucide.dev/) — Icon library

**Infrastructure**
- [Supabase](https://supabase.com/) — Managed PostgreSQL with pgvector
- [Google Gemini 2.5-flash](https://ai.google.dev/) — Primary AI reasoning engine

---

## 📜 License

This project is developed for academic and research purposes as part of a final-year submission for Indian Railways administrative AI systems.

---

<div align="center">
  Made with ❤️ for Indian Railways  
  <br/>
  <strong>RailVera v3.0</strong>
</div>
