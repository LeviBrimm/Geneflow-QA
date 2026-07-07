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
    reference_source: Mapped[str] = mapped_column(String(64), default="seeded", nullable=False)
    transcript_id: Mapped[str | None] = mapped_column(String(128))
    transcript_hgvs: Mapped[str | None] = mapped_column(String(255))
    protein_hgvs: Mapped[str | None] = mapped_column(String(255))

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
    external_reference = relationship("ExternalReferenceSnapshot", back_populates="query", uselist=False)
    variant_evidence_snapshots = relationship("VariantEvidenceSnapshot", back_populates="query")


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    query_id: Mapped[int] = mapped_column(ForeignKey("variant_queries.id"), nullable=False, unique=True)
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


class ExternalReferenceSnapshot(Base):
    __tablename__ = "external_reference_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    query_id: Mapped[int] = mapped_column(ForeignKey("variant_queries.id"), nullable=False, unique=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    lookup_status: Mapped[str] = mapped_column(String(32), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(128))
    external_url: Mapped[str | None] = mapped_column(String(512))
    gene_biotype: Mapped[str | None] = mapped_column(String(128))
    location: Mapped[str | None] = mapped_column(String(128))
    summary: Mapped[str | None] = mapped_column(Text)
    raw_payload: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    query = relationship("VariantQuery", back_populates="external_reference")


class VariantEvidenceSnapshot(Base):
    __tablename__ = "variant_evidence_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    query_id: Mapped[int] = mapped_column(ForeignKey("variant_queries.id"), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    lookup_status: Mapped[str] = mapped_column(String(32), nullable=False)
    evidence_level: Mapped[str] = mapped_column(String(64), nullable=False)
    submitted_notation: Mapped[str | None] = mapped_column(String(255))
    normalized_hgvs: Mapped[str | None] = mapped_column(String(255))
    rsid: Mapped[str | None] = mapped_column(String(64))
    transcript_id: Mapped[str | None] = mapped_column(String(128))
    consequence_terms: Mapped[str | None] = mapped_column(Text)
    impact: Mapped[str | None] = mapped_column(String(64))
    clinical_significance: Mapped[str | None] = mapped_column(String(128))
    condition: Mapped[str | None] = mapped_column(String(255))
    review_status: Mapped[str | None] = mapped_column(String(128))
    external_url: Mapped[str | None] = mapped_column(String(512))
    raw_payload: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    query = relationship("VariantQuery", back_populates="variant_evidence_snapshots")
