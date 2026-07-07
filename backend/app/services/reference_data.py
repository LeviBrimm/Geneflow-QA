from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.models.gene import Gene
from app.models.variant import Variant, VariantEmbedding
from app.services.external_reference import fetch_ensembl_variant_reference
from app.services.parser import ParsedVariant
from app.services.similarity import vector_to_storage


SEED_DATA = [
    {
        "symbol": "BRCA1",
        "full_name": "BRCA1 DNA repair associated",
        "description": "BRCA1 is involved in DNA repair and genome stability.",
        "variants": [
            {
                "hgvs": "c.5266dupC",
                "rsid": "rs80357906",
                "variant_type": "frameshift",
                "significance": "Pathogenic",
                "condition": "Hereditary breast and ovarian cancer syndrome",
                "allele_frequency": 0.00003,
                "summary": "A duplication in BRCA1 that disrupts the reading frame in public reference annotations.",
                "position": 5266,
                "domain": "BRCT domain",
                "transcript_id": "NM_007294.4",
                "transcript_hgvs": "NM_007294.4:c.5266dupC",
                "protein_hgvs": "NP_009225.1:p.Gln1756Profs",
            }
        ],
    },
    {
        "symbol": "TP53",
        "full_name": "Tumor protein p53",
        "description": "TP53 encodes a tumor suppressor involved in cell-cycle control and DNA damage response.",
        "variants": [
            {
                "hgvs": "p.R175H",
                "rsid": "rs28934578",
                "variant_type": "missense",
                "significance": "Pathogenic",
                "condition": "Li-Fraumeni syndrome",
                "allele_frequency": 0.00002,
                "summary": "A recurrent TP53 missense variant affecting the DNA-binding domain.",
                "position": 175,
                "domain": "DNA-binding domain",
                "transcript_id": "NM_000546.6",
                "transcript_hgvs": "NM_000546.6:c.524G>A",
                "protein_hgvs": "NP_000537.3:p.Arg175His",
            }
        ],
    },
    {
        "symbol": "CFTR",
        "full_name": "CF transmembrane conductance regulator",
        "description": "CFTR encodes an ion channel involved in chloride transport across epithelial cells.",
        "variants": [
            {
                "hgvs": "ΔF508",
                "rsid": "rs113993960",
                "variant_type": "deletion",
                "significance": "Pathogenic",
                "condition": "Cystic fibrosis",
                "allele_frequency": 0.007,
                "summary": "A common CFTR deletion removing phenylalanine at position 508.",
                "position": 508,
                "domain": "NBD1",
                "transcript_id": "NM_000492.4",
                "transcript_hgvs": "NM_000492.4:c.1521_1523delCTT",
                "protein_hgvs": "NP_000483.3:p.Phe508del",
            }
        ],
    },
]


def seed_reference_data(db: Session) -> None:
    if db.scalar(select(Gene).limit(1)):
        _update_seed_variant_metadata(db)
        return
    for gene_data in SEED_DATA:
        variants = gene_data["variants"]
        gene = Gene(
            symbol=gene_data["symbol"],
            full_name=gene_data["full_name"],
            description=gene_data["description"],
        )
        db.add(gene)
        db.flush()
        for variant_data in variants:
            variant = Variant(gene_id=gene.id, **variant_data)
            variant.reference_source = "seeded"
            db.add(variant)
            db.flush()
            db.add(
                VariantEmbedding(variant_id=variant.id, embedding=vector_to_storage(_seed_embedding(variant.summary)))
            )
    db.commit()


def _update_seed_variant_metadata(db: Session) -> None:
    updated = False
    for gene_data in SEED_DATA:
        for variant_data in gene_data["variants"]:
            variant = db.scalar(
                select(Variant)
                .join(Gene)
                .where(Gene.symbol == gene_data["symbol"])
                .where(Variant.hgvs == variant_data["hgvs"])
            )
            if not variant:
                continue
            if variant.reference_source != "seeded":
                variant.reference_source = "seeded"
                updated = True
            for field in ("transcript_id", "transcript_hgvs", "protein_hgvs"):
                if getattr(variant, field) != variant_data[field]:
                    setattr(variant, field, variant_data[field])
                    updated = True
    if updated:
        db.commit()


def lookup_variant(db: Session, parsed: ParsedVariant) -> Variant | None:
    return db.scalar(
        select(Variant).join(Gene).where(Gene.symbol == parsed.gene).where(Variant.hgvs == parsed.notation)
    )


def resolve_variant_reference(db: Session, parsed: ParsedVariant) -> Variant | None:
    variant = lookup_variant(db, parsed)
    if variant:
        return variant

    settings = get_settings()
    if settings.external_reference_mode.lower() != "live":
        return None

    ensembl_reference = fetch_ensembl_variant_reference(
        parsed.gene,
        parsed.notation,
        parsed.variant_type,
        base_url=settings.external_reference_base_url,
        timeout=settings.external_reference_timeout_seconds,
    )
    gene = db.scalar(select(Gene).where(Gene.symbol == parsed.gene))
    if not gene:
        gene = Gene(
            symbol=ensembl_reference.gene_symbol,
            full_name=ensembl_reference.gene_full_name,
            description=ensembl_reference.gene_description,
        )
        db.add(gene)
        db.flush()

    variant = Variant(
        gene_id=gene.id,
        hgvs=ensembl_reference.hgvs,
        rsid=ensembl_reference.rsid,
        variant_type=ensembl_reference.variant_type,
        significance=ensembl_reference.significance,
        condition=ensembl_reference.condition,
        allele_frequency=ensembl_reference.allele_frequency,
        summary=ensembl_reference.summary,
        position=ensembl_reference.position,
        domain=ensembl_reference.domain,
        reference_source="ensembl_vep",
        transcript_id=ensembl_reference.transcript_id,
        transcript_hgvs=ensembl_reference.transcript_hgvs,
        protein_hgvs=ensembl_reference.protein_hgvs,
    )
    db.add(variant)
    db.flush()
    db.add(VariantEmbedding(variant_id=variant.id, embedding=vector_to_storage(_seed_embedding(variant.summary))))
    return variant


def _seed_embedding(text: str) -> list[float]:
    words = text.lower()
    return [
        float(words.count("dna") + words.count("repair")),
        float(words.count("missense") + words.count("domain")),
        float(words.count("deletion") + words.count("duplication")),
        float(words.count("cystic") + words.count("cancer")),
    ]
