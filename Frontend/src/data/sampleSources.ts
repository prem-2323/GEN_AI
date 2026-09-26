export interface SampleSourceDoc {
  id: string;
  name: string;
  type: 'PDF' | 'DOCX' | 'TXT';
  size: string;
  category: string;
  summary: string;
  content: string;
}

export const SAMPLE_SOURCES: SampleSourceDoc[] = [];
