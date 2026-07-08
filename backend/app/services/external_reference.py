import json
from dataclasses import dataclass
from typing import Any

from app.config.settings import get_settings
from app.models.gene import Gene
from app.models.variant import ExternalReferenceSnapshot, Variant, VariantQuery
from app.services.ensembl_client import EnsemblClientError, fetch_gene_payload, fetch_vep_hgvs_payload
from app.services.ensembl_mapper import (
    EnsemblGeneReference,
    EnsemblMappingError,
    EnsemblVariantReference,
    ensembl_hgvs_notation,
    map_gene_reference,
    map_variant_reference,
)


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
    gene_reference = _fetch_ensembl_gene_reference(gene_symbol, base_url, timeout)
    return ExternalReferenceResult(
        source="ensembl",
        lookup_status="success",
        external_id=gene_reference.external_id,
        external_url=gene_reference.external_url,
        gene_biotype=gene_reference.gene_biotype,
        location=gene_reference.location,
        summary=gene_reference.summary,
        raw_payload=gene_reference.raw_payload,
    )


def fetch_ensembl_variant_reference(
    gene_symbol: str,
    notation: str,
    variant_type: str,
    base_url: str,
    timeout: float,
) -> EnsemblVariantReference:
    gene_reference = _fetch_ensembl_gene_reference(gene_symbol, base_url, timeout)
    hgvs_notation = ensembl_hgvs_notation(gene_symbol, notation)
    vep_payload = _fetch_ensembl_vep_hgvs(hgvs_notation, base_url, timeout)
    try:
        return map_variant_reference(gene_symbol, notation, variant_type, gene_reference, vep_payload)
    except EnsemblMappingError as exc:
        raise ExternalReferenceError(str(exc)) from exc


def _fetch_ensembl_gene_reference(gene_symbol: str, base_url: str, timeout: float) -> EnsemblGeneReference:
    try:
        return map_gene_reference(fetch_gene_payload(gene_symbol, base_url, timeout))
    except (EnsemblClientError, EnsemblMappingError) as exc:
        raise ExternalReferenceError(str(exc)) from exc


def _fetch_ensembl_vep_hgvs(hgvs_notation: str, base_url: str, timeout: float) -> list[dict[str, Any]]:
    try:
        return fetch_vep_hgvs_payload(hgvs_notation, base_url, timeout)
    except EnsemblClientError as exc:
        raise ExternalReferenceError(str(exc)) from exc


def _mock_reference(gene: Gene, variant: Variant) -> ExternalReferenceResult:
    external_id = ENSEMBL_GENE_IDS.get(gene.symbol)
    return ExternalReferenceResult(
        source="ensembl-mock",
        lookup_status="success",
        external_id=external_id or f"MOCK-{gene.symbol}",
        external_url=_mock_ensembl_gene_url(external_id),
        gene_biotype="protein_coding",
        location=f"{gene.symbol}:{variant.position or 'unknown'}",
        summary=f"Mock Ensembl enrichment for {gene.symbol}; switch EXTERNAL_REFERENCE_MODE=live for public API data.",
        raw_payload={"gene": gene.symbol, "variant": variant.hgvs, "mode": "mock"},
    )


def _serialize_payload(payload: dict[str, Any] | None) -> str | None:
    if payload is None:
        return None
    return json.dumps(payload, sort_keys=True)


def _mock_ensembl_gene_url(external_id: str | None) -> str | None:
    if not external_id:
        return None
    return f"https://www.ensembl.org/Homo_sapiens/Gene/Summary?g={external_id}"
