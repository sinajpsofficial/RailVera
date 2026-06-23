import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.rag_pipeline import RAGPipeline

async def test():
    url = "postgresql+asyncpg://postgres:1234@localhost:5432/railway_ai"
    eng = create_async_engine(url)
    AsyncSessionLocal = async_sessionmaker(bind=eng, class_=AsyncSession, expire_on_commit=False)
    
    query = "Evaluate promotion eligibility for Goods Driver Rajesh Kumar to Senior Driver grade. Employee has completed 8 years of service."
    print("Initializing RAGPipeline...")
    rag = RAGPipeline()
    
    async with AsyncSessionLocal() as db:
        print("Running retrieve query...")
        # Let's bypass the score filter to see what is returned
        query_embedding = await rag.embed_text(query)
        from pgvector.sqlalchemy import Vector
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
        
        print(f"Found {len(candidates)} candidates in vector search.")
        if candidates:
            pairs = [[query, row.raw_text] for row in candidates]
            import torch
            rerank_scores = rag.reranker.predict(pairs)
            
            print("\nReranker scores:")
            for row, score in zip(candidates, rerank_scores):
                print(f" - Rule {row.rule_id}: similarity={row.similarity:.4f}, rerank_score={score:.4f}")
                
    await eng.dispose()

asyncio.run(test())
