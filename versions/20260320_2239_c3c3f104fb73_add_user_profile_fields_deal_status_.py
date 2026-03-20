"""Add user profile fields, deal status, pending listing status, and deal/listing_mediator tables

Revision ID: c3c3f104fb73
Revises: fe4b4f265d94
Create Date: 2026-03-20 22:39:19.019042

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c3c3f104fb73'
down_revision: Union[str, None] = 'fe4b4f265d94'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""

    # Get database connection
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Get existing columns in users table
    existing_user_columns = [col['name'] for col in inspector.get_columns('users')]

    # Add new columns to users table (only if they don't exist)
    if 'username' not in existing_user_columns:
        op.add_column('users', sa.Column('username', sa.String(50), nullable=True))
        op.create_unique_constraint('uq_users_username', 'users', ['username'])

    if 'avatar_url' not in existing_user_columns:
        op.add_column('users', sa.Column('avatar_url', sa.String(500), nullable=True))

    if 'bio' not in existing_user_columns:
        op.add_column('users', sa.Column('bio', sa.Text(), nullable=True))

    if 'rating' not in existing_user_columns:
        op.add_column('users', sa.Column('rating', sa.Numeric(3, 2), nullable=False, server_default='0.0'))

    if 'total_deals_as_buyer' not in existing_user_columns:
        op.add_column('users', sa.Column('total_deals_as_buyer', sa.Integer(), nullable=False, server_default='0'))

    if 'total_deals_as_seller' not in existing_user_columns:
        op.add_column('users', sa.Column('total_deals_as_seller', sa.Integer(), nullable=False, server_default='0'))

    if 'completed_deals' not in existing_user_columns:
        op.add_column('users', sa.Column('completed_deals', sa.Integer(), nullable=False, server_default='0'))

    # Update listing_status enum to add 'pending' (if not already exists)
    # We need to be careful here - PostgreSQL doesn't support removing enum values easily
    # So we'll just try to add it and ignore if it exists
    try:
        op.execute("ALTER TYPE listing_status ADD VALUE 'pending'")
    except Exception:
        pass  # Value already exists

    # Create deal_status enum
    try:
        deal_status_enum = postgresql.ENUM(
            'pending',
            'in_progress',
            'awaiting_payment',
            'payment_verified',
            'credentials_exchanged',
            'completed',
            'cancelled',
            'disputed',
            name='deal_status',
            create_type=True,
            metadata=sa.MetaData()
        )
        deal_status_enum.create(op.get_bind(), checkfirst=True)
    except Exception:
        pass  # Already exists

    # Create deals table (without listing_id foreign key constraint if listings table doesn't exist)
    if not inspector.has_table('deals'):
        if inspector.has_table('listings'):
            # Normal case: listings table exists, create with all constraints
            op.create_table(
                'deals',
                sa.Column('id', sa.Integer(), nullable=False),
                sa.Column('listing_id', sa.Integer(), nullable=False),
                sa.Column('buyer_id', sa.Integer(), nullable=False),
                sa.Column('seller_id', sa.Integer(), nullable=False),
                sa.Column('mediator_id', sa.Integer(), nullable=True),
                sa.Column('status', deal_status_enum, nullable=False, server_default='pending'),
                sa.Column('price', sa.Numeric(10, 2), nullable=False),
                sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
                sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
                sa.ForeignKeyConstraint(['buyer_id'], ['users.id'], ondelete='CASCADE'),
                sa.ForeignKeyConstraint(['listing_id'], ['listings.id'], ondelete='CASCADE'),
                sa.ForeignKeyConstraint(['mediator_id'], ['users.id'], ondelete='SET NULL'),
                sa.ForeignKeyConstraint(['seller_id'], ['users.id'], ondelete='CASCADE'),
                sa.PrimaryKeyConstraint('id')
            )
        else:
            # Fallback: create without listing_id foreign key constraint
            op.create_table(
                'deals',
                sa.Column('id', sa.Integer(), nullable=False),
                sa.Column('listing_id', sa.Integer(), nullable=False),
                sa.Column('buyer_id', sa.Integer(), nullable=False),
                sa.Column('seller_id', sa.Integer(), nullable=False),
                sa.Column('mediator_id', sa.Integer(), nullable=True),
                sa.Column('status', deal_status_enum, nullable=False, server_default='pending'),
                sa.Column('price', sa.Numeric(10, 2), nullable=False),
                sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
                sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
                sa.ForeignKeyConstraint(['buyer_id'], ['users.id'], ondelete='CASCADE'),
                sa.ForeignKeyConstraint(['mediator_id'], ['users.id'], ondelete='SET NULL'),
                sa.ForeignKeyConstraint(['seller_id'], ['users.id'], ondelete='CASCADE'),
                sa.PrimaryKeyConstraint('id')
            )
        op.create_index(op.f('ix_deals_buyer_id'), 'deals', ['buyer_id'], unique=False)
        op.create_index(op.f('ix_deals_listing_id'), 'deals', ['listing_id'], unique=False)
        op.create_index(op.f('ix_deals_seller_id'), 'deals', ['seller_id'], unique=False)
        op.create_index(op.f('ix_deals_status'), 'deals', ['status'], unique=False)

    # Create listing_mediators table
    if not inspector.has_table('listing_mediators'):
        op.create_table(
            'listing_mediators',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('listing_id', sa.Integer(), nullable=False),
            sa.Column('mediator_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
            sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
            sa.ForeignKeyConstraint(['listing_id'], ['listings.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['mediator_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('listing_id', 'mediator_id', name='unique_listing_mediator')
        )


def downgrade() -> None:
    """Downgrade database schema."""

    # Get database connection
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Drop listing_mediators table
    if inspector.has_table('listing_mediators'):
        op.drop_table('listing_mediators')

    # Drop deals table
    if inspector.has_table('deals'):
        op.drop_index(op.f('ix_deals_status'), table_name='deals')
        op.drop_index(op.f('ix_deals_seller_id'), table_name='deals')
        op.drop_index(op.f('ix_deals_buyer_id'), table_name='deals')
        op.drop_index(op.f('ix_deals_listing_id'), table_name='deals')
        op.drop_table('deals')

    # Drop deal_status enum
    try:
        postgresql.ENUM(name='deal_status').drop(op.get_bind())
    except Exception:
        pass  # Doesn't exist

    # Remove 'pending' from listing_status (not directly supported, would need manual intervention)
    # For now, we'll leave it in the enum

    # Get existing columns in users table
    existing_user_columns = [col['name'] for col in inspector.get_columns('users')]

    # Drop unique constraint on username
    if 'username' in existing_user_columns:
        try:
            op.drop_constraint('uq_users_username', 'users', type_='unique')
        except Exception:
            pass  # Doesn't exist

    # Remove columns from users table (only if they exist)
    for col in ['completed_deals', 'total_deals_as_seller', 'total_deals_as_buyer', 'rating', 'bio', 'avatar_url', 'username']:
        if col in existing_user_columns:
            try:
                op.drop_column('users', col)
            except Exception:
                pass  # Already removed or doesn't exist
