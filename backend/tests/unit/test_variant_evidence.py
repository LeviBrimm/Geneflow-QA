from types import SimpleNamespace

from app.services.variant_evidence import (
    build_seeded_variant_evidence,
    build_variant_evidence,
    serialize_variant_evidence,
)


def test_build_seeded_variant_evidence_normalizes_curated_variant():
    query = SimpleNamespace(raw_input="BRCA1 c.5266dupC")
    variant = SimpleNamespace(
        gene=SimpleNamespace(symbol="BRCA1"),
        hgvs="c.5266dupC",
        rsid="rs80357906",
        variant_type="frameshift",
        significance="Pathogenic",
        condition="Hereditary breast and ovarian cancer syndrome",
        transcript_id="NM_007294.4",
        transcript_hgvs="NM_007294.4:c.5266dupC",
        protein_hgvs="NP_009225.1:p.Gln1756Profs",
    )

    evidence = build_seeded_variant_evidence(query, variant)

    assert len(evidence) == 1
    assert evidence[0].source == "seeded-variant-evidence"
    assert evidence[0].evidence_level == "seeded_internal_match"
    assert evidence[0].normalized_hgvs == "NM_007294.4:c.5266dupC"
    assert evidence[0].consequence_terms == ["frameshift_variant", "coding_sequence_variant"]
    assert evidence[0].impact == "HIGH"
    assert evidence[0].external_url == "https://www.ncbi.nlm.nih.gov/clinvar/?term=rs80357906"


def test_build_variant_evidence_uses_live_source_marker():
    query = SimpleNamespace(raw_input="BRAF c.1799T>A")
    variant = SimpleNamespace(
        gene=SimpleNamespace(symbol="BRAF"),
        hgvs="c.1799T>A",
        rsid="rs113488022",
        variant_type="missense",
        significance="uncertain_significance",
        condition="Not provided by Ensembl VEP",
        reference_source="ensembl_vep",
        transcript_id="ENST00000646891",
        transcript_hgvs="ENST00000646891.2:c.1799T>A",
        protein_hgvs="ENSP00000493543.1:p.Val600Glu",
    )

    evidence = build_variant_evidence(query, variant)

    assert evidence[0].source == "ensembl-vep"
    assert evidence[0].evidence_level == "live_external_match"
    assert evidence[0].normalized_hgvs == "ENST00000646891.2:c.1799T>A"
    assert evidence[0].consequence_terms == ["missense_variant"]


def test_serialize_variant_evidence_returns_api_shape():
    snapshot = SimpleNamespace(
        source="seeded-variant-evidence",
        lookup_status="success",
        evidence_level="seeded_internal_match",
        submitted_notation="TP53 p.R175H",
        normalized_hgvs="NM_000546.6:c.524G>A",
        rsid="rs28934578",
        transcript_id="NM_000546.6",
        consequence_terms='["missense_variant"]',
        impact="MODERATE",
        clinical_significance="Pathogenic",
        condition="Li-Fraumeni syndrome",
        review_status="curated educational seed",
        external_url="https://www.ncbi.nlm.nih.gov/clinvar/?term=rs28934578",
        error_message=None,
    )

    payload = serialize_variant_evidence([snapshot])

    assert payload == [
        {
            "source": "seeded-variant-evidence",
            "lookup_status": "success",
            "evidence_level": "seeded_internal_match",
            "submitted_notation": "TP53 p.R175H",
            "normalized_hgvs": "NM_000546.6:c.524G>A",
            "rsid": "rs28934578",
            "transcript_id": "NM_000546.6",
            "consequence_terms": ["missense_variant"],
            "impact": "MODERATE",
            "clinical_significance": "Pathogenic",
            "condition": "Li-Fraumeni syndrome",
            "review_status": "curated educational seed",
            "external_url": "https://www.ncbi.nlm.nih.gov/clinvar/?term=rs28934578",
            "error_message": None,
        }
    ]
