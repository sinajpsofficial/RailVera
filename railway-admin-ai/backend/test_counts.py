import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, func
from app.models.rule import Rule

async def test():
    url = "postgresql+asyncpg://postgres:1234@localhost:5432/railway_ai"
    eng = create_async_engine(url)
    AsyncSessionLocal = async_sessionmaker(bind=eng, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as db:
        total_res = await db.execute(select(func.count()).select_from(Rule))
        total = total_res.scalar_one()
        
        embedded_res = await db.execute(
            select(func.count()).select_from(Rule).where(Rule.embedding.isnot(None))
        )
        embedded = embedded_res.scalar_one()
        print(f"Total: {total}, Embedded: {embedded}")
        
    await eng.dispose()

asyncio.run(test())
