from alembic import op
revision = '005_normalize_userrole_enum'
down_revision = '004_add_user_role'
branch_labels = None
depends_on = None
def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute(
        )
def downgrade() -> None:
    pass
