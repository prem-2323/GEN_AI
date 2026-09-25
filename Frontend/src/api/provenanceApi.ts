import { authenticatedFetch } from './client';

export interface LineageNodeUI {
  node_id: string;
  node_type: string;
  label: string;
  location?: Record<string, any>;
  metadata?: Record<string, any>;
  children?: LineageNodeUI[];
}

export interface LineageTreeUI {
  root_id: string;
  direction: 'FORWARD' | 'REVERSE';
  tree: LineageNodeUI;
  total_nodes: number;
  depth: number;
  completeness_score: number;
}

export interface OutputProvenanceUI {
  output_id: string;
  document_ids: string[];
  claim_ids: string[];
  evidence_ids: string[];
  citation_ids: string[];
  validation_id?: string;
  metadata?: Record<string, any>;
  transformation_metadata?: Record<string, any>;
  created_at: string;
  content_hash: string;
}

export interface IntegrityResultUI {
  valid: boolean;
  source_id: string;
  expected_hash: string;
  actual_hash: string;
  checked_at: string;
  message: string;
}

export const provenanceApi = {
  getOutputProvenance: async (outputId: string): Promise<OutputProvenanceUI> => {
    return authenticatedFetch(`/api/provenance/output/${outputId}`);
  },

  getOutputLineage: async (outputId: string): Promise<LineageTreeUI> => {
    return authenticatedFetch(`/api/provenance/output/${outputId}/lineage`);
  },

  getDocumentLineage: async (documentId: string): Promise<LineageTreeUI> => {
    return authenticatedFetch(`/api/provenance/document/${documentId}/lineage`);
  },

  getClaimProvenance: async (claimId: string): Promise<any> => {
    return authenticatedFetch(`/api/provenance/claim/${claimId}`);
  },

  getEvidence: async (evidenceId: string): Promise<any> => {
    return authenticatedFetch(`/api/provenance/evidence/${evidenceId}`);
  },

  getCitationProvenance: async (citationId: string): Promise<any> => {
    return authenticatedFetch(`/api/provenance/citation/${citationId}`);
  },

  verifyIntegrity: async (payload: { artifact_id: string; content: string; expected_hash?: string }): Promise<IntegrityResultUI> => {
    return authenticatedFetch('/api/provenance/verify', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  getMetrics: async (): Promise<any> => {
    return authenticatedFetch('/api/provenance/metrics');
  },
};
