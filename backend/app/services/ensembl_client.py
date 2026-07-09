from typing import Any
from urllib.parse import quote

import httpx


class EnsemblClientError(Exception):
    pass


def fetch_gene_payload(gene_symbol: str, base_url: str, timeout: float) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}/lookup/symbol/homo_sapiens/{gene_symbol}"
    response = httpx.get(
        url,
        params={"expand": "1", "content-type": "application/json"},
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise EnsemblClientError("Ensembl response was not a JSON object.")
    return payload


def fetch_vep_hgvs_payload(hgvs_notation: str, base_url: str, timeout: float) -> list[dict[str, Any]]:
    encoded_hgvs = quote(hgvs_notation, safe=":.")
    url = f"{base_url.rstrip('/')}/vep/human/hgvs/{encoded_hgvs}"
    response = httpx.get(
        url,
        params={
            "content-type": "application/json",
            "hgvs": "1",
            "canonical": "1",
            "mane": "1",
            "merged": "1",
            "pick": "1",
            "protein": "1",
            "variant_class": "1",
        },
        timeout=timeout,
        headers={"Content-Type": "application/json"},
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list) or not payload:
        raise EnsemblClientError("Ensembl VEP response did not include variant consequences.")
    return [item for item in payload if isinstance(item, dict)]
