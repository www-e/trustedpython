"""Fix alembic and apply migrations properly."""

import asyncio
from sqlalchemy import text
from app.db import engine
from alembic import command
from alembic.config import Config
import os


async def fix_and_migrate():
    """Fix alembic version and apply migrations."""

    # First, fix the alembic version table
    async with engine.begin() as conn:
        try:
            result = await conn.execute(text("SELECT version_num FROM alembic_version"))
            versions = result.fetchall()
            print(f"Current alembic versions: {versions}")
        except Exception:
            print("Creating alembic_version table...")
            await conn.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
            await conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('44ec30f3a4a6')"))
            print("Base version set!")

    # Now apply migrations using alembic programmatically
    print("Applying migrations...")
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    print("Migrations applied successfully!")


if __name__ == "__main__":
    print("Fixing database schema and applying migrations...")
    asyncio.run(fix_and_migrate())
