import pytest

from app.services.parser import VariantParseError, parse_variant


@pytest.mark.parametrize(
    ("raw", "gene", "notation", "variant_type"),
    [
        ("BRCA1 c.5266dupC", "BRCA1", "c.5266dupC", "frameshift"),
        ("TP53 p.R175H", "TP53", "p.R175H", "missense"),
        ("CFTR ΔF508", "CFTR", "ΔF508", "deletion"),
        ("BRCA1 c.76A>G", "BRCA1", "c.76A>G", "substitution"),
        ("CFTR c.1521_1523delCTT", "CFTR", "c.1521_1523delCTT", "deletion"),
        ("TP53 p.R306*", "TP53", "p.R306*", "nonsense"),
    ],
)
def test_parse_supported_variants(raw, gene, notation, variant_type):
    parsed = parse_variant(raw)
    assert parsed.gene == gene
    assert parsed.notation == notation
    assert parsed.variant_type == variant_type
    assert parsed.is_valid is True


@pytest.mark.parametrize(
    ("raw", "expected_gene", "expected_notation"),
    [
        ("  BRCA1    c.5266dupC  ", "BRCA1", "c.5266dupC"),
        ("\tTP53\np.R175H", "TP53", "p.R175H"),
        ("CFTR ∆F508", "CFTR", "ΔF508"),
    ],
)
def test_parse_normalizes_supported_input(raw, expected_gene, expected_notation):
    parsed = parse_variant(raw)
    assert parsed.gene == expected_gene
    assert parsed.notation == expected_notation


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        "not a variant",
        "brca1 c.5266dupC",
        "BRCA1",
        "c.5266dupC",
        "BRCA1 5266dupC",
        "BRCA1 c.",
        "BRCA1 c.5266A>Z",
        "BRCA1 c.5266dup",
        "TP53 p.175H",
        "TP53 p.RH",
        "CFTR F508",
        "BRCA1 c.5266dupC extra",
    ],
)
def test_parse_rejects_invalid_or_unsupported_variants(raw):
    with pytest.raises(VariantParseError):
        parse_variant(raw)


def test_parse_rejects_non_string_input():
    with pytest.raises(VariantParseError, match="must be a string"):
        parse_variant(None)
