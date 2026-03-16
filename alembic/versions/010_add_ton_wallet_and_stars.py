from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '010_add_ton_wallet_and_stars'
down_revision = '009_add_notifications_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'ton_wallets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('wallet_address', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('tonconnect_session_id', sa.String(255), nullable=True, unique=True),
        sa.Column('status', sa.String(50), nullable=False, index=True, server_default='pending'),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('wallet_metadata', sa.JSON(), nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('connected_at', sa.DateTime(), nullable=True),
        sa.Column('disconnected_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_ton_wallets_user_status', 'ton_wallets', ['user_id', 'status'])
    op.create_index('ix_ton_wallets_address', 'ton_wallets', ['wallet_address'])

    op.create_table(
        'star_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('ton_wallet_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('telegram_payment_charge_id', sa.String(255), nullable=True, unique=True),
        sa.Column('provider_payment_charge_id', sa.String(255), nullable=True),
        sa.Column('amount_stars', sa.String(50), nullable=False),
        sa.Column('transaction_type', sa.String(50), nullable=False),
        sa.Column('related_nft_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('related_listing_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('related_order_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, index=True, server_default='pending'),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('tx_metadata', sa.JSON(), nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ton_wallet_id'], ['ton_wallets.id']),
        sa.ForeignKeyConstraint(['related_nft_id'], ['nfts.id']),
        sa.ForeignKeyConstraint(['related_listing_id'], ['listings.id']),
        sa.ForeignKeyConstraint(['related_order_id'], ['orders.id']),
    )
    op.create_index('ix_star_transactions_user_status', 'star_transactions', ['user_id', 'status'])
    op.create_index('ix_star_transactions_telegram_id', 'star_transactions', ['telegram_payment_charge_id'])
    op.create_index('ix_star_transactions_nft', 'star_transactions', ['related_nft_id'])


def downgrade() -> None:
    op.drop_index('ix_star_transactions_nft', 'star_transactions')
    op.drop_index('ix_star_transactions_telegram_id', 'star_transactions')
    op.drop_index('ix_star_transactions_user_status', 'star_transactions')
    op.drop_table('star_transactions')
    op.drop_index('ix_ton_wallets_address', 'ton_wallets')
    op.drop_index('ix_ton_wallets_user_status', 'ton_wallets')
    op.drop_table('ton_wallets')
