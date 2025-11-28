"""Add total_amount and created_at to Order

Revision ID: 9a886d445394
Revises: 
Create Date: 2025-08-26 22:12:01.531665
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers
revision = '9a886d445394'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # only add created_at (since total_amount already exists)
    op.add_column('order',
        sa.Column('created_at', sa.DateTime(), nullable=True)
    )

    conn = op.get_bind()
    from datetime import datetime
    conn.execute(
        sa.text("UPDATE `order` SET created_at = :now"),
        {"now": datetime.utcnow()}
    )

    with op.batch_alter_table("order") as batch_op:
        batch_op.alter_column("created_at", nullable=False)



def downgrade():
    op.drop_column('order', 'created_at')
    op.drop_column('order', 'total_amount')
