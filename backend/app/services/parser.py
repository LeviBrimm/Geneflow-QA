import re
from dataclasses import dataclass


class VariantParseError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedVariant:
    gene: str
    notation: str
    variant_type: str
    is_valid: bool = True


GENE_PATTERN = r"(?P<gene>[A-Z0-9]{2,12})"
CDNA_PATTERN = r"c\.(?P<cpos>\d+(?:_\d+)?)(?P<change>dup[A-Z]+|del[A-Z]*|ins[A-Z]+|[ACGT]>[ACGT])"
PROTEIN_PATTERN = r"p\.(?P<protein>[A-Z][a-z]{2}\d+[A-Z][a-z]{2}|[A-Z]\d+[A-Z]|[A-Z]\d+\*)"
DELTA_PATTERN = r"(?P<delta>[ΔD]F508)"


def parse_variant(raw_input: str) -> ParsedVariant:
    if not isinstance(raw_input, str):
        raise VariantParseError("Variant input must be a string.")

    cleaned = " ".join(raw_input.strip().replace("∆", "Δ").split())
    if not cleaned:
        raise VariantParseError("Variant input is required.")

    match = re.fullmatch(fr"{GENE_PATTERN}\s+(?:{CDNA_PATTERN}|{PROTEIN_PATTERN}|{DELTA_PATTERN})", cleaned)
    if not match:
        raise VariantParseError("Unable to parse variant. Use examples like BRCA1 c.5266dupC or TP53 p.R175H.")

    gene = match.group("gene")
    notation = cleaned.split(" ", 1)[1]
    return ParsedVariant(gene=gene, notation=notation, variant_type=_classify_variant(notation))


def _classify_variant(notation: str) -> str:
    lower = notation.lower()
    if "dup" in lower:
        return "frameshift"
    if "del" in lower or notation.startswith("Δ"):
        return "deletion"
    if ">" in notation:
        return "substitution"
    if "*" in notation:
        return "nonsense"
    if notation.startswith("p."):
        return "missense"
    return "unknown"
