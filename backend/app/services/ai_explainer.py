from dataclasses import dataclass
from collections.abc import Sequence

from app.models.gene import Gene
from app.models.variant import Variant
from app.services.variant_evidence import VariantEvidenceResult


DISCLAIMER = "Educational only. Not medical advice. Consult a licensed medical professional for health decisions."


@dataclass(frozen=True)
class ExplanationResult:
    general_explanation: str
    technical_explanation: str
    model_used: str


def build_prompt(
    gene: Gene,
    variant: Variant,
    evidence_results: Sequence[VariantEvidenceResult] | None = None,
) -> str:
    evidence = _primary_evidence(evidence_results)
    evidence_text = _evidence_prompt_text(evidence)
    return (
        "Explain this public genomic variant for an educational software demo. "
        "Avoid medical advice. "
        f"Gene: {gene.symbol} ({gene.full_name}). "
        f"Variant: {variant.hgvs}. Type: {variant.variant_type}. "
        f"Significance: {variant.significance}. Condition: {variant.condition}. "
        f"Summary: {variant.summary}"
        f"{evidence_text}"
    )


def generate_explanation(
    gene: Gene,
    variant: Variant,
    ai_mode: str = "mock",
    evidence_results: Sequence[VariantEvidenceResult] | None = None,
) -> ExplanationResult:
    # Mock mode is deterministic for tests, demos, and development without API keys.
    evidence = _primary_evidence(evidence_results)
    source = _source_label(evidence.source if evidence else variant.reference_source)
    consequence_terms = _terms_text(evidence.consequence_terms if evidence else None)
    impact = evidence.impact if evidence and evidence.impact else "not available"
    normalized_hgvs = evidence.normalized_hgvs if evidence and evidence.normalized_hgvs else variant.hgvs
    transcript_id = evidence.transcript_id if evidence and evidence.transcript_id else variant.transcript_id
    external_url = evidence.external_url if evidence and evidence.external_url else "not available"
    general = (
        f"{gene.symbol} {variant.hgvs} is resolved from {source} evidence as "
        f"{variant.significance.lower()} and associated with {variant.condition}. "
        f"{variant.summary} {DISCLAIMER}"
    )
    technical = (
        f"Parsed as a {variant.variant_type} variant in {gene.symbol}. "
        f"Evidence source: {source}. Normalized HGVS: {normalized_hgvs}. "
        f"Consequence terms: {consequence_terms}. Impact: {impact}. "
        f"Transcript ID: {transcript_id or 'not available'}. "
        f"Transcript HGVS: {variant.transcript_hgvs or 'not available'}. "
        f"Protein HGVS: {variant.protein_hgvs or 'not available'}. "
        f"The annotation links rsID {variant.rsid or 'not available'} "
        f"with allele frequency {variant.allele_frequency if variant.allele_frequency is not None else 'not available'}. "
        f"External evidence URL: {external_url}. Reference note: {variant.summary} {DISCLAIMER}"
    )
    return ExplanationResult(general, technical, f"{ai_mode}-explainer-v1")


def _primary_evidence(evidence_results: Sequence[VariantEvidenceResult] | None) -> VariantEvidenceResult | None:
    if not evidence_results:
        return None
    for evidence in evidence_results:
        if evidence.lookup_status == "success":
            return evidence
    return evidence_results[0]


def _evidence_prompt_text(evidence: VariantEvidenceResult | None) -> str:
    if not evidence:
        return ""
    return (
        f" Evidence source: {_source_label(evidence.source)}. "
        f"Evidence level: {evidence.evidence_level}. "
        f"Normalized HGVS: {evidence.normalized_hgvs or 'not available'}. "
        f"Consequence terms: {_terms_text(evidence.consequence_terms)}. "
        f"Impact: {evidence.impact or 'not available'}. "
        f"External URL: {evidence.external_url or 'not available'}."
    )


def _source_label(source: str | None) -> str:
    if source == "ensembl_vep" or source == "ensembl-vep":
        return "Ensembl VEP"
    if source == "seeded" or source == "seeded-variant-evidence":
        return "seeded demo"
    return source or "reference"


def _terms_text(terms: list[str] | None) -> str:
    if not terms:
        return "not available"
    return ", ".join(terms)
