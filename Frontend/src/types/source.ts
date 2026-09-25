export type SourceType = 'PDF' | 'DOCX' | 'TXT' | 'MD' | 'JSON' | 'IMAGE' | 'AUDIO' | 'VIDEO';

export interface SourceFile {
  id: string;
  sourceId?: string;
  projectId?: string;
  userId?: string;
  name: string;
  type: SourceType | string;
  size: string | number;
  pages?: number;
  status: 'validating' | 'extracting' | 'analyzing' | 'building_uckr' | 'ready' | 'completed' | 'failed';
  uploadedAt?: string;
  createdAt?: string;
  updatedAt?: string;
  extractedText?: string;
  fileId?: string;
  storagePath?: string;
  mimeType?: string;
  sha256?: string;
  normalized?: {
    text: { content: string; wordCount: number };
    tables: any[];
    sections: any[];
    metadata: Record<string, any>;
  };
}

export interface SourceUploadResponse {
  ok: boolean;
  source: SourceFile;
}

export interface SourceListResponse {
  ok: boolean;
  sources: SourceFile[];
  count: number;
}
