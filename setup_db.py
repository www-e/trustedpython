"""Quick script to set up the database properly."""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def setup_database():
    """Create missing tables and fix alembic version."""
    engine = create_async_engine(DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        # Check what tables exist
        result = await conn.execute(text("""
            SELECT tablename FROM pg_tables WHERE schemaname = 'public'
            ORDER BY tablename;
        """))
        tables = [row[0] for row in result.fetchall()]
        print(f"Existing tables: {tables}")

        # Create missing tables if needed
        if 'categories' not in tables:
            print("Creating categories table...")
            await conn.execute(text("CREATE TYPE game_type AS ENUM ('PUBG', 'FREE_FIRE', 'CALL_OF_DUTY', 'FORTNITE', 'MOBILE_LEGENDS', 'OTHER')"))
            await conn.execute(text("""
                CREATE TABLE categories (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) UNIQUE NOT NULL,
                    description TEXT,
                    icon_url VARCHAR(500),
                    is_active BOOLEAN DEFAULT TRUE NOT NULL,
                    sort_order INTEGER DEFAULT 0 NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
                )
            """))
            await conn.execute(text("CREATE INDEX ix_categories_name ON categories(name)"))
            print("✓ Categories table created")

        if 'listings' not in tables:
            print("Creating listings table...")
            await conn.execute(text("""
                CREATE TYPE listing_status AS ENUM ('DRAFT', 'PENDING', 'ACTIVE', 'SOLD', 'PAUSED', 'ARCHIVED');
                CREATE TABLE listings (
                    id SERIAL PRIMARY KEY,
                    seller_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
                    title VARCHAR(200) NOT NULL,
                    description TEXT NOT NULL,
                    game_type game_type NOT NULL,
                    level INTEGER,
                    rank VARCHAR(100),
                    server VARCHAR(100),
                    skins_count INTEGER,
                    characters_count INTEGER,
                    price NUMERIC(10, 2) NOT NULL,
                    status listing_status DEFAULT 'DRAFT' NOT NULL,
                    is_featured BOOLEAN DEFAULT FALSE NOT NULL,
                    views_count INTEGER DEFAULT 0 NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
                );
                CREATE INDEX ix_listings_seller_id ON listings(seller_id);
                CREATE INDEX ix_listings_category_id ON listings(category_id);
            """))
            print("✓ Listings table created")

        if 'listing_images' not in tables:
            print("Creating listing_images table...")
            await conn.execute(text("""
                CREATE TABLE listing_images (
                    id SERIAL PRIMARY KEY,
                    listing_id INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
                    image_url VARCHAR(500) NOT NULL,
                    caption VARCHAR(200),
                    sort_order INTEGER DEFAULT 0 NOT NULL,
                    is_primary BOOLEAN DEFAULT FALSE NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
                );
                CREATE INDEX ix_listing_images_listing_id ON listing_images(listing_id);
            """))
            print("✓ Listing images table created")

        # Now create our new tables
        if 'deal_status' not in [row[0] for row in await conn.execute(text("""
            SELECT typname FROM pg_type WHERE typname = 'deal_status'
        """)).fetchall()]:
            print("Creating deal_status enum...")
            await conn.execute(text("""
                CREATE TYPE deal_status AS ENUM ('pending', 'in_progress', 'awaiting_payment',
                'payment_verified', 'credentials_exchanged', 'completed', 'cancelled', 'disputed');
            """))
            print("✓ Deal status enum created")

        if 'deals' not in tables:
            print("Creating deals table...")
            await conn.execute(text("""
                CREATE TABLE deals (
                    id SERIAL PRIMARY KEY,
                    listing_id INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
                    buyer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    seller_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    mediator_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    status deal_status DEFAULT 'pending' NOT NULL,
                    price NUMERIC(10, 2) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
                );
                CREATE INDEX ix_deals_buyer_id ON deals(buyer_id);
                CREATE INDEX ix_deals_listing_id ON deals(listing_id);
                CREATE INDEX ix_deals_seller_id ON deals(seller_id);
                CREATE INDEX ix_deals_status ON deals(status);
            """))
            print("✓ Deals table created")

        if 'listing_mediators' not in tables:
            print("Creating listing_mediators table...")
            await conn.execute(text("""
                CREATE TABLE listing_mediators (
                    id SERIAL PRIMARY KEY,
                    listing_id INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
                    mediator_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    UNIQUE (listing_id, mediator_id)
                );
            """))
            print("✓ Listing mediators table created")

        # Add new columns to users table
        result = await conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'users' AND column_name = 'username'
        """))
        if not result.fetchone():
            print("Adding new columns to users table...")
            await conn.execute(text("""
                ALTER TABLE users ADD COLUMN username VARCHAR(50) UNIQUE;
                ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500);
                ALTER TABLE users ADD COLUMN bio TEXT;
                ALTER TABLE users ADD COLUMN rating NUMERIC(3, 2) DEFAULT 0.0 NOT NULL;
                ALTER TABLE users ADD COLUMN total_deals_as_buyer INTEGER DEFAULT 0 NOT NULL;
                ALTER TABLE users ADD COLUMN total_deals_as_seller INTEGER DEFAULT 0 NOT NULL;
                ALTER TABLE users ADD COLUMN completed_deals INTEGER DEFAULT 0 NOT NULL;
            """))
            print("✓ User columns added")

        # Update alembic version to our new migration
        print("Updating alembic version...")
        await conn.execute(text("""
            DELETE FROM alembic_version;
            INSERT INTO alembic_version (version_num) VALUES ('c3c3f104fb73');
        """))
        print("✓ Alembic version updated")

        # Verify
        result = await conn.execute(text("""
            SELECT tablename FROM pg_tables WHERE schemaname = 'public'
            ORDER BY tablename;
        """))
        tables = [row[0] for row in result.fetchall()]
        print(f"\n✓ Database setup complete!")
        print(f"  Tables: {', '.join(tables)}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(setup_database())
