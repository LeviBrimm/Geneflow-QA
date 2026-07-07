export type AuthResponse = {
  access_token: string;
  token_type: string;
  email: string;
};

export type AnalyzeResponse = {
  query_id: number;
  job_id: string;
  status: JobStatus;
};

export type JobStatus = "queued" | "processing" | "completed" | "failed";

export type JobResponse = {
  job_id: string;
  query_id: number;
  status: JobStatus;
  error_message?: string | null;
};

export type VariantResult = {
  query_id: number;
  raw_input: string;
  status: JobStatus;
  created_at: string;
  job_id: string;
  parsed: {
    gene: string;
    notation: string;
    variant_type: string;
    is_valid: boolean;
  };
  reference: {
    gene_full_name: string | null;
    gene_description: string | null;
    rsid: string | null;
    significance: string | null;
    condition: string | null;
    allele_frequency: number | null;
    summary: string | null;
    position: number | null;
    domain: string | null;
    reference_source: string | null;
  };
  explanations: {
    general: string | null;
    technical: string | null;
    model_used: string | null;
  };
  external_reference: {
    source: string | null;
    lookup_status: string;
    external_id: string | null;
    external_url: string | null;
    gene_biotype: string | null;
    location: string | null;
    summary: string | null;
    error_message: string | null;
  };
  variant_evidence: VariantEvidence[];
  similar_variants: SimilarVariant[];
};

export type HistoryItem = {
  query_id: number;
  raw_input: string;
  status: JobStatus;
  created_at: string;
  job_id: string;
};

export type SimilarVariant = {
  variant_id: number;
  gene: string;
  hgvs: string;
  significance: string;
  condition: string;
  similarity_score: number;
};

export type VariantEvidence = {
  source: string;
  lookup_status: string;
  evidence_level: string;
  submitted_notation: string | null;
  normalized_hgvs: string | null;
  rsid: string | null;
  transcript_id: string | null;
  consequence_terms: string[];
  impact: string | null;
  clinical_significance: string | null;
  condition: string | null;
  review_status: string | null;
  external_url: string | null;
  error_message: string | null;
};
