from markupsafe import escape

from app.models.variant import VariantQuery
from app.services.ai_explainer import DISCLAIMER


def generate_html_report(query: VariantQuery, similar: list[dict]) -> str:
    variant = query.variant
    gene = variant.gene if variant else None
    explanation = query.explanation
    external_reference = query.external_reference
    variant_evidence_items = "".join(
        f"<li>{escape(item.normalized_hgvs or 'Unknown HGVS')} - {escape(item.impact or 'Unknown impact')} "
        f"({escape(item.clinical_significance or 'No clinical significance')})</li>"
        for item in query.variant_evidence_snapshots
    )
    similar_items = "".join(
        f"<li>{escape(item['gene'])} {escape(item['hgvs'])} - score {item['similarity_score']}</li>" for item in similar
    )
    external_url = external_reference.external_url if external_reference else None
    external_link = (
        f'<p><strong>External URL:</strong> <a href="{escape(external_url)}">{escape(external_url)}</a></p>'
        if external_url
        else ""
    )
    external_source = _field(external_reference.source if external_reference else None, "pending")
    external_status = _field(external_reference.lookup_status if external_reference else None, "pending")
    external_id = _field(external_reference.external_id if external_reference else None)
    external_biotype = _field(external_reference.gene_biotype if external_reference else None)
    external_location = _field(external_reference.location if external_reference else None)
    external_summary = _field(
        external_reference.summary if external_reference else None,
        "External reference enrichment is pending.",
    )
    return f"""<!doctype html>
<html>
<head><meta charset="utf-8"><title>GeneFlow Report #{query.id}</title></head>
<body>
  <h1>GeneFlow Variant Report</h1>
  <p><strong>Variant:</strong> {escape(query.raw_input)}</p>
  <p><strong>Status:</strong> {escape(query.status)}</p>
  <p><strong>Gene:</strong> {escape(gene.symbol if gene else query.parsed_gene)}</p>
  <p><strong>Reference:</strong> {escape(variant.summary if variant else "No reference match available.")}</p>
  <h2>External Reference</h2>
  <p><strong>Source:</strong> {escape(external_source)}</p>
  <p><strong>Lookup status:</strong> {escape(external_status)}</p>
  <p><strong>External ID:</strong> {escape(external_id)}</p>
  <p><strong>Biotype:</strong> {escape(external_biotype)}</p>
  <p><strong>Location:</strong> {escape(external_location)}</p>
  <p>{escape(external_summary)}</p>
  {external_link}
  <h2>Variant Evidence</h2>
  <ul>{variant_evidence_items or "<li>Variant-level evidence is pending.</li>"}</ul>
  <h2>General Explanation</h2>
  <p>{escape(explanation.general_explanation if explanation else "Pending")}</p>
  <h2>Technical Explanation</h2>
  <p>{escape(explanation.technical_explanation if explanation else "Pending")}</p>
  <h2>Similar Variants</h2>
  <ul>{similar_items or "<li>No similar variants available.</li>"}</ul>
  <footer><p>{escape(DISCLAIMER)}</p></footer>
</body>
</html>"""


def _field(value: str | None, fallback: str = "Unavailable") -> str:
    return value if value else fallback
