from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, documents, cases, chat, eligibility, rules, reports
import os

app = FastAPI(title="Railway Admin AI", version="3.0")

# Setup CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create folders for reports and uploads if not present locally
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

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "3.0"}
