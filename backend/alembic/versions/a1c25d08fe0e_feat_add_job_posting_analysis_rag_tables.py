"""feat add job posting analysis rag tables

Revision ID: a1c25d08fe0e
Revises: 8da9a2719fcd
Create Date: 2026-05-11 21:49:13.933425
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'a1c25d08fe0e'
down_revision = '8da9a2719fcd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Compatibility shim.

    This revision was created before the concrete job-posting RAG tables were
    generated in later revisions. We keep it as an intentional no-op so that
    fresh environments and existing environments share the same linear history
    without applying unrelated schema mutations here.
    """
    return None


def downgrade() -> None:
    return None
