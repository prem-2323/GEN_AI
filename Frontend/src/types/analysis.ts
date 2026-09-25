export interface AIAnalysisEntity {
  name: string;
  category: string;
  mentions: number;
  role?: string;
  sourceContext?: string;
}

export interface AIAnalysisEvent {
  title: string;
  timestamp: string;
  impact: string;
  actors: string[];
}

export interface AIAnalysisMetric {
  name: string;
  value: string | number;
  unit?: string;
  context: string;
  confidence?: number;
}

export interface AIAnalysisFact {
  id?: string;
  statement: string;
  value?: string;
  category?: string;
  type?: string;
  sourceDoc?: string;
  page?: number;
  section?: string;
  confidence: number;
  quote?: string;
}

export interface AIAnalysisVisualEvidence {
  imageId?: string;
  description: string;
  diagramType?: string;
  extractedLabels: string[];
  confidence: number;
}

export interface AIAnalysis {
  provider?: 'ollama' | 'gemini' | 'deterministic' | 'hybrid';
  model?: string;
  visionModel?: string;
  detectedTopic: string;
  summary: string;
  domain?: string;
  confidenceScore: number;
  keyEntities: AIAnalysisEntity[];
  entities?: AIAnalysisEntity[];
  keyEvents: AIAnalysisEvent[];
  events?: AIAnalysisEvent[];
  keyMetrics: AIAnalysisMetric[];
  metrics?: AIAnalysisMetric[];
  facts?: AIAnalysisFact[];
  visualEvidence?: AIAnalysisVisualEvidence[];
  intentMap?: {
    primaryIntent: string;
    targetAudience: string;
    complexityLevel: string;
  };
}

export interface AnalysisRecord {
  id?: string;
  projectId: string;
  sourceId: string;
  firebaseUid?: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  provider: string;
  model: string;
  visionModel?: string;
  summary: string;
  facts: AIAnalysisFact[];
  entities: AIAnalysisEntity[];
  events: AIAnalysisEvent[];
  metrics: AIAnalysisMetric[];
  visualEvidence: AIAnalysisVisualEvidence[];
  createdAt: string;
  updatedAt: string;
}
