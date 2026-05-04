"""init v2 schema

Revision ID: 0001_init_v2_schema
Revises:
Create Date: 2026-04-30
"""
from __future__ import annotations

from alembic import op

revision = "0001_init_v2_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.core.database import Base
    from app import models  # noqa: F401

    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    from app.core.database import Base
    from app import models  # noqa: F401

    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
