# RailVera Deployment & Quick Setup Guide

This guide describes how to run, bootstrap, and deploy **RailVera** locally or in production.

---

## 🏗 Option 1: Docker Compose Setup (Recommended)

Docker Compose sets up all services (PostgreSQL with `pgvector`, FastAPI backend, and Next.js frontend) with a single command.

### Prerequisites
1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. Run Ollama locally on your host machine (if running the LLM locally):
   - Ollama should be running and listening on port `11434`.
   - Pull the Qwen model: `ollama pull qwen2.5:7b` (or whichever version is configured).

### Build and Start Services
Run this command from the `railway-admin-ai` directory:
```bash
docker compose up --build
```

- **Frontend**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/docs
- **Database**: Port `5432` on `localhost`

---

## 💻 Option 2: Local Native Setup (Development)

If you prefer to run services manually for faster hot-reloading:

### 1. Database (PostgreSQL with PGVector)
1. Install PostgreSQL.
2. Install the [pgvector extension](https://github.com/ankane/pgvector).
3. Create a database named `railway_admin_db`.
4. Connect to database and run `CREATE EXTENSION vector;`.

### 2. Backend Setup
1. Open a terminal in `./backend`.
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set environment variables in a `.env` file in the `./backend` directory:
   ```env
   DATABASE_URL=postgresql+asyncpg://postgres:postgrespassword@localhost:5432/railway_admin_db
   SECRET_KEY=yoursecretkeyhere
   OLLAMA_HOST=http://localhost:11434
   ```
5. Apply migrations using the SQL file:
   - Import the schema from [`schema.sql`](./backend/schema.sql) using pgAdmin or psql:
     ```bash
     psql -U postgres -d railway_admin_db -f schema.sql
     ```
6. Start the backend:
   ```bash
   uvicorn app.main:app --reload
   ```

### 3. Frontend Setup
1. Open a terminal in `./frontend`.
2. Install dependencies:
   ```bash
   npm install
   ```
3. Create a `.env.local` file:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```
4. Start the Next.js development server:
   ```bash
   npm run dev
   ```

---

## 🚀 Production Deployment Checklist

When deploying to production (e.g., on AWS EC2, DigitalOcean, or Azure):

1. **Environment Variables**:
   - Change `SECRET_KEY` in the backend environment.
   - Update `DATABASE_URL` to point to a production-managed database (e.g., AWS RDS PostgreSQL).
   - Change `NEXT_PUBLIC_API_URL` to point to your backend's public domain name.
2. **Reverse Proxy / SSL**:
   - Use **Nginx** or **Caddy** to set up HTTPS certificates (Let's Encrypt) and route requests:
     - Route `/api/*` to the backend on port `8000`.
     - Route other traffic (`/*`) to the Next.js frontend on port `3000`.
3. **Database Backups**:
   - Ensure automatic backups are configured for the Postgres database volume (`pgdata`).

---

## 🆓 Option 3: Free Cloud Deployment (Zero Cost)

If you want to host RailVera on the internet without paying for servers, you can use a combination of generous free-tier cloud providers.

### 1. Database: Supabase or Neon (Free)
PostgreSQL with `pgvector` is required.
- **[Supabase](https://supabase.com/)**: Create a free project. It comes with `pgvector` pre-installed. Go to Database Settings to get your Connection String (`DATABASE_URL`).
- **Alternative**: [Neon.tech](https://neon.tech/) also offers a free Postgres tier with `pgvector` support.

### 2. Frontend: Vercel (Free)
Next.js is created by Vercel, making it the perfect free host.
- Push your code to a GitHub repository.
- Go to [Vercel](https://vercel.com/) and import your `frontend` folder.
- Set the Environment Variable: `NEXT_PUBLIC_API_URL` to point to your deployed backend URL.
- Vercel provides a free automatic SSL and a `.vercel.app` domain.

### 3. Backend: Render or Koyeb (Free)
Host the FastAPI backend.
- **[Render](https://render.com/)**: Create a "Web Service" connected to your GitHub repo. 
  - Set the Root Directory to `backend`.
  - Build Command: `pip install -r requirements.txt && apt-get update && apt-get install -y tesseract-ocr poppler-utils` (You may need to use their Docker environment option for system dependencies).
  - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port 10000`
- **Environment Variables**:
  - `DATABASE_URL` (from Supabase/Neon)
  - `SECRET_KEY`
  - `OLLAMA_HOST` (See note below)

### 🧠 Note on the LLM (Ollama)
Running Large Language Models (like Qwen 7B) requires significant RAM (usually 8GB+), which cloud providers **do not offer for free**. You have two options for a zero-cost setup:

1. **Local Tunneling (Hybrid Setup)**:
   - Run Ollama on your personal laptop/PC.
   - Use a free tool like [ngrok](https://ngrok.com/) or [Cloudflare Tunnels](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) to expose your local port `11434` to the internet securely.
   - Set the `OLLAMA_HOST` in your cloud backend (Render) to your ngrok URL.
2. **Switch to a Free API**:
   - Modify `backend/app/core/llm_client.py` to use a free-tier API provider instead of local Ollama (e.g., [Groq](https://groq.com/) or [Google Gemini API](https://ai.google.dev/)).
