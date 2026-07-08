"""unique variant reference

Revision ID: 20260611_0005
Revises: 20260610_0004
Create Date: 2026-06-11 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260611_0005"
down_revision: str | None = "20260610_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("uq_variants_gene_id_hgvs", "variants", ["gene_id", "hgvs"], unique=True)


def downgrade() -> None:
    op.drop_index("uq_variants_gene_id_hgvs", table_name="variants")
