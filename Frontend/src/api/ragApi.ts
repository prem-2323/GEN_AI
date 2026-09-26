import { workspaceFetch } from './client';

export interface GroundedAnswerPayload {
  query: string;
  top_k?: number;
  qubo_k?: number;
  enable_qubo?: boolean;
  max_new_tokens?: number;
}

export interface EvidenceItem {
  evidence_id: string;
  document_id: string;
  page_number: number;
  chunk_id?: string;
  text: string;
  source?: string;
  score?: number;
  qubo_score?: number;
}

export interface GroundedAnswerResponse {
  query: string;
  answer: string;
  citations: string[];
  evidence: EvidenceItem[];
  retrieval: {
    fused_count: number;
    vector_candidates: number;
    graph_candidates: number;
    fusion_time_ms: number;
  };
  qubo: {
    qubo_enabled: boolean;
    solver_type?: string;
    total_energy?: number;
    qubo_optimization_time_ms?: number;
  };
  model: {
    model_name: string;
    adapter_path: string;
  };
  grounding: {
    grounding_pass: boolean;
    numerical_valid: boolean;
    cited_evidence_ids: string[];
    invalid_citations: string[];
    unsupported_numbers: string[];
  };
  total_latency_ms: number;
}

export interface RagQueryPayload {
  query: string;
  document_ids?: string[];
  top_k?: number;
  use_optimization?: boolean;
}

export interface RagSourceUI {
  citation_id: number | string;
  document_id: string;
  chunk_id?: string;
  page?: number;
  section?: string;
  text?: string;
  score?: number;
}

export interface RagQueryResponse {
  query: string;
  answer: string;
  sources: RagSourceUI[];
  citations: Record<string, any>[];
  latency_ms?: number;
}

export const ragApi = {
  answer: async (payload: GroundedAnswerPayload): Promise<GroundedAnswerResponse> => {
    return workspaceFetch('/api/rag/answer', {
      method: 'POST',
      body: JSON.stringify({
        query: payload.query,
        top_k: payload.top_k ?? 5,
        qubo_k: payload.qubo_k ?? 3,
        enable_qubo: payload.enable_qubo ?? true,
        max_new_tokens: payload.max_new_tokens ?? 256,
      }),
    });
  },

  query: async (payload: RagQueryPayload): Promise<RagQueryResponse> => {
    return workspaceFetch('/api/rag/query', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};
