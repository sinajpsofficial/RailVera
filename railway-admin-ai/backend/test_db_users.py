import asyncio
import time
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text, select
from app.models.user import User

async def test():
    print("Creating engine...")
    url = "postgresql+asyncpg://postgres:1234@localhost:5432/railway_ai"
    eng = create_async_engine(url)
    AsyncSessionLocal = async_sessionmaker(bind=eng, class_=AsyncSession, expire_on_commit=False)
    
    print("Connecting and executing select...")
    start = time.time()
    try:
        async with AsyncSessionLocal() as session:
            stmt = select(User)
            res = await session.execute(stmt)
            users = res.scalars().all()
            print(f"Success! Found {len(users)} users in {time.time() - start:.4f}s")
            for u in users:
                print(f" - {u.email} ({u.name})")
    except Exception as e:
        print("Error executing select:", type(e).__name__, str(e))
    finally:
        await eng.dispose()

asyncio.run(test())
