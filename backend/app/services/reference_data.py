from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.gene import Gene
from app.models.variant import Variant, VariantEmbedding
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
            }
        ],
    },
]


def seed_reference_data(db: Session) -> None:
    if db.scalar(select(Gene).limit(1)):
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
            db.add(variant)
            db.flush()
            db.add(
                VariantEmbedding(variant_id=variant.id, embedding=vector_to_storage(_seed_embedding(variant.summary)))
            )
    db.commit()


def lookup_variant(db: Session, parsed: ParsedVariant) -> Variant | None:
    return db.scalar(
        select(Variant).join(Gene).where(Gene.symbol == parsed.gene).where(Variant.hgvs == parsed.notation)
    )


def _seed_embedding(text: str) -> list[float]:
    words = text.lower()
    return [
        float(words.count("dna") + words.count("repair")),
        float(words.count("missense") + words.count("domain")),
        float(words.count("deletion") + words.count("duplication")),
        float(words.count("cystic") + words.count("cancer")),
    ]
