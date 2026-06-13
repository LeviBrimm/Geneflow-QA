"""variant evidence snapshots

Revision ID: 20260609_0003
Revises: 20260608_0002
Create Date: 2026-06-09 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260609_0003"
down_revision: str | None = "20260608_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("variants", sa.Column("transcript_id", sa.String(length=128), nullable=True))
    op.add_column("variants", sa.Column("transcript_hgvs", sa.String(length=255), nullable=True))
    op.add_column("variants", sa.Column("protein_hgvs", sa.String(length=255), nullable=True))
    op.create_table(
        "variant_evidence_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("query_id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("lookup_status", sa.String(length=32), nullable=False),
        sa.Column("evidence_level", sa.String(length=64), nullable=False),
        sa.Column("submitted_notation", sa.String(length=255), nullable=True),
        sa.Column("normalized_hgvs", sa.String(length=255), nullable=True),
        sa.Column("rsid", sa.String(length=64), nullable=True),
        sa.Column("transcript_id", sa.String(length=128), nullable=True),
        sa.Column("consequence_terms", sa.Text(), nullable=True),
        sa.Column("impact", sa.String(length=64), nullable=True),
        sa.Column("clinical_significance", sa.String(length=128), nullable=True),
        sa.Column("condition", sa.String(length=255), nullable=True),
        sa.Column("review_status", sa.String(length=128), nullable=True),
        sa.Column("external_url", sa.String(length=512), nullable=True),
        sa.Column("raw_payload", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["query_id"], ["variant_queries.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_variant_evidence_snapshots_id"),
        "variant_evidence_snapshots",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_variant_evidence_snapshots_id"), table_name="variant_evidence_snapshots")
    op.drop_table("variant_evidence_snapshots")
    op.drop_column("variants", "protein_hgvs")
    op.drop_column("variants", "transcript_hgvs")
    op.drop_column("variants", "transcript_id")
