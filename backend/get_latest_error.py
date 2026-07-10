import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    url = "postgresql+asyncpg://postgres.zzwspcijmoeoxsdpciiv:Project%40100%251234@aws-1-ap-south-1.pooler.supabase.com:5432/postgres"
    engine = create_async_engine(url)
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT id, status, error_message, document_type FROM uploads ORDER BY created_at DESC LIMIT 1"))
        row = res.fetchone()
        if row:
            print("LATEST UPLOAD DETAILS:")
            print(f"ID: {row[0]}")
            print(f"Status: {row[1]}")
            print(f"Error Message: {row[2]}")
            print(f"Doc Type: {row[3]}")
        else:
            print("No uploads found.")

asyncio.run(main())
