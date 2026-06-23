import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test():
    eng = create_async_engine(
        "postgresql+asyncpg://postgres:1234@localhost:5432/railway_ai",
        connect_args={"timeout": 5}
    )
    try:
        async with eng.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("DB connection OK:", result.fetchone())
    except Exception as e:
        print("DB connection FAILED:", type(e).__name__, str(e))
    finally:
        await eng.dispose()

asyncio.run(test())
