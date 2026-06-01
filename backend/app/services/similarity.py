import math

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.gene import Gene
from app.models.variant import Variant, VariantEmbedding


def vector_to_storage(vector: list[float]) -> str:
    return ",".join(f"{value:.6f}" for value in vector)


def vector_from_storage(raw: str) -> list[float]:
    return [float(part) for part in raw.split(",") if part]


def embed_text(text: str) -> list[float]:
    lowered = text.lower()
    return [
        float(len(lowered) % 17),
        float(sum(1 for char in lowered if char in "aeiou") % 19),
        float(lowered.count("variant") + lowered.count("mutation")),
        float(lowered.count("pathogenic") + lowered.count("domain")),
    ]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right, strict=False))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def similar_variants(db: Session, variant_id: int, limit: int = 5) -> list[dict]:
    source_variant = db.get(Variant, variant_id)
    if not source_variant:
        return []
    source_vector = embed_text(source_variant.summary)
    rows = db.execute(select(Variant, Gene, VariantEmbedding).join(Gene).join(VariantEmbedding)).all()
    scored = []
    for variant, gene, embedding in rows:
        if variant.id == variant_id:
            continue
        score = cosine_similarity(source_vector, vector_from_storage(embedding.embedding))
        scored.append(
            {
                "variant_id": variant.id,
                "gene": gene.symbol,
                "hgvs": variant.hgvs,
                "significance": variant.significance,
                "condition": variant.condition,
                "similarity_score": round(score, 4),
            }
        )
    return sorted(scored, key=lambda row: row["similarity_score"], reverse=True)[:limit]
