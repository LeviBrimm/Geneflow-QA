from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    raw_input: str


class AnalyzeResponse(BaseModel):
    query_id: int
    job_id: str
    status: str


class QuerySummaryResponse(BaseModel):
    query_id: int
    raw_input: str
    status: str
    created_at: str
    job_id: str | None


class ParsedVariantResponse(BaseModel):
    gene: str
    notation: str
    variant_type: str
    is_valid: bool


class ReferenceDataResponse(BaseModel):
    gene_full_name: str | None
    gene_description: str | None
    rsid: str | None
    significance: str | None
    condition: str | None
    allele_frequency: float | None
    summary: str | None
    position: int | None
    domain: str | None


class ExplanationResponse(BaseModel):
    general: str | None
    technical: str | None
    model_used: str | None


class ExternalReferenceResponse(BaseModel):
    source: str | None
    lookup_status: str
    external_id: str | None
    external_url: str | None
    gene_biotype: str | None
    location: str | None
    summary: str | None
    error_message: str | None


class SimilarVariantResponse(BaseModel):
    variant_id: int
    gene: str
    hgvs: str
    significance: str
    condition: str
    similarity_score: float


class VariantResultResponse(QuerySummaryResponse):
    parsed: ParsedVariantResponse
    reference: ReferenceDataResponse
    explanations: ExplanationResponse
    external_reference: ExternalReferenceResponse
    similar_variants: list[SimilarVariantResponse]


class JobStatusResponse(BaseModel):
    job_id: str
    query_id: int
    status: str
    error_message: str | None
    started_at: str | None
    completed_at: str | None


class HealthResponse(BaseModel):
    status: str
    service: str
