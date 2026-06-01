from dataclasses import dataclass

from app.models.gene import Gene
from app.models.variant import Variant


DISCLAIMER = "Educational only. Not medical advice. Consult a licensed medical professional for health decisions."


@dataclass(frozen=True)
class ExplanationResult:
    general_explanation: str
    technical_explanation: str
    model_used: str


def build_prompt(gene: Gene, variant: Variant) -> str:
    return (
        "Explain this public genomic variant for an educational software demo. "
        "Avoid medical advice. "
        f"Gene: {gene.symbol} ({gene.full_name}). "
        f"Variant: {variant.hgvs}. Type: {variant.variant_type}. "
        f"Significance: {variant.significance}. Condition: {variant.condition}. "
        f"Summary: {variant.summary}"
    )


def generate_explanation(gene: Gene, variant: Variant, ai_mode: str = "mock") -> ExplanationResult:
    # Mock mode is deterministic for tests, demos, and development without API keys.
    general = (
        f"{gene.symbol} {variant.hgvs} is listed in this demo reference set as "
        f"{variant.significance.lower()} and associated with {variant.condition}. "
        f"{variant.summary} {DISCLAIMER}"
    )
    technical = (
        f"Parsed as a {variant.variant_type} variant in {gene.symbol}. "
        f"The local annotation record links rsID {variant.rsid or 'not available'} "
        f"with allele frequency {variant.allele_frequency if variant.allele_frequency is not None else 'not available'}. "
        f"Reference note: {variant.summary} {DISCLAIMER}"
    )
    return ExplanationResult(general, technical, f"{ai_mode}-explainer-v1")
