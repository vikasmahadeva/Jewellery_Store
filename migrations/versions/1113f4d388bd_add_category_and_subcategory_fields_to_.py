"""Add category and subcategory fields to Product

Revision ID: 1113f4d388bd
Revises: 9a886d445394
Create Date: 2025-09-07 10:25:41.821336
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1113f4d388bd'
down_revision = '9a886d445394'
branch_labels = None
depends_on = None


def upgrade():
    # Modify 'order' table
    with op.batch_alter_table('order', schema=None) as batch_op:
        batch_op.alter_column('status',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.String(length=20),
               nullable=False)
        # Remove product_id and quantity columns without trying to drop constraint
        batch_op.drop_column('product_id')
        batch_op.drop_column('quantity')

    # Modify 'product' table
    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.add_column(sa.Column('category', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('subcategory', sa.String(length=50), nullable=True))
        batch_op.alter_column('name',
               existing_type=sa.VARCHAR(length=200),
               type_=sa.String(length=120),
               existing_nullable=False)
        batch_op.alter_column('stock',
               existing_type=sa.INTEGER(),
               nullable=True)
        batch_op.alter_column('image',
               existing_type=sa.VARCHAR(length=300),
               type_=sa.String(length=255),
               existing_nullable=True)


def downgrade():
    # Revert 'product' table changes
    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.alter_column('image',
               existing_type=sa.String(length=255),
               type_=sa.VARCHAR(length=300),
               existing_nullable=True)
        batch_op.alter_column('stock',
               existing_type=sa.INTEGER(),
               nullable=False)
        batch_op.alter_column('name',
               existing_type=sa.String(length=120),
               type_=sa.VARCHAR(length=200),
               existing_nullable=False)
        batch_op.drop_column('subcategory')
        batch_op.drop_column('category')

    # Revert 'order' table changes
    with op.batch_alter_table('order', schema=None) as batch_op:
        batch_op.add_column(sa.Column('quantity', sa.INTEGER(), nullable=False))
        batch_op.add_column(sa.Column('product_id', sa.INTEGER(), nullable=False))
        batch_op.create_foreign_key(None, 'product', ['product_id'], ['id'])
        batch_op.alter_column('status',
               existing_type=sa.String(length=20),
               type_=sa.VARCHAR(length=50),
               nullable=True)
