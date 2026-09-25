export interface QualityMetrics {
  factPreservation: number; // 0 - 100
  consistency: number; // 0 - 100
  citationCoverage: number; // 0 - 100
  sourceGrounding: number; // 0 - 100
  completeness: number; // 0 - 100
  overall: number; // 0 - 100
  status: 'PASS' | 'WARN' | 'FAIL';
}

export interface DeliverableQualityReport {
  deliverableId: string;
  projectId: string;
  type: string;
  approved: boolean;
  approvedAt?: string;
  approvedBy?: string;
  metrics: QualityMetrics;
  suggestions: string[];
}
