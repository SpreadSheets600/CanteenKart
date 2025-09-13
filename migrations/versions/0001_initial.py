"""Initial schema migration

Revision ID: 0001_initial
Revises: 
Create Date: 2025-09-13
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('user_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('phone', sa.Text, nullable=False, unique=True),
        sa.Column('name', sa.Text, nullable=False),
        sa.Column('role', sa.Text, nullable=False, server_default='student'),
        sa.Column('password_hash', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    op.create_table(
        'menu_items',
        sa.Column('item_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('name', sa.Text, nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('price', sa.Float, nullable=False, server_default='0.0'),
        sa.Column('stock_qty', sa.Integer, nullable=False, server_default='0'),
        sa.Column('is_available', sa.Integer, nullable=False, server_default='1'),
    )

    op.create_table(
        'orders',
        sa.Column('order_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer, nullable=False),
        sa.Column('status', sa.Text, nullable=False, server_default='pending'),
        sa.Column('pickup_slot', sa.DateTime),
        sa.Column('token_code', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id']),
    )

    op.create_table(
        'order_items',
        sa.Column('order_item_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('order_id', sa.Integer, nullable=False),
        sa.Column('item_id', sa.Integer, nullable=False),
        sa.Column('quantity', sa.Integer, nullable=False, server_default='1'),
        sa.Column('price', sa.Float, nullable=False, server_default='0.0'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.order_id']),
        sa.ForeignKeyConstraint(['item_id'], ['menu_items.item_id']),
    )

    op.create_table(
        'wallet',
        sa.Column('wallet_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer, nullable=False),
        sa.Column('balance', sa.Float, nullable=False, server_default='0.0'),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id']),
    )

    op.create_table(
        'transactions',
        sa.Column('txn_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer, nullable=False),
        sa.Column('amount', sa.Float, nullable=False),
        sa.Column('txn_type', sa.Text, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id']),
    )

    op.create_table(
        'sales_summary',
        sa.Column('summary_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('date', sa.Date, nullable=False),
        sa.Column('total_orders', sa.Integer, nullable=False, server_default='0'),
        sa.Column('total_revenue', sa.Float, nullable=False, server_default='0.0'),
        sa.Column('peak_hour', sa.Integer),
        sa.Column('top_item_id', sa.Integer),
        sa.ForeignKeyConstraint(['top_item_id'], ['menu_items.item_id']),
    )

    op.create_table(
        'item_performance',
        sa.Column('item_id', sa.Integer, primary_key=True),
        sa.Column('total_sold', sa.Integer, nullable=False, server_default='0'),
        sa.Column('total_revenue', sa.Float, nullable=False, server_default='0.0'),
        sa.Column('average_rating', sa.Float),
        sa.Column('last_sold_at', sa.DateTime),
        sa.ForeignKeyConstraint(['item_id'], ['menu_items.item_id']),
    )

    op.create_table(
        'feedback',
        sa.Column('feedback_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer, nullable=False),
        sa.Column('item_id', sa.Integer, nullable=False),
        sa.Column('rating', sa.Integer),
        sa.Column('comments', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id']),
        sa.ForeignKeyConstraint(['item_id'], ['menu_items.item_id']),
    )

    op.create_table(
        'user_activity',
        sa.Column('activity_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer, nullable=False),
        sa.Column('item_id', sa.Integer),
        sa.Column('action', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id']),
        sa.ForeignKeyConstraint(['item_id'], ['menu_items.item_id']),
    )


def downgrade():
    op.drop_table('user_activity')
    op.drop_table('feedback')
    op.drop_table('item_performance')
    op.drop_table('sales_summary')
    op.drop_table('transactions')
    op.drop_table('wallet')
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('menu_items')
    op.drop_table('users')
