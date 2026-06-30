from sqlalchemy.ext.asyncio import AsyncSession
from pgvector.sqlalchemy import Vector
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class RAGPipeline:
    """
    Retrieves the most relevant rules from the database for any query.
    
    Optimized for memory-constrained environments (like Render Free tier, 512MB RAM):
    - Uses Google Gemini Embedding API (text-embedding-004) if enabled (zero RAM overhead).
    - Lazy-loads local PyTorch/SentenceTransformers only if running locally on Ollama.
    - Bypasses local CrossEncoder reranking when using Gemini to save ~1GB of RAM.
    """

    def __init__(self):
        from app.config import settings
        self.use_gemini = (settings.LLM_PROVIDER.lower() == "gemini") and bool(settings.GEMINI_API_KEY)
        
        self.embedder = None
        self.reranker = None
        
        if not self.use_gemini:
            # Load local models only if Ollama is selected (requires >1.5GB RAM)
            logger.info("Initializing Local SentenceTransformer BAAI/bge-small-en-v1.5...")
            from sentence_transformers import SentenceTransformer, CrossEncoder
            self.embedder = SentenceTransformer("BAAI/bge-small-en-v1.5")
            
            logger.info("Initializing Local CrossEncoder BAAI/bge-reranker-base...")
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                device = "cpu"
                
            logger.info(f"CrossEncoder device set to: {device}")
            self.reranker = CrossEncoder("BAAI/bge-reranker-base", device=device)
        else:
            logger.info("RAGPipeline initialized with Gemini Cloud Embeddings (zero local RAM footprint).")

    async def _embed_text_gemini(self, text: str) -> List[float]:
        """Gets 384-dimensional embeddings via Google Gemini Embedding API."""
        import httpx
        from app.config import settings
        
        url = "https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent"
        params = {"key": settings.GEMINI_API_KEY}
        body = {
            "content": {
                "parts": [{"text": text}]
            },
            "outputDimensionality": 384
        }
        
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(url, params=params, json=body)
            response.raise_for_status()
            data = response.json()
            return data["embedding"]["values"]

    def _embed_text_sync(self, text: str) -> List[float]:
        if not self.embedder:
            raise RuntimeError("Local embedder is not initialized.")
        return self.embedder.encode(text, normalize_embeddings=True).tolist()

    async def embed_text(self, text: str) -> List[float]:
        if self.use_gemini:
            return await self._embed_text_gemini(text)
            
        import asyncio
        return await asyncio.to_thread(self._embed_text_sync, text)

    async def embed_all_rules(self, db: AsyncSession) -> int:
        """
        Run this ONCE after ingesting rules.md to create embeddings.
        Stores the embedding vector in the rules.embedding column.
        """
        from app.models.rule import Rule
        from sqlalchemy import select
        import asyncio

        result = await db.execute(select(Rule))
        rules = result.scalars().all()

        embedded_count = 0
        for rule in rules:
            text = f"{rule.rule_name}. {rule.description}"
            rule.embedding = await self.embed_text(text)
            embedded_count += 1
            if embedded_count % 5 == 0:
                await asyncio.sleep(0.01)

        await db.commit()
        logger.info(f"Embedded {embedded_count} rules successfully.")
        return embedded_count

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
        import asyncio
        query_embedding = await self.embed_text(query)

        # Step 1: Vector similarity search (top 20)
        from sqlalchemy import text, bindparam

        sql = text("""
            SELECT rule_id, rule_name, description, raw_text,
                   1 - (embedding <=> :embedding) AS similarity
            FROM rules
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> :embedding
            LIMIT 20
        """).bindparams(bindparam("embedding", type_=Vector(384)))
        result = await db.execute(sql, {"embedding": query_embedding})
        candidates = result.fetchall()

        if not candidates:
            return []

        # Step 2: Reranking
        if self.use_gemini or not self.reranker:
            # In Gemini Cloud mode, bypass CrossEncoder to stay within 512MB RAM.
            # Postgres cosine similarity rankings are already highly accurate.
            results = [
                {
                    "rule_id": row.rule_id,
                    "rule_name": row.rule_name,
                    "description": row.description,
                    "relevance_score": round(float(row.similarity), 4),
                }
                for row in candidates[:top_k]
            ]
            return results

        # Local mode: Re-rank using bge-reranker CrossEncoder
        pairs = [[query, row.raw_text] for row in candidates]
        rerank_scores = await asyncio.to_thread(self.reranker.predict, pairs)

        import math
        def sigmoid(x: float) -> float:
            return 1.0 / (1.0 + math.exp(-x))

        ranked = sorted(
            zip(candidates, [sigmoid(float(s)) for s in rerank_scores]),
            key=lambda x: x[1],
            reverse=True
        )

        # Step 3: Return top_k with metadata
        results = [
            {
                "rule_id": row.rule_id,
                "rule_name": row.rule_name,
                "description": row.description,
                "relevance_score": round(prob, 4),
            }
            for row, prob in ranked[:top_k]
            if prob > 0.10
        ]

        if not results and candidates:
            logger.warning(
                "[RAG] Reranker filtered all candidates. Falling back to top vector matches."
            )
            results = [
                {
                    "rule_id": row.rule_id,
                    "rule_name": row.rule_name,
                    "description": row.description,
                    "relevance_score": round(float(sim), 4),
                }
                for row, sim in zip(candidates[:top_k], [float(r) for _, r in ranked[:top_k]])
            ]

        return results
