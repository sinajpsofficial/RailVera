from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Optional
from pydantic import BaseModel

from app.database.connection import get_db
from app.core.rag_pipeline import RAGPipeline
from app.core.prompt_builder import PromptBuilder
from app.core.llm_client import LLMClient

router = APIRouter()

# Shared instances (lazy loaded)
rag_pipeline = None
prompt_builder = PromptBuilder()
llm_client = LLMClient()

def get_rag_pipeline() -> RAGPipeline:
    global rag_pipeline
    if rag_pipeline is None:
        rag_pipeline = RAGPipeline()
    return rag_pipeline

class ChatQueryRequest(BaseModel):
    query: str
    extracted_facts: Optional[Dict] = {}
    missing_documents: Optional[List[str]] = []
    conversation_history: Optional[List[Dict]] = []

@router.get("/")
async def chat_root():
    return {"message": "Chat endpoint is active."}

@router.post("/query")
async def chat_query(
    request: ChatQueryRequest,
    db: AsyncSession = Depends(get_db),
    pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    1. Retrieve relevant rules from DB using the semantic search pipeline.
    2. Format the retrieved rules, facts, missing docs, and history into a strict context prompt.
    3. Generate the response using Qwen3 (via local Ollama) or fallback programmatically.
    """
    query_text = request.query.strip()
    if not query_text:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        # Step 1: Retrieve rules matching the query semantically
        rules = await pipeline.retrieve(query_text, db, top_k=5)

        # Step 2: Build prompt
        prompt = prompt_builder.build(
            question=query_text,
            retrieved_rules=rules,
            extracted_facts=request.extracted_facts,
            missing_documents=request.missing_documents,
            conversation_history=request.conversation_history
        )

        # Step 3: Run LLM generation
        response = await llm_client.generate(
            prompt=prompt,
            retrieved_rules=rules,
            extracted_facts=request.extracted_facts,
            missing_documents=request.missing_documents
        )

        return {
            "response": response,
            "retrieved_rules": rules,
            "prompt_length": len(prompt)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate response: {str(e)}")
