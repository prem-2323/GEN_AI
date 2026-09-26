export type UckrFactType =
  | 'Metric'
  | 'Proposition'
  | 'Entity Finding'
  | 'Timeline / Event'
  | 'Action Mandate'
  | 'Risk / Impact'
  | 'Technical Spec'
  | 'Guideline / Policy';

export type UckrEntityCategory =
  | 'Actor / Stakeholder'
  | 'Organization'
  | 'Technology / Standard'
  | 'Specification'
  | 'Infrastructure / Asset'
  | 'Policy / Regulation'
  | 'Location';

export interface SourceReference {
  docId?: string;
  sourceDoc?: string;
  page?: number;
  section?: string;
  chunkId?: string;
  quote?: string;
}

export interface UckrFact {
  id: string;
  factId?: string;
  value?: string;
  statement?: string;
  type: UckrFactType | string;
  sourceDoc: string;
  page?: number;
  section?: string;
  confidence: number;
  quote: string;
  sourceRefs?: SourceReference[];
  usedInDeliverables?: string[];
}

export interface UckrEntity {
  id: string;
  entityId?: string;
  name: string;
  canonicalName?: string;
  category: UckrEntityCategory | string;
  mentions: number;
  role?: string;
  sourceContext?: string;
}

export interface UckrEvent {
  id: string;
  eventId?: string;
  title: string;
  name?: string;
  timestamp?: string;
  date?: string;
  impact?: string;
  actors: string[];
}

export interface UckrTimelineNode {
  id: string;
  description: string;
  duration_value?: number | null;
  duration_unit?: string | null;
  sequence?: number | null;
  kind?: 'total' | 'phase' | 'milestone' | string;
  sourceFactId?: string | null;
  sourceText?: string;
  startRelationship?: string | null;
  endRelationship?: string | null;
}

export interface UckrMetric {
  id: string;
  metricId?: string;
  name: string;
  value: string | number;
  unit?: string;
  context: string;
  confidence: number;
}

export interface UckrRelationship {
  id: string;
  relationshipId?: string;
  source: string;
  sourceEntityId?: string;
  relation: string;
  relationshipType?: string;
  target: string;
  targetEntityId?: string;
  confidence: number;
}

export interface UckrAction {
  id: string;
  actionId?: string;
  action: string;
  text?: string;
  priority: 'P0 Immediate' | 'P1 High' | 'P2 Medium' | string;
  timeframe?: string;
  owner?: string;
}

export interface UckrClaim {
  id: string;
  claimId?: string;
  statement: string;
  category?: string;
  confidence: number;
  isSupported?: boolean;
  citationId?: string;
}

export interface UckrSourceCitation {
  id: string;
  citationId?: string;
  title?: string;
  sourceDoc?: string;
  page?: number;
  section?: string;
  chunkId?: string;
  excerpt?: string;
  quote?: string;
}

export interface UckrStatistics {
  totalFacts: number;
  totalEntities: number;
  totalEvents: number;
  totalTimelineNodes?: number;
  timelineConsistent?: boolean | null;
  timelineTotalDuration?: number | null;
  timelineDurationUnit?: string | null;
  timelinePhaseCount?: number;
  totalMetrics: number;
  totalClaims?: number;
  totalActions: number;
  totalSources: number;
  totalRelationships: number;
  coverage: number;
  grounding: number;
  groundingIndex?: number;
  factCompleteness?: number;
  factConsistency?: number;
  entityConsistency?: number;
  numberConsistency?: number;
  dateConsistency?: number;
  readiness: string;
}

export interface UckrKnowledgeBase {
  id?: string;
  uckrId?: string;
  projectId?: string;
  sourceId?: string;
  version: number;
  status?: string;
  statistics: UckrStatistics;
  stats: UckrStatistics; // alias for backwards compatibility
  facts: UckrFact[];
  entities: UckrEntity[];
  events: UckrEvent[];
  timeline?: UckrTimelineNode[];
  metrics: UckrMetric[];
  claims?: UckrClaim[];
  relationships: UckrRelationship[];
  actions: UckrAction[];
  citations?: UckrSourceCitation[];
  sources: UckrSourceCitation[];
  validation?: {
    timelineConsistency?: {
      consistent?: boolean | null;
      declared_total?: number;
      calculated_total?: number;
      duration_unit?: string;
      phase_count?: number;
    };
  };
  createdAt?: string;
  updatedAt?: string;
}

export interface UckrVersionSummary {
  version: number;
  uckrId: string;
  createdAt: string;
  factCount: number;
  entityCount: number;
  grounding: number;
  status: string;
}
