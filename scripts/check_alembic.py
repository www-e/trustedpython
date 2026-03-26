"""Check and fix alembic version."""

import asyncio
from sqlalchemy import text
from app.db import engine


async def check_alembic():
    """Check alembic version."""
    async with engine.begin() as conn:
        try:
            result = await conn.execute(text("SELECT version_num FROM alembic_version"))
            versions = result.fetchall()
            print(f"Alembic versions: {versions}")
        except Exception as e:
            print(f"No alembic_version table: {e}")
            print("Creating alembic_version table with base version...")
            await conn.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
            await conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('44ec30f3a4a6')"))
            print("Base version set!")


if __name__ == "__main__":
    asyncio.run(check_alembic())
