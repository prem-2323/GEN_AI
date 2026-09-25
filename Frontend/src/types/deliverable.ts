export type OutputType =
  | 'linkedin'
  | 'twitter'
  | 'advisory'
  | 'executive_summary'
  | 'infographic'
  | 'presentation'
  | 'video';

export interface TransformationConfig {
  targetAudience: string;
  tone: string;
  language: string;
  levelOfDetail: string;
  objective: string;
  contentStyle: string;
  customNotes?: string;
  brandVoice?: any;
}

export interface LinkedInDeliverable {
  hook: string;
  body: string;
  callToAction: string;
  hashtags: string[];
  characterCount: number;
  targetAudience: string;
}

export interface TwitterDeliverable {
  singlePost: string;
  thread: Array<{
    index: number;
    text: string;
    charCount: number;
  }>;
}

export interface AdvisoryDeliverable {
  advisoryId: string;
  title: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'INFORMATIONAL';
  dateIssued: string;
  situation: string;
  keyInformation: string[];
  threatImpact: string;
  recommendedActions: Array<{
    phase: string;
    steps: string[];
  }>;
  complianceReferences: string[];
}

export interface ExecutiveSummaryDeliverable {
  priority: 'High' | 'Critical' | 'Medium' | 'Low';
  keyFindingsCount: number;
  recommendationsCount: number;
  executiveOverview: string;
  keyFindings: Array<{
    metric?: string;
    title: string;
    description: string;
  }>;
  implications: string[];
  strategicActions: string[];
}

export interface InfographicDeliverable {
  keyMessage: string;
  keyStatistics: Array<{
    value: string;
    label: string;
    subtext: string;
  }>;
  supportingPoints: Array<{
    iconName: string;
    title: string;
    description: string;
  }>;
  callToAction: string;
  layoutRecommendation: 'Vertical' | 'Horizontal' | 'Timeline' | 'Process' | 'Comparison';
  visualStyle: 'Corporate' | 'Minimal' | 'Editorial' | 'Technology';
}

export interface PresentationSlide {
  slideNumber: number;
  title: string;
  subtitle?: string;
  bullets: string[];
  column_left?: string[];
  column_right?: string[];
  visualRecommendation?: string;
  visual_recommendation?: string;
  speakerNotes?: string;
  speaker_notes?: string;
}

export interface PresentationDeliverable {
  deckTitle: string;
  presentation_title?: string;
  subtitle?: string;
  totalSlides: number;
  theme?: string;
  slides: PresentationSlide[];
}

export interface VideoScene {
  sceneNumber: number;
  title: string;
  durationSeconds: number;
  sceneDescription: string;
  visualRecommendation: string;
  narration: string;
  onScreenText: string;
}

export interface VideoDeliverable {
  title: string;
  aspectRatio: '16:9' | '9:16' | '1:1';
  style: 'Professional' | 'News' | 'Documentary' | 'Corporate';
  totalDurationSeconds: number;
  script: string;
  scenes: VideoScene[];
  subtitlesSrt: string;
}

export interface DeliverablesState {
  linkedin?: LinkedInDeliverable;
  twitter?: TwitterDeliverable;
  advisory?: AdvisoryDeliverable;
  executive_summary?: ExecutiveSummaryDeliverable;
  infographic?: InfographicDeliverable;
  presentation?: PresentationDeliverable;
  video?: VideoDeliverable;
}

export type TransformationDeliverables = DeliverablesState;

export interface DeliverableRecord {
  id?: string;
  deliverableId: string;
  projectId: string;
  sourceId?: string;
  type: OutputType | string;
  title?: string;
  content: any;
  approved?: boolean;
  qualityScore?: number;
  validationStatus?: string;
  uckrVersion?: number;
  createdAt: string;
  updatedAt: string;
}
