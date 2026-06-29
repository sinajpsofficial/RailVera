from sentence_transformers import SentenceTransformer, CrossEncoder
from sqlalchemy.ext.asyncio import AsyncSession
from pgvector.sqlalchemy import Vector
from typing import List, Dict
import numpy as np
import logging

logger = logging.getLogger(__name__)

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
        logger.info("Initializing SentenceTransformer BAAI/bge-small-en-v1.5...")
        self.embedder = SentenceTransformer("BAAI/bge-small-en-v1.5")
        
        logger.info("Initializing CrossEncoder BAAI/bge-reranker-base...")
        try:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            device = "cpu"
            
        logger.info(f"CrossEncoder device set to: {device}")
        self.reranker = CrossEncoder("BAAI/bge-reranker-base", device=device)

    def _embed_text_sync(self, text: str) -> List[float]:
        return self.embedder.encode(text, normalize_embeddings=True).tolist()

    async def embed_text(self, text: str) -> List[float]:
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
            # Cooperatively yield control back to the event loop every few items
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
        from app.models.rule import Rule
        from sqlalchemy import select, text, bindparam

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

        # Step 2: Re-rank using bge-reranker CrossEncoder
        pairs = [[query, row.raw_text] for row in candidates]
        rerank_scores = await asyncio.to_thread(self.reranker.predict, pairs)

        # IMPORTANT: bge-reranker-base returns raw logits, NOT probabilities.
        # Convert to probability using sigmoid before applying any threshold.
        import math
        def sigmoid(x: float) -> float:
            return 1.0 / (1.0 + math.exp(-x))

        ranked = sorted(
            zip(candidates, [sigmoid(float(s)) for s in rerank_scores]),
            key=lambda x: x[1],
            reverse=True
        )

        # Step 3: Return top_k with metadata
        # Use a low threshold of 0.10 (post-sigmoid) to allow relevant rules through.
        # The vector similarity pre-filter already ensures candidates are related.
        results = [
            {
                "rule_id": row.rule_id,
                "rule_name": row.rule_name,
                "description": row.description,
                "relevance_score": round(prob, 4),
            }
            for row, prob in ranked[:top_k]
            if prob > 0.10  # Low post-sigmoid threshold; pre-filter handles relevance
        ]

        # Fallback: if reranker filtered everything, return top vector matches directly
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

