import asyncio
import time
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test_speed(host):
    start = time.time()
    url = f"postgresql+asyncpg://postgres:1234@{host}:5432/railway_ai"
    eng = create_async_engine(url, connect_args={"timeout": 5})
    try:
        async with eng.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print(f"Host {host}: OK in {time.time() - start:.4f}s")
    except Exception as e:
        print(f"Host {host}: FAILED in {time.time() - start:.4f}s ({type(e).__name__})")
    finally:
        await eng.dispose()

async def main():
    await test_speed("localhost")
    await test_speed("127.0.0.1")

asyncio.run(main())
