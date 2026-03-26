"""Fix alembic and apply migrations - fixed with proper transaction handling."""

import asyncio
from sqlalchemy import text
from app.db import engine
from alembic import command
from alembic.config import Config


async def fix_alembic():
    """Fix alembic version table separately."""

    async with engine.connect() as conn:
        # Disable autocommit/autocommit to handle transaction manually
        await conn.execute(text("SET TRANSACTION READ WRITE"))

        try:
            result = await conn.execute(text("SELECT version_num FROM alembic_version"))
            versions = result.fetchall()
            print(f"Current alembic versions: {versions}")
        except Exception as e:
            if "alembic_version" in str(e):
                print("Creating alembic_version table...")
                # In new transaction
                async with engine.begin() as trans:
                    await trans.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
                    await trans.execute(text("INSERT INTO alembic_version (version_num) VALUES ('44ec30f3a4a6')"))
                print("Base version set!")
            else:
                raise


async def apply_migrations():
    """Apply alembic migrations."""
    print("Applying migrations...")
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    print("Migrations applied!")


async def verify_migration():
    """Verify is_popular column exists."""
    async for db in get_db():
        result = await db.execute(
            text("SELECT column_name FROM information_schema.columns WHERE table_name = 'categories' AND column_name = 'is_popular'")
        )
        has_is_popular = result.rowcount > 0
        print(f"is_popular column exists: {has_is_popular}")
        return has_is_popular


async def main():
    """Run all migration steps."""
    await fix_alembic()
    await apply_migrations()

    # Verify
    has_is_popular = await verify_migration()
    if has_is_popular:
        print("SUCCESS! Database schema is up to date.")
    else:
        print("WARNING: is_popular column still missing!")


if __name__ == "__main__":
    print("Fixing database schema...")
    asyncio.run(main())
