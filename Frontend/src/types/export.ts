export type ExportFormat = 'pptx' | 'docx' | 'pdf' | 'txt' | 'md' | 'mp3' | 'zip' | 'json';

export interface ExportRequestPayload {
  format: ExportFormat;
  require_approval?: boolean;
  custom_title?: string;
}

export interface ExportRecord {
  id?: string;
  exportId: string;
  projectId: string;
  deliverableId: string;
  format: ExportFormat | string;
  filename: string;
  fileId: string;
  sizeBytes: number;
  mimeType: string;
  downloadUrl?: string;
  status: 'ready' | 'processing' | 'failed';
  createdAt: string;
}
