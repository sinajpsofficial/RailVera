<div align="center">

<img src="railway-admin-ai/frontend/app/icon.png" width="128" height="128" alt="RailVera Logo" />

# 🚂 RailVera Workspace

### *Indian Railways Departmental Decision Support & Eligibility System*

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Gemini](https://img.shields.io/badge/Google_Gemini-2.5_Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://deepmind.google/technologies/gemini)

**RailVera** is an advanced AI-powered personnel decision support portal designed for **HR and Personnel Officers** in the Indian Railways. It reads, parses, vectorizes, and queries complex departmental rules to automate promotion, leave, and transfer eligibility evaluations.

</div>

---

## 🏗 System Architecture & Workflow

Here is how the RAG (Retrieval-Augmented Generation) pipeline processes rules from the workspace root to generate grounded decisions:

```mermaid
flowchart TD
    subgraph Ingestion_Phase["1. Rules Ingestion (Startup)"]
        A[rules.md] -->|Custom Markdown Parser| B(Parsed Rules Blocks)
        B -->|HuggingFace Embedder| C(384-dimensional Vectors)
        C -->|pgvector INSERT| D[(Supabase PostgreSQL)]
    end

    subgraph Query_Phase["2. Eligibility Decision Loop"]
        E[HR Officer Query] -->|Embedding Search| F(Vector Similarity Match)
        D -->|Retrieve Relevant Rules| F
        F -->|Prompt Context Assembly| G[Gemini 2.5-Flash LLM]
        G -->|Generate Decision| H{Decision Success?}
        H -->|Yes| I[Output grounded decision with Citations]
        H -->|No Fallback| J[Ollama Local LLM]
        J -->|Failed?| K[Deterministic Rule Engine]
    end
```

---

## 📁 Workspace Map

The workspace contains both the core datasets and the codebase:

| Resource / Directory | Description |
| :--- | :--- |
| **[`rules.md`](file:///c:/Users/Navami/project/RailVera/rules.md)** | The complete rulebook dataset containing leave, promotion, and transfer policies. |
| **[`railway-admin-ai/`](file:///c:/Users/Navami/project/RailVera/railway-admin-ai)** | The application package consisting of the Next.js frontend and FastAPI backend. |
| **[`Railway_Admin_AI_Master_Prompt_v2.md`](file:///c:/Users/Navami/project/RailVera/Railway_Admin_AI_Master_Prompt_v2.md)** | Master specification prompt detailing prompt structures and domain rules. |

---

## ✨ Key Features

* 🤖 **Double-Grounded RAG**: Combines vector database semantic search with a rules-based logical engine to completely avoid AI hallucinations.
* 📄 **Document Intelligence**: Deep OCR parsing of scanned railway Service Books, APARs, and Medical Certificates.
* 🛡️ **JWT Security**: Role-based access control segregating Personnel Officers from general Employees.
* 📜 **Automated PDF Reports**: Instant download of official generated eligibility PDF reports signed and ready for administrative filing.

---

## 🚀 Quick Setup & Run

Ensure you have configured your environment variables inside `railway-admin-ai/backend/.env` before launching.

### 1. Launch the Backend API
```bash
cd railway-admin-ai/backend
python -m venv .venv
# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run FastAPI backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Launch the Web Portal
```bash
cd railway-admin-ai/frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to view the portal.

---

<div align="center">
Developed for the Indian Railways Personnel Department.
</div>
