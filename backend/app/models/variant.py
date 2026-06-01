from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Variant(Base):
    __tablename__ = "variants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    gene_id: Mapped[int] = mapped_column(ForeignKey("genes.id"), nullable=False)
    hgvs: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    rsid: Mapped[str | None] = mapped_column(String(64))
    variant_type: Mapped[str] = mapped_column(String(64), nullable=False)
    significance: Mapped[str] = mapped_column(String(128), nullable=False)
    condition: Mapped[str] = mapped_column(String(255), nullable=False)
    allele_frequency: Mapped[float | None] = mapped_column(Float)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int | None] = mapped_column(Integer)
    domain: Mapped[str | None] = mapped_column(String(128))

    gene = relationship("Gene", back_populates="variants")
    embeddings = relationship("VariantEmbedding", back_populates="variant")


class VariantQuery(Base):
    __tablename__ = "variant_queries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    variant_id: Mapped[int | None] = mapped_column(ForeignKey("variants.id"))
    raw_input: Mapped[str] = mapped_column(String(255), nullable=False)
    parsed_gene: Mapped[str] = mapped_column(String(32), nullable=False)
    parsed_variant: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="queries")
    variant = relationship("Variant")
    job = relationship("AnalysisJob", back_populates="query", uselist=False)
    explanation = relationship("Explanation", back_populates="query", uselist=False)


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    query_id: Mapped[int] = mapped_column(ForeignKey("variant_queries.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)

    query = relationship("VariantQuery", back_populates="job")


class Explanation(Base):
    __tablename__ = "explanations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    query_id: Mapped[int] = mapped_column(ForeignKey("variant_queries.id"), nullable=False)
    general_explanation: Mapped[str] = mapped_column(Text, nullable=False)
    technical_explanation: Mapped[str] = mapped_column(Text, nullable=False)
    model_used: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    query = relationship("VariantQuery", back_populates="explanation")


class VariantEmbedding(Base):
    __tablename__ = "variant_embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("variants.id"), nullable=False)
    embedding: Mapped[str] = mapped_column(Text, nullable=False)

    variant = relationship("Variant", back_populates="embeddings")
