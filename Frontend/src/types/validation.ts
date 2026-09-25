export interface DeliverableValidationResult {
  deliverableType: string;
  groundingScore: number;
  unsupportedClaims: string[];
  unsupportedMetrics: string[];
  unsupportedEntities: string[];
  citedFacts: string[];
  checkpoints: Array<{
    name: string;
    passed: boolean;
    details: string;
  }>;
}

export interface ConsistencyValidationReport {
  id?: string;
  projectId: string;
  sourceId: string;
  overallScore: number;
  factsPreserved: { count: number; total: number; preservedRatio: number };
  numbersPreserved: { count: number; total: number; preservedRatio: number };
  datesPreserved: { count: number; total: number; preservedRatio: number };
  entitiesMatched: { count: number; total: number; matchRatio: number };
  citationsValid: { count: number; total: number; validRatio: number };
  unsupportedClaims: Array<{ claim: string; deliverable: string; reason: string }>;
  deliverableAudits: Record<string, DeliverableValidationResult>;
  createdAt: string;
}
