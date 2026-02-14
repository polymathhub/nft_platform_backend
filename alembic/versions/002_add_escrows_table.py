"""add escrows table

Revision ID: 002_add_escrows_table
Revises: 001_add_collection_rarity
Create Date: 2026-02-13 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_escrows_table'
down_revision = '001_add_collection_rarity'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'escrows',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('listing_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('offer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('buyer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('seller_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column('currency', sa.String(length=32), nullable=False),
        sa.Column('commission_amount', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('tx_hash', sa.String(length=256), nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )


def downgrade():
    op.drop_table('escrows')
