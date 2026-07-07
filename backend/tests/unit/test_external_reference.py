from types import SimpleNamespace

import pytest

from app.services import external_reference
from app.services.external_reference import (
    ExternalReferenceError,
    _fetch_ensembl_reference,
    fetch_ensembl_variant_reference,
    fetch_external_reference,
)


def test_fetch_ensembl_reference_maps_successful_response(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "id": "ENSG00000012048",
                "display_name": "BRCA1",
                "description": "BRCA1 DNA repair associated",
                "biotype": "protein_coding",
                "seq_region_name": "17",
                "start": 43044295,
                "end": 43170245,
                "extra_field": "not retained",
            }

    monkeypatch.setattr(external_reference.httpx, "get", lambda *_args, **_kwargs: FakeResponse())

    result = _fetch_ensembl_reference("BRCA1", "https://rest.ensembl.org", 3.0)

    assert result.source == "ensembl"
    assert result.lookup_status == "success"
    assert result.external_id == "ENSG00000012048"
    assert result.gene_biotype == "protein_coding"
    assert result.location == "17:43044295-43170245"
    assert result.summary == "BRCA1 DNA repair associated"
    assert result.raw_payload == {
        "id": "ENSG00000012048",
        "display_name": "BRCA1",
        "description": "BRCA1 DNA repair associated",
        "biotype": "protein_coding",
        "seq_region_name": "17",
        "start": 43044295,
        "end": 43170245,
    }


def test_fetch_ensembl_reference_rejects_unexpected_payload(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return ["not", "an", "object"]

    monkeypatch.setattr(external_reference.httpx, "get", lambda *_args, **_kwargs: FakeResponse())

    with pytest.raises(ExternalReferenceError):
        _fetch_ensembl_reference("BRCA1", "https://rest.ensembl.org", 3.0)


def test_fetch_ensembl_variant_reference_maps_vep_response(monkeypatch):
    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self.payload

    def fake_get(url, *_args, **_kwargs):
        if "/lookup/symbol/" in url:
            return FakeResponse(
                {
                    "id": "ENSG00000157764",
                    "display_name": "BRAF",
                    "description": "B-Raf proto-oncogene, serine/threonine kinase [Source:HGNC Symbol]",
                    "biotype": "protein_coding",
                    "seq_region_name": "7",
                    "start": 140719327,
                    "end": 140924929,
                }
            )
        return FakeResponse(
            [
                {
                    "input": "BRAF:p.V600E",
                    "id": "rs113488022",
                    "seq_region_name": "7",
                    "start": 140753336,
                    "end": 140753336,
                    "most_severe_consequence": "missense_variant",
                    "variant_class": "SNV",
                    "transcript_consequences": [
                        {
                            "gene_symbol": "BRAF",
                            "gene_id": "ENSG00000157764",
                            "transcript_id": "ENST00000646891",
                            "canonical": 1,
                            "impact": "MODERATE",
                            "consequence_terms": ["missense_variant"],
                            "hgvsc": "ENST00000646891.2:c.1799T>A",
                            "hgvsp": "ENSP00000493543.1:p.Val600Glu",
                        }
                    ],
                    "colocated_variants": [
                        {"id": "rs113488022", "clin_sig": ["pathogenic"], "minor_allele_freq": 0.0001}
                    ],
                }
            ]
        )

    monkeypatch.setattr(external_reference.httpx, "get", fake_get)

    result = fetch_ensembl_variant_reference("BRAF", "p.V600E", "missense", "https://rest.ensembl.org", 3.0)

    assert result.gene_symbol == "BRAF"
    assert result.gene_full_name == "B-Raf proto-oncogene, serine/threonine kinase"
    assert result.hgvs == "p.V600E"
    assert result.rsid == "rs113488022"
    assert result.transcript_id == "ENST00000646891"
    assert result.transcript_hgvs == "ENST00000646891.2:c.1799T>A"
    assert result.protein_hgvs == "ENSP00000493543.1:p.Val600Glu"
    assert result.significance == "pathogenic"
    assert result.allele_frequency == 0.0001


def test_fetch_external_reference_uses_deterministic_mock_mode(monkeypatch):
    settings = SimpleNamespace(external_reference_mode="mock")
    gene = SimpleNamespace(symbol="TP53")
    variant = SimpleNamespace(hgvs="p.R175H", position=175)
    monkeypatch.setattr(external_reference, "get_settings", lambda: settings)

    result = fetch_external_reference(gene, variant)

    assert result.source == "ensembl-mock"
    assert result.lookup_status == "success"
    assert result.external_id == "ENSG00000141510"
    assert result.external_url == "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000141510"
    assert "TP53" in result.summary


def test_fetch_external_reference_captures_live_lookup_failure(monkeypatch):
    settings = SimpleNamespace(
        external_reference_mode="live",
        external_reference_base_url="https://rest.ensembl.org",
        external_reference_timeout_seconds=0.01,
    )
    monkeypatch.setattr(external_reference, "get_settings", lambda: settings)
    monkeypatch.setattr(
        external_reference,
        "_fetch_ensembl_reference",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(TimeoutError("lookup timed out")),
    )

    result = fetch_external_reference(SimpleNamespace(symbol="CFTR"), SimpleNamespace(hgvs="ΔF508"))

    assert result.source == "ensembl"
    assert result.lookup_status == "failed"
    assert result.error_message == "lookup timed out"
