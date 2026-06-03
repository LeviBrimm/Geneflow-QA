"""initial schema

Revision ID: 20260603_0001
Revises:
Create Date: 2026-06-03 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260603_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "genes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_genes_id"), "genes", ["id"], unique=False)
    op.create_index(op.f("ix_genes_symbol"), "genes", ["symbol"], unique=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    op.create_table(
        "variants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("gene_id", sa.Integer(), nullable=False),
        sa.Column("hgvs", sa.String(length=128), nullable=False),
        sa.Column("rsid", sa.String(length=64), nullable=True),
        sa.Column("variant_type", sa.String(length=64), nullable=False),
        sa.Column("significance", sa.String(length=128), nullable=False),
        sa.Column("condition", sa.String(length=255), nullable=False),
        sa.Column("allele_frequency", sa.Float(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column("domain", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(["gene_id"], ["genes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_variants_hgvs"), "variants", ["hgvs"], unique=False)
    op.create_index(op.f("ix_variants_id"), "variants", ["id"], unique=False)

    op.create_table(
        "variant_queries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("variant_id", sa.Integer(), nullable=True),
        sa.Column("raw_input", sa.String(length=255), nullable=False),
        sa.Column("parsed_gene", sa.String(length=32), nullable=False),
        sa.Column("parsed_variant", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["variant_id"], ["variants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_variant_queries_id"), "variant_queries", ["id"], unique=False)

    op.create_table(
        "analysis_jobs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("query_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["query_id"], ["variant_queries.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_analysis_jobs_id"), "analysis_jobs", ["id"], unique=False)

    op.create_table(
        "explanations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("query_id", sa.Integer(), nullable=False),
        sa.Column("general_explanation", sa.Text(), nullable=False),
        sa.Column("technical_explanation", sa.Text(), nullable=False),
        sa.Column("model_used", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["query_id"], ["variant_queries.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_explanations_id"), "explanations", ["id"], unique=False)

    op.create_table(
        "variant_embeddings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("variant_id", sa.Integer(), nullable=False),
        sa.Column("embedding", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["variant_id"], ["variants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_variant_embeddings_id"), "variant_embeddings", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_variant_embeddings_id"), table_name="variant_embeddings")
    op.drop_table("variant_embeddings")
    op.drop_index(op.f("ix_explanations_id"), table_name="explanations")
    op.drop_table("explanations")
    op.drop_index(op.f("ix_analysis_jobs_id"), table_name="analysis_jobs")
    op.drop_table("analysis_jobs")
    op.drop_index(op.f("ix_variant_queries_id"), table_name="variant_queries")
    op.drop_table("variant_queries")
    op.drop_index(op.f("ix_variants_id"), table_name="variants")
    op.drop_index(op.f("ix_variants_hgvs"), table_name="variants")
    op.drop_table("variants")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_genes_symbol"), table_name="genes")
    op.drop_index(op.f("ix_genes_id"), table_name="genes")
    op.drop_table("genes")
