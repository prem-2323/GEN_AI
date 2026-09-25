export interface ProjectRecord {
  id: string;
  projectId?: string;
  userId?: string;
  firebaseUid?: string;
  name: string;
  projectName?: string;
  title?: string;
  description?: string;
  status: 'Draft' | 'Processing' | 'Ready' | 'Completed' | 'Failed';
  sourceCount?: number;
  source?: any;
  sourceFile?: any;
  config?: any;
  selectedOutputs?: string[];
  analysis?: any;
  uckr?: any;
  deliverables?: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

export interface ProjectCreatePayload {
  name: string;
  description?: string;
  id?: string;
}

export interface ProjectUpdatePayload {
  name?: string;
  description?: string;
  status?: string;
  sourceCount?: number;
  source?: any;
  config?: any;
  selectedOutputs?: string[];
  analysis?: any;
  uckr?: any;
  deliverables?: Record<string, any>;
}

export interface ProjectWorkspaceResponse {
  project: ProjectRecord;
  sources: any[];
  analysis: any[];
  uckr: any[];
  deliverables: any[];
  validations: any[];
  quality: any[];
  exports: any[];
}
