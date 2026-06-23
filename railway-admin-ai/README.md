# Railway Employee Administrative Decision Support AI

An explainable, rules-bound AI assistant acting as a digital Railway Personnel Officer, ensuring deterministic eligibility evaluation, document demand verification, and formal decision reporting. 

All decision logic is grounded strictly in [rules.md](file:///c:/Users/Chad/railvera/railway-admin-ai/backend/app/knowledge/rules.md) to eliminate hallucinations.

---

## 📂 Project Structure

```
railway-admin-ai/
├── backend/                       # FastAPI Python 3.11 Backend
│   ├── app/
│   │   ├── database/              # DB connections & migrations
│   │   ├── api/                   # REST API routes
│   │   ├── core/                  # RAG, LLM prompting, & decision engine
│   │   ├── document_intelligence/ # Tesseract OCR, classifiers, & extractors
│   │   ├── models/                # SQLAlchemy database models
│   │   ├── schemas/               # Pydantic validation schemas
│   │   ├── knowledge/             # Rules database (rules.md)
│   │   └── utils/                 # Security, auditing, & validation utils
│   ├── uploads/                   # Uploaded employee documents (evidence)
│   ├── reports/                   # Programmatically generated decision PDFs
│   └── tests/                     # Backend unit tests
└── frontend/                      # Next.js 14 Web Application
    ├── app/                       # App router pages (Chat, Eligibility, Docs)
    ├── components/                # Shared layout & feature components
    └── lib/                       # API clients & utilities
```

---

## 🛠️ Local Native Setup Checklist

Follow these steps in order to install requirements and start the application locally on Windows.

### Prerequisite Installations
1. **Python 3.11**: [Download Python](https://www.python.org/downloads/). Verify during setup that `"Add Python to PATH"` is checked.
2. **Node.js 20**: [Download Node.js LTS](https://nodejs.org/).
3. **PostgreSQL 15**: [Download PostgreSQL](https://www.postgresql.org/downloads/). Note the database password you define.
   - Run `CREATE EXTENSION IF NOT EXISTS vector;` inside pgAdmin to enable vector similarity operations.
4. **Ollama**: [Download Ollama](https://ollama.com/download). Run `ollama pull qwen3` in Command Prompt to fetch the AI model.
5. **Tesseract OCR**: [Download Tesseract Installer](https://github.com/UB-Mannheim/tesseract/wiki). Ensure Tesseract is added to your environment `PATH`.

---

## 🚀 Running the Application

### 1. Start Database & Local AI services
- Ensure the **PostgreSQL** service is running.
- In a terminal, start **Ollama**:
  ```bash
  ollama serve
  ```

### 2. Run Backend (FastAPI)
Navigate to the `backend` folder, configure settings, install dependencies, and run:
```bash
cd backend
copy .env.example .env
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
- API Health Status: [http://localhost:8000/health](http://localhost:8000/health)
- API Documentation (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Run Frontend (Next.js)
Navigate to the `frontend` folder and run:
```bash
cd frontend
npm install
npm run dev
```
- Frontend Web App: [http://localhost:3000](http://localhost:3000)

---

## ✅ System Ingestion Verification

After starting the backend and database services, perform a one-time ingestion command to populate the rule repository and build vector index search entries:

1. **Ingest Rules Markdown**:
   ```bash
   curl -X POST http://localhost:8000/api/rules/ingest
   ```
2. **Generate Vector Embeddings**:
   ```bash
   curl -X POST http://localhost:8000/api/rules/embed
   ```
