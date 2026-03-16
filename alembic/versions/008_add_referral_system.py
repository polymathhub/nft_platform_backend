from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '008_add_referral_system'
down_revision = '007_add_activity_logs_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'referrals',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('referrer_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('referred_user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True, unique=True),
        sa.Column('referral_code', sa.String(50), nullable=False, index=True),
        sa.Column('status', sa.String(50), nullable=False, index=True, server_default='active'),
        sa.Column('lifetime_earnings', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('referred_purchase_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('referred_purchase_amount', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), index=True),
        sa.Column('first_purchase_at', sa.DateTime(), nullable=True),
        sa.Column('locked_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['referrer_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['referred_user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_referrals_referrer_status', 'referrals', ['referrer_id', 'status'])
    op.create_index('ix_referrals_referred_user', 'referrals', ['referred_user_id'])
    op.create_index('ix_referrals_code_status', 'referrals', ['referral_code', 'status'])

    op.create_table(
        'referral_commissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('referral_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('commission_amount', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('commission_rate', sa.Float(), nullable=False, server_default='0.1'),
        sa.Column('transaction_amount', sa.Float(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, index=True, server_default='pending'),
        sa.Column('earned_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), index=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['referral_id'], ['referrals.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['transaction_id'], ['payments.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_referral_commissions_referral_status', 'referral_commissions', ['referral_id', 'status'])
    op.create_index('ix_referral_commissions_earned', 'referral_commissions', ['earned_at'])


def downgrade() -> None:
    op.drop_index('ix_referral_commissions_earned', 'referral_commissions')
    op.drop_index('ix_referral_commissions_referral_status', 'referral_commissions')
    op.drop_table('referral_commissions')
    op.drop_index('ix_referrals_code_status', 'referrals')
    op.drop_index('ix_referrals_referred_user', 'referrals')
    op.drop_index('ix_referrals_referrer_status', 'referrals')
    op.drop_table('referrals')
