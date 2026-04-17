"""expand document file metadata

Revision ID: 20260417_000002
Revises: 20260417_000001
Create Date: 2026-04-17 14:20:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260417_000002"
down_revision = "20260417_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "document",
        sa.Column("original_file_name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "document",
        sa.Column("stored_file_name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "document",
        sa.Column("file_ext", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "document",
        sa.Column("mime_type", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "document",
        sa.Column("file_size", sa.BigInteger(), nullable=True),
    )

    op.execute("UPDATE document SET original_file_name = title WHERE original_file_name IS NULL")
    op.execute("UPDATE document SET stored_file_name = title WHERE stored_file_name IS NULL")

    op.alter_column("document", "original_file_name", nullable=False)
    op.alter_column("document", "stored_file_name", nullable=False)


def downgrade() -> None:
    op.drop_column("document", "file_size")
    op.drop_column("document", "mime_type")
    op.drop_column("document", "file_ext")
    op.drop_column("document", "stored_file_name")
    op.drop_column("document", "original_file_name")
