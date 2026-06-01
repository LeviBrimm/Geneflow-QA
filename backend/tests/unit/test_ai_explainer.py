from app.services.ai_explainer import DISCLAIMER, build_prompt
from app.models.gene import Gene
from app.models.variant import Variant


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
