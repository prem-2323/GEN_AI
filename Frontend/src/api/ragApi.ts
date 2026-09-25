import { workspaceFetch } from './client';

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
  query: async (payload: RagQueryPayload): Promise<RagQueryResponse> => {
    return workspaceFetch('/api/rag/query', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};
