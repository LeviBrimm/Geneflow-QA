import pytest

from app.services.parser import VariantParseError, parse_variant


@pytest.mark.parametrize(
    ("raw", "gene", "notation", "variant_type"),
    [
        ("BRCA1 c.5266dupC", "BRCA1", "c.5266dupC", "frameshift"),
        ("TP53 p.R175H", "TP53", "p.R175H", "missense"),
        ("CFTR ΔF508", "CFTR", "ΔF508", "deletion"),
    ],
)
def test_parse_supported_variants(raw, gene, notation, variant_type):
    parsed = parse_variant(raw)
    assert parsed.gene == gene
    assert parsed.notation == notation
    assert parsed.variant_type == variant_type
    assert parsed.is_valid is True


def test_parse_rejects_invalid_variant():
    with pytest.raises(VariantParseError):
        parse_variant("not a variant")
