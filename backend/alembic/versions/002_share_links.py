"""Add share_links table for one-time share tokens"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002_share_links"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "share_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("jti", sa.String(64), nullable=False, unique=True),
        sa.Column("creator_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("document_ids_json", sa.Text, nullable=False),
        sa.Column("expires_at", sa.DateTime, nullable=False),
        sa.Column("used_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Index("ix_share_links_jti", "jti"),
        sa.Index("ix_share_links_creator_id", "creator_id"),
        sa.Index("ix_share_links_expires_at", "expires_at"),
        sa.Index("ix_share_links_used_at", "used_at"),
    )


def downgrade() -> None:
    op.drop_table("share_links")

