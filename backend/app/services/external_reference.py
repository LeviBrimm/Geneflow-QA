import json
from dataclasses import dataclass
from typing import Any

import httpx

from app.config.settings import get_settings
from app.models.gene import Gene
from app.models.variant import ExternalReferenceSnapshot, Variant, VariantQuery


class ExternalReferenceError(Exception):
    pass


@dataclass(frozen=True)
class ExternalReferenceResult:
    source: str
    lookup_status: str
    external_id: str | None = None
    external_url: str | None = None
    gene_biotype: str | None = None
    location: str | None = None
    summary: str | None = None
    raw_payload: dict[str, Any] | None = None
    error_message: str | None = None


ENSEMBL_GENE_IDS = {
    "BRCA1": "ENSG00000012048",
    "TP53": "ENSG00000141510",
    "CFTR": "ENSG00000001626",
}


def fetch_external_reference(gene: Gene, variant: Variant) -> ExternalReferenceResult:
    settings = get_settings()
    mode = settings.external_reference_mode.lower()

    if mode == "disabled":
        return ExternalReferenceResult(source="none", lookup_status="disabled")
    if mode == "mock":
        return _mock_reference(gene, variant)
    if mode != "live":
        return ExternalReferenceResult(
            source="ensembl",
            lookup_status="failed",
            error_message=f"Unsupported external reference mode: {settings.external_reference_mode}",
        )

    try:
        return _fetch_ensembl_reference(
            gene.symbol,
            base_url=settings.external_reference_base_url,
            timeout=settings.external_reference_timeout_seconds,
        )
    except Exception as exc:  # noqa: BLE001 - external dependency failures must not fail analysis.
        return ExternalReferenceResult(source="ensembl", lookup_status="failed", error_message=str(exc))


def save_external_reference_snapshot(query: VariantQuery, result: ExternalReferenceResult) -> ExternalReferenceSnapshot:
    snapshot = ExternalReferenceSnapshot(
        query_id=query.id,
        source=result.source,
        lookup_status=result.lookup_status,
        external_id=result.external_id,
        external_url=result.external_url,
        gene_biotype=result.gene_biotype,
        location=result.location,
        summary=result.summary,
        raw_payload=_serialize_payload(result.raw_payload),
        error_message=result.error_message,
    )
    return snapshot


def _fetch_ensembl_reference(gene_symbol: str, base_url: str, timeout: float) -> ExternalReferenceResult:
    url = f"{base_url.rstrip('/')}/lookup/symbol/homo_sapiens/{gene_symbol}"
    response = httpx.get(
        url,
        params={"expand": "1", "content-type": "application/json"},
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ExternalReferenceError("Ensembl response was not a JSON object.")

    external_id = _string_or_none(payload.get("id"))
    return ExternalReferenceResult(
        source="ensembl",
        lookup_status="success",
        external_id=external_id,
        external_url=_ensembl_gene_url(external_id),
        gene_biotype=_string_or_none(payload.get("biotype")),
        location=_format_location(payload),
        summary=_string_or_none(payload.get("description")),
        raw_payload=_compact_payload(payload),
    )


def _mock_reference(gene: Gene, variant: Variant) -> ExternalReferenceResult:
    external_id = ENSEMBL_GENE_IDS.get(gene.symbol)
    return ExternalReferenceResult(
        source="ensembl-mock",
        lookup_status="success",
        external_id=external_id or f"MOCK-{gene.symbol}",
        external_url=_ensembl_gene_url(external_id),
        gene_biotype="protein_coding",
        location=f"{gene.symbol}:{variant.position or 'unknown'}",
        summary=f"Mock Ensembl enrichment for {gene.symbol}; switch EXTERNAL_REFERENCE_MODE=live for public API data.",
        raw_payload={"gene": gene.symbol, "variant": variant.hgvs, "mode": "mock"},
    )


def _format_location(payload: dict[str, Any]) -> str | None:
    seq_region = payload.get("seq_region_name")
    start = payload.get("start")
    end = payload.get("end")
    if seq_region and start and end:
        return f"{seq_region}:{start}-{end}"
    return None


def _compact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": payload.get("id"),
        "display_name": payload.get("display_name"),
        "description": payload.get("description"),
        "biotype": payload.get("biotype"),
        "seq_region_name": payload.get("seq_region_name"),
        "start": payload.get("start"),
        "end": payload.get("end"),
    }


def _serialize_payload(payload: dict[str, Any] | None) -> str | None:
    if payload is None:
        return None
    return json.dumps(payload, sort_keys=True)


def _ensembl_gene_url(external_id: str | None) -> str | None:
    if not external_id:
        return None
    return f"https://www.ensembl.org/Homo_sapiens/Gene/Summary?g={external_id}"


def _string_or_none(value: Any) -> str | None:
    return value if isinstance(value, str) else None
