import asyncio
import asyncpg
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

async def create_tables():
    # Resolve paths relative to migrations.py directory to prevent CWD errors
    current_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(current_dir, "..", "..", "schema.sql")
    
    # Read the connection string from env
    db_url = os.getenv("DATABASE_URL_SYNC")
    if not db_url:
        db_url = os.getenv("DATABASE_URL")
        if db_url and db_url.startswith("postgresql+asyncpg://"):
            db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    if not db_url:
        print("Error: DATABASE_URL or DATABASE_URL_SYNC not set in environment.")
        return
        
    print(f"Connecting to database server (host: {db_url.split('@')[-1]})...")
    
    try:
        conn = await asyncpg.connect(db_url)
        print("Connection established successfully.")
        
        print(f"Reading schema from: {schema_path}")
        with open(schema_path, "r", encoding="utf-8") as f:
            sql = f.read()
            
        print("Executing schema.sql DDL script...")
        await conn.execute(sql)
        await conn.close()
        print("All tables and vector indexes created successfully.")
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    asyncio.run(create_tables())
