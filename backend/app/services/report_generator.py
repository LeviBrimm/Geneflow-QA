from markupsafe import escape

from app.models.variant import VariantQuery
from app.services.ai_explainer import DISCLAIMER


def generate_html_report(query: VariantQuery, similar: list[dict]) -> str:
    variant = query.variant
    gene = variant.gene if variant else None
    explanation = query.explanation
    similar_items = "".join(
        f"<li>{escape(item['gene'])} {escape(item['hgvs'])} - score {item['similarity_score']}</li>"
        for item in similar
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
  <h2>General Explanation</h2>
  <p>{escape(explanation.general_explanation if explanation else "Pending")}</p>
  <h2>Technical Explanation</h2>
  <p>{escape(explanation.technical_explanation if explanation else "Pending")}</p>
  <h2>Similar Variants</h2>
  <ul>{similar_items or "<li>No similar variants available.</li>"}</ul>
  <footer><p>{escape(DISCLAIMER)}</p></footer>
</body>
</html>"""
