from dataclasses import replace

from app.models.gene import Gene
from app.models.variant import Variant
from app.services.ai_explainer import DISCLAIMER, build_prompt, generate_explanation
from app.services.variant_evidence import VariantEvidenceResult


def test_prompt_includes_guardrail_language():
    gene = Gene(symbol="TP53", full_name="Tumor protein p53", description="test")
    variant = Variant(
        gene_id=1,
        hgvs="p.R175H",
        variant_type="missense",
        significance="Pathogenic",
        condition="Li-Fraumeni syndrome",
        summary="Reference summary",
    )
    prompt = build_prompt(gene, variant)
    assert "Avoid medical advice" in prompt
    assert "TP53" in prompt
    assert DISCLAIMER.startswith("Educational only")


def test_prompt_includes_variant_evidence_context():
    gene = Gene(symbol="BRAF", full_name="B-Raf proto-oncogene", description="test")
    variant = _variant()
    evidence = _evidence()

    prompt = build_prompt(gene, variant, evidence_results=[evidence])

    assert "Evidence source: Ensembl VEP" in prompt
    assert "Consequence terms: missense_variant" in prompt
    assert "Impact: MODERATE" in prompt


def test_mock_explanation_is_grounded_in_variant_evidence():
    gene = Gene(symbol="BRAF", full_name="B-Raf proto-oncogene", description="test")
    variant = _variant()
    evidence = _evidence()

    result = generate_explanation(gene, variant, evidence_results=[evidence])

    assert "resolved from Ensembl VEP evidence" in result.general_explanation
    assert "Normalized HGVS: ENST00000646891.2:c.1799T>A" in result.technical_explanation
    assert "Consequence terms: missense_variant" in result.technical_explanation
    assert "Impact: MODERATE" in result.technical_explanation
    assert "Transcript ID: ENST00000646891" in result.technical_explanation


def test_mock_explanation_falls_back_to_variant_data_without_evidence():
    gene = Gene(symbol="BRAF", full_name="B-Raf proto-oncogene", description="test")
    variant = _variant()
    variant.reference_source = "curated-reference"

    result = generate_explanation(gene, variant)

    assert "resolved from curated-reference evidence" in result.general_explanation
    assert "Consequence terms: not available" in result.technical_explanation


def test_prompt_uses_first_evidence_when_no_lookup_succeeded():
    gene = Gene(symbol="BRAF", full_name="B-Raf proto-oncogene", description="test")
    variant = _variant()
    evidence = replace(_evidence(), lookup_status="failed")

    prompt = build_prompt(gene, variant, evidence_results=[evidence])

    assert "Evidence source: Ensembl VEP" in prompt
    assert "Evidence level: live_external_match" in prompt


def _variant() -> Variant:
    return Variant(
        gene_id=1,
        hgvs="p.V600E",
        rsid="rs113488022",
        variant_type="missense",
        significance="pathogenic",
        condition="Not provided by Ensembl VEP",
        summary="Live Ensembl VEP annotation for BRAF p.V600E.",
        allele_frequency=0.0001,
        reference_source="ensembl_vep",
        transcript_id="ENST00000646891",
        transcript_hgvs="ENST00000646891.2:c.1799T>A",
        protein_hgvs="ENSP00000493543.1:p.Val600Glu",
    )


def _evidence() -> VariantEvidenceResult:
    return VariantEvidenceResult(
        source="ensembl-vep",
        lookup_status="success",
        evidence_level="live_external_match",
        submitted_notation="BRAF p.V600E",
        normalized_hgvs="ENST00000646891.2:c.1799T>A",
        rsid="rs113488022",
        transcript_id="ENST00000646891",
        consequence_terms=["missense_variant"],
        impact="MODERATE",
        clinical_significance="pathogenic",
        condition="Not provided by Ensembl VEP",
        external_url="https://www.ensembl.org/Homo_sapiens/Tools/VEP?hgvs=BRAF:p.V600E",
    )
