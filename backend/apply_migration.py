import asyncio
import os
import sys

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine
from sqlalchemy import text

async def apply_migration():
    migration_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "supabase", "migrations", "009_vision_detections.sql"
    )
    
    print(f"Reading migration file: {migration_path}")
    with open(migration_path, "r") as f:
        sql_content = f.read()

    # Split by semicolon or run the whole block
    print("Applying migration queries to Supabase database...")
    async with engine.begin() as conn:
        # Run individual statements to avoid issues with some drivers
        statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]
        for stmt in statements:
            if stmt:
                print(f"Executing: {stmt[:60]}...")
                await conn.execute(text(stmt))
    print("SUCCESS! Database migration 009 applied successfully.")

if __name__ == "__main__":
    asyncio.run(apply_migration())
