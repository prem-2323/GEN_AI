export type JobStage =
  | 'queued'
  | 'extracting_pdf'
  | 'analyzing_images'
  | 'analyzing_text'
  | 'building_context'
  | 'generating_output'
  | 'parsing_results'
  | 'completed'
  | 'failed';

export interface JobRecord {
  jobId: string;
  projectId: string;
  sourceId: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  stage: JobStage;
  progress: number;
  error?: string;
  result?: any;
  createdAt: string;
  updatedAt: string;
}
