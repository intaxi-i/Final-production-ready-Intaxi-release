"""add city order comment

Revision ID: 0002_add_city_order_comment
Revises: 0001_init_v2_schema
Create Date: 2026-05-01
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_add_city_order_comment"
down_revision = "0001_init_v2_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("city_orders_v2", sa.Column("comment", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("city_orders_v2", "comment")
