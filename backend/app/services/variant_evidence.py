import json
from dataclasses import dataclass
from typing import Any

from app.models.variant import Variant, VariantEvidenceSnapshot, VariantQuery


@dataclass(frozen=True)
class VariantEvidenceResult:
    source: str
    lookup_status: str
    evidence_level: str
    submitted_notation: str | None = None
    normalized_hgvs: str | None = None
    rsid: str | None = None
    transcript_id: str | None = None
    consequence_terms: list[str] | None = None
    impact: str | None = None
    clinical_significance: str | None = None
    condition: str | None = None
    review_status: str | None = None
    external_url: str | None = None
    raw_payload: dict[str, Any] | None = None
    error_message: str | None = None


CONSEQUENCE_BY_TYPE = {
    "deletion": ["inframe_deletion", "protein_altering_variant"],
    "frameshift": ["frameshift_variant", "coding_sequence_variant"],
    "missense": ["missense_variant"],
}

IMPACT_BY_TYPE = {
    "deletion": "MODERATE",
    "frameshift": "HIGH",
    "missense": "MODERATE",
}


def build_seeded_variant_evidence(query: VariantQuery, variant: Variant) -> list[VariantEvidenceResult]:
    normalized_hgvs = variant.transcript_hgvs or f"{variant.gene.symbol} {variant.hgvs}"
    terms = CONSEQUENCE_BY_TYPE.get(variant.variant_type, ["sequence_variant"])
    impact = IMPACT_BY_TYPE.get(variant.variant_type, "MODIFIER")
    payload = {
        "gene": variant.gene.symbol,
        "variant": variant.hgvs,
        "transcript_hgvs": variant.transcript_hgvs,
        "protein_hgvs": variant.protein_hgvs,
        "rsid": variant.rsid,
        "evidence_source": "seeded_reference",
    }

    return [
        VariantEvidenceResult(
            source="seeded-variant-evidence",
            lookup_status="success",
            evidence_level="seeded_internal_match",
            submitted_notation=query.raw_input,
            normalized_hgvs=normalized_hgvs,
            rsid=variant.rsid,
            transcript_id=variant.transcript_id,
            consequence_terms=terms,
            impact=impact,
            clinical_significance=variant.significance,
            condition=variant.condition,
            review_status="curated educational seed",
            external_url=_clinvar_url(variant.rsid),
            raw_payload=payload,
        )
    ]


def save_variant_evidence_snapshots(
    query: VariantQuery, evidence_results: list[VariantEvidenceResult]
) -> list[VariantEvidenceSnapshot]:
    return [
        VariantEvidenceSnapshot(
            query_id=query.id,
            source=result.source,
            lookup_status=result.lookup_status,
            evidence_level=result.evidence_level,
            submitted_notation=result.submitted_notation,
            normalized_hgvs=result.normalized_hgvs,
            rsid=result.rsid,
            transcript_id=result.transcript_id,
            consequence_terms=_serialize_terms(result.consequence_terms),
            impact=result.impact,
            clinical_significance=result.clinical_significance,
            condition=result.condition,
            review_status=result.review_status,
            external_url=result.external_url,
            raw_payload=_serialize_payload(result.raw_payload),
            error_message=result.error_message,
        )
        for result in evidence_results
    ]


def serialize_variant_evidence(snapshots: list[VariantEvidenceSnapshot]) -> list[dict]:
    return [
        {
            "source": snapshot.source,
            "lookup_status": snapshot.lookup_status,
            "evidence_level": snapshot.evidence_level,
            "submitted_notation": snapshot.submitted_notation,
            "normalized_hgvs": snapshot.normalized_hgvs,
            "rsid": snapshot.rsid,
            "transcript_id": snapshot.transcript_id,
            "consequence_terms": _deserialize_terms(snapshot.consequence_terms),
            "impact": snapshot.impact,
            "clinical_significance": snapshot.clinical_significance,
            "condition": snapshot.condition,
            "review_status": snapshot.review_status,
            "external_url": snapshot.external_url,
            "error_message": snapshot.error_message,
        }
        for snapshot in snapshots
    ]


def _clinvar_url(rsid: str | None) -> str | None:
    if not rsid:
        return None
    return f"https://www.ncbi.nlm.nih.gov/clinvar/?term={rsid}"


def _serialize_terms(terms: list[str] | None) -> str | None:
    if terms is None:
        return None
    return json.dumps(terms, sort_keys=True)


def _deserialize_terms(raw_terms: str | None) -> list[str]:
    if not raw_terms:
        return []
    parsed = json.loads(raw_terms)
    return parsed if isinstance(parsed, list) else []


def _serialize_payload(payload: dict[str, Any] | None) -> str | None:
    if payload is None:
        return None
    return json.dumps(payload, sort_keys=True)
