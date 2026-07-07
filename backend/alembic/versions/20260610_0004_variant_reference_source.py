"""variant reference source

Revision ID: 20260610_0004
Revises: 20260609_0003
Create Date: 2026-06-10 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260610_0004"
down_revision: str | None = "20260609_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "variants",
        sa.Column("reference_source", sa.String(length=64), nullable=False, server_default="seeded"),
    )
    op.execute(
        "update variants set reference_source = 'ensembl_vep' " "where summary like 'Live Ensembl VEP annotation%'"
    )


def downgrade() -> None:
    op.drop_column("variants", "reference_source")
