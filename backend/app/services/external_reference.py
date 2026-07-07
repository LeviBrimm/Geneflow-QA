import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

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


@dataclass(frozen=True)
class EnsemblVariantReference:
    gene_symbol: str
    gene_full_name: str
    gene_description: str
    hgvs: str
    variant_type: str
    significance: str
    condition: str
    allele_frequency: float | None
    summary: str
    position: int | None
    domain: str | None
    transcript_id: str | None
    transcript_hgvs: str | None
    protein_hgvs: str | None
    rsid: str | None
    consequence_terms: list[str]
    impact: str | None
    raw_payload: dict[str, Any]


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


def fetch_ensembl_variant_reference(
    gene_symbol: str,
    notation: str,
    variant_type: str,
    base_url: str,
    timeout: float,
) -> EnsemblVariantReference:
    gene_reference = _fetch_ensembl_reference(gene_symbol, base_url, timeout)
    hgvs_notation = _ensembl_hgvs_notation(gene_symbol, notation)
    vep_payload = _fetch_ensembl_vep_hgvs(hgvs_notation, base_url, timeout)
    primary_result = _first_dict(vep_payload)
    transcript = _select_transcript_consequence(primary_result, gene_symbol)
    colocated = _select_colocated_variant(primary_result)
    consequence_terms = _string_list(transcript.get("consequence_terms"))
    rsid = _string_or_none(colocated.get("id")) or _string_or_none(primary_result.get("id"))
    clinical_significance = _first_string(colocated.get("clin_sig"))
    allele_frequency = _float_or_none(
        colocated.get("minor_allele_freq")
        or colocated.get("gnomadg_af")
        or colocated.get("gnomade_af")
        or transcript.get("gnomadg_af")
        or transcript.get("gnomade_af")
    )
    location = _string_or_none(primary_result.get("seq_region_name"))
    start = _int_or_none(primary_result.get("start"))
    location_summary = f"{location}:{start}" if location and start else "the submitted locus"
    impact = _string_or_none(transcript.get("impact"))
    summary = (
        f"Live Ensembl VEP annotation for {gene_symbol} {notation}. "
        f"Most relevant consequence: {', '.join(consequence_terms) if consequence_terms else 'sequence_variant'} "
        f"at {location_summary}."
    )

    return EnsemblVariantReference(
        gene_symbol=gene_symbol,
        gene_full_name=_gene_full_name(gene_reference.summary, gene_symbol),
        gene_description=gene_reference.summary or f"Live Ensembl gene record for {gene_symbol}.",
        hgvs=notation,
        variant_type=_variant_type_from_terms(consequence_terms) or variant_type,
        significance=clinical_significance or "Not provided by Ensembl VEP",
        condition="Not provided by Ensembl VEP",
        allele_frequency=allele_frequency,
        summary=summary,
        position=start,
        domain=_domain_summary(transcript),
        transcript_id=_string_or_none(transcript.get("transcript_id")) or _string_or_none(transcript.get("feature")),
        transcript_hgvs=_string_or_none(transcript.get("hgvsc")),
        protein_hgvs=_string_or_none(transcript.get("hgvsp")),
        rsid=rsid,
        consequence_terms=consequence_terms,
        impact=impact,
        raw_payload=_compact_vep_payload(primary_result, transcript, colocated, gene_reference.raw_payload),
    )


def _fetch_ensembl_vep_hgvs(hgvs_notation: str, base_url: str, timeout: float) -> list[dict[str, Any]]:
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
        raise ExternalReferenceError("Ensembl VEP response did not include variant consequences.")
    return [item for item in payload if isinstance(item, dict)]


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


def _compact_vep_payload(
    result: dict[str, Any],
    transcript: dict[str, Any],
    colocated: dict[str, Any],
    gene_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "gene": gene_payload,
        "vep": {
            "input": result.get("input"),
            "id": result.get("id"),
            "assembly_name": result.get("assembly_name"),
            "seq_region_name": result.get("seq_region_name"),
            "start": result.get("start"),
            "end": result.get("end"),
            "most_severe_consequence": result.get("most_severe_consequence"),
            "variant_class": result.get("variant_class"),
        },
        "transcript_consequence": {
            "gene_symbol": transcript.get("gene_symbol"),
            "gene_id": transcript.get("gene_id"),
            "transcript_id": transcript.get("transcript_id"),
            "impact": transcript.get("impact"),
            "consequence_terms": transcript.get("consequence_terms"),
            "hgvsc": transcript.get("hgvsc"),
            "hgvsp": transcript.get("hgvsp"),
            "canonical": transcript.get("canonical"),
            "mane_select": transcript.get("mane_select"),
        },
        "colocated_variant": {
            "id": colocated.get("id"),
            "clin_sig": colocated.get("clin_sig"),
            "minor_allele_freq": colocated.get("minor_allele_freq"),
        },
    }


def _ensembl_hgvs_notation(gene_symbol: str, notation: str) -> str:
    return notation if ":" in notation else f"{gene_symbol}:{notation}"


def _first_dict(items: list[dict[str, Any]]) -> dict[str, Any]:
    if not items:
        raise ExternalReferenceError("Ensembl VEP response did not include JSON objects.")
    return items[0]


def _select_transcript_consequence(result: dict[str, Any], gene_symbol: str) -> dict[str, Any]:
    consequences = result.get("transcript_consequences")
    if not isinstance(consequences, list):
        return {}
    dicts = [item for item in consequences if isinstance(item, dict)]
    if not dicts:
        return {}
    matching = [item for item in dicts if item.get("gene_symbol") == gene_symbol]
    candidates = matching or dicts
    for flag in ("mane_select", "canonical", "pick"):
        for item in candidates:
            if item.get(flag):
                return item
    return candidates[0]


def _select_colocated_variant(result: dict[str, Any]) -> dict[str, Any]:
    colocated = result.get("colocated_variants")
    if not isinstance(colocated, list):
        return {}
    dicts = [item for item in colocated if isinstance(item, dict)]
    if not dicts:
        return {}
    for item in dicts:
        if isinstance(item.get("id"), str) and item["id"].startswith("rs"):
            return item
    return dicts[0]


def _gene_full_name(description: str | None, gene_symbol: str) -> str:
    if not description:
        return gene_symbol
    return description.split("[", 1)[0].strip() or gene_symbol


def _domain_summary(transcript: dict[str, Any]) -> str | None:
    domains = transcript.get("domains")
    if not isinstance(domains, list):
        return None
    labels = []
    for item in domains:
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            labels.append(item["id"])
    return ", ".join(labels[:3]) or None


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _variant_type_from_terms(terms: list[str]) -> str | None:
    if "frameshift_variant" in terms:
        return "frameshift"
    if "stop_gained" in terms:
        return "nonsense"
    if "missense_variant" in terms:
        return "missense"
    if "inframe_deletion" in terms or "feature_truncation" in terms:
        return "deletion"
    if "synonymous_variant" in terms:
        return "synonymous"
    return None


def _first_string(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str):
                return item
    return None


def _int_or_none(value: Any) -> int | None:
    return value if isinstance(value, int) else None


def _float_or_none(value: Any) -> float | None:
    if isinstance(value, int | float):
        return float(value)
    return None


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
