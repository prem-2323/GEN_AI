import React, { useState } from 'react';
import {
  ViewState,
  SourceFile,
  TransformationConfig,
  OutputType,
  DeliverablesState,
  ProjectRecord,
  AIAnalysis,
  TransformationProject,
  UckrKnowledgeBase
} from './types';
import { Sidebar } from './components/layout/Sidebar';
import { TopBar } from './components/layout/TopBar';
import { ToastContainer, ToastMessage } from './components/common/Toast';
import { DashboardView } from './components/dashboard/DashboardView';
import { NewTransformationView } from './components/transformation/NewTransformationView';
import { GenerationPipelineView } from './components/transformation/GenerationPipelineView';
import { ResultsWorkspaceView } from './components/results/ResultsWorkspaceView';
import { ProjectsView } from './components/pages/ProjectsView';
import { OutputsView } from './components/pages/OutputsView';
import { AgentsView } from './components/pages/AgentsView';
import { McpView } from './components/pages/McpView';
import { SettingsView } from './components/pages/SettingsView';
import { UckrPanel } from './components/uckr/UckrPanel';
import { FirebaseProvider, useFirebase } from './context/FirebaseContext';
import { generateDeliverables } from './services/aiService';
import { AuthModal } from './components/auth/AuthModal';

const DEFAULT_CONFIG: TransformationConfig = {
  targetAudience: 'General Public',
  tone: 'Professional',
  language: 'English',
  levelOfDetail: 'Balanced',
  objective: 'Inform',
  contentStyle: 'Professional',
};

export interface PipelineResults {
  deliverables: DeliverablesState;
  analysis: AIAnalysis | null;
  uckr: UckrKnowledgeBase | null;
}

function AppContent() {
  const {
    user,
    cloudProjects,
    isSyncing,
    saveProjectToCloud,
    deleteProjectFromCloud,
    signInWithGoogle
  } = useFirebase();

  const [currentView, setCurrentView] = useState<ViewState>('dashboard');
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  // Active Project & Transformation State — empty by default, no demo content
  const [currentProjectId, setCurrentProjectId] = useState<string>('');
  const [source, setSource] = useState<SourceFile | null>(null);
  const [config, setConfig] = useState<TransformationConfig>(DEFAULT_CONFIG);
  const [analysis, setAnalysis] = useState<AIAnalysis | null>(null);
  const [uckr, setUckr] = useState<UckrKnowledgeBase | null>(null);
  const [selectedOutputs, setSelectedOutputs] = useState<OutputType[]>([]);
  const [deliverables, setDeliverables] = useState<DeliverablesState>({});
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const [savedCloudIds, setSavedCloudIds] = useState<string[]>([]);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState<'signin' | 'signup'>('signin');

  // Projects come from Firestore only — no local mock projects
  const combinedProjects = cloudProjects;

  const addToast = (title: string, message: string, type: 'success' | 'info' | 'error' = 'info') => {
    const id = `toast-${Date.now()}-${Math.random()}`;
    setToasts((prev) => [...prev, { id, title, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4500);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  // Quick Start from Dashboard Drop/Paste — real user content only
  const handleQuickStartUpload = (partial: Partial<SourceFile>) => {
    setCurrentProjectId(`proj-${Date.now()}`);
    setSource({
      id: `src-${Date.now()}`,
      name: partial.name || 'Untitled_Source.txt',
      type: partial.type || 'TEXT',
      size: partial.size || '0 KB',
      status: 'ready',
      uploadedAt: new Date().toISOString(),
      extractedText: partial.extractedText || ''
    });
    // Reset derived state — real analysis runs in the studio
    setAnalysis(null);
    setUckr(null);
    setDeliverables({});
    addToast('Source Ingested', `"${partial.name || 'Untitled_Source.txt'}" ready in transformation studio.`, 'success');
  };

  // Output selection toggling
  const handleToggleOutput = (output: OutputType) => {
    setSelectedOutputs((prev) => {
      if (prev.includes(output)) {
        return prev.filter((o) => o !== output);
      } else {
        return [...prev, output];
      }
    });
  };

  const handleSelectAllOutputs = () => {
    setSelectedOutputs([
      'linkedin',
      'twitter',
      'advisory',
      'executive_summary',
      'infographic',
      'presentation',
      'video'
    ]);
    addToast('All Deliverables Selected', 'All 7 output types enabled.', 'info');
  };

  const handleClearOutputs = () => {
    setSelectedOutputs([]);
  };

  // Start Pipeline — requires a real source
  const handleStartGeneration = () => {
    if (!source) {
      addToast('No Source', 'Upload or paste source content before generating.', 'error');
      return;
    }
    if (selectedOutputs.length === 0) {
      addToast('No Outputs Selected', 'Please select at least one deliverable to generate.', 'error');
      return;
    }
    setCurrentView('generation_pipeline');
  };

  const handlePipelineError = (message: string) => {
    addToast('Generation Failed', message, 'error');
    setCurrentView('new_transformation');
  };

  // Pipeline Completion — real AI results
  const handlePipelineComplete = async (results: PipelineResults) => {
    setDeliverables(results.deliverables);
    if (results.analysis) setAnalysis(results.analysis);
    if (results.uckr) setUckr(results.uckr);
    setCurrentView('results');
    addToast('Deliverables Ready', `Synthesized ${selectedOutputs.length} deliverables from ${source?.name || 'source'}.`, 'success');

    // If user is logged into Firebase, automatically persist the transformation
    if (user && source) {
      const newProjectId = currentProjectId || `proj-${Date.now()}`;
      const projectRecord: TransformationProject = {
        id: newProjectId,
        userId: user.uid,
        title: source.name.replace(/\.[^/.]+$/, '') || 'Untitled Transformation',
        description: `${config.targetAudience} · ${config.tone} · ${selectedOutputs.length} deliverables`,
        source,
        config,
        selectedOutputs,
        analysis: results.analysis || analysis as AIAnalysis,
        uckr: results.uckr || undefined,
        deliverables: results.deliverables,
        status: 'Completed',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
      if (projectRecord.analysis) {
        try {
          const saved = await saveProjectToCloud(projectRecord);
          if (saved) {
            setSavedCloudIds((prev) => [...prev, newProjectId]);
            addToast('Synced to Cloud', 'Transformation saved to your cloud workspace.', 'success');
          } else {
            console.warn('Auto cloud save skipped: persistence unavailable.');
          }
        } catch (err) {
          console.error('Auto cloud save failed:', err);
        }
      }
    }
  };

  // Manual Save to Cloud
  const handleSaveToCloud = async () => {
    if (!user) {
      addToast('Sign In Required', 'Please sign in or create an account to save to the cloud.', 'info');
      setAuthModalMode('signin');
      setIsAuthModalOpen(true);
      return;
    }

    if (!source || !analysis) {
      addToast('Nothing To Save', 'Upload a source and run generation before saving.', 'error');
      return;
    }

    const projectId = currentProjectId || `proj-${Date.now()}`;
    const projectRecord: TransformationProject = {
      id: projectId,
      userId: user.uid,
      title: source.name.replace(/\.[^/.]+$/, '') || 'Untitled Transformation',
      description: `${config.targetAudience} · ${config.tone} · ${selectedOutputs.length} deliverables`,
      source,
      config,
      selectedOutputs,
      analysis,
      uckr: uckr || undefined,
      deliverables,
      status: 'Completed',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    try {
      const success = await saveProjectToCloud(projectRecord);
      if (success) {
        setSavedCloudIds((prev) => [...prev, projectId]);
        addToast('Saved to Cloud', 'Project and deliverables stored in your cloud workspace.', 'success');
      } else {
        addToast('Save Failed', 'Could not store the project. Check that the backend is running and you are signed in.', 'error');
      }
    } catch (err) {
      addToast('Save Failed', 'Could not store the project. Check the backend connection or Firestore permissions.', 'error');
    }
  };

  // Generate a single missing deliverable via real AI
  const handleAddDeliverable = async (type: OutputType) => {
    if (!source) {
      addToast('No Source', 'Upload source content before generating deliverables.', 'error');
      return;
    }
    if (!selectedOutputs.includes(type)) {
      setSelectedOutputs((prev) => [...prev, type]);
    }
    try {
      const fresh = await generateDeliverables(source, config, [type], analysis, uckr);
      setDeliverables((prev) => ({ ...prev, ...fresh }));
      addToast('Deliverable Synthesized', `Generated ${type.replace('_', ' ')} from your source.`, 'success');
    } catch (err) {
      addToast('Generation Failed', err instanceof Error ? err.message : 'Could not generate deliverable.', 'error');
    }
  };

  // Publish to platform — queued until backend publishing is connected
  const handlePublishMcp = (platformName: string) => {
    addToast(
      `Queued for ${platformName}`,
      `Publish request noted. Dispatch waits for backend integration.`,
      'info'
    );
  };

  // Project select — Firestore records only
  const handleSelectProject = (project: ProjectRecord) => {
    setCurrentProjectId(project.id);
    setSource(project.source || null);
    setConfig(project.config || DEFAULT_CONFIG);
    setSelectedOutputs(project.selectedOutputs || []);
    setAnalysis(project.analysis || null);
    setUckr(project.uckr || null);
    setDeliverables(project.deliverables || {});
    setCurrentView('results');
    addToast('Project Loaded', `Opened workspace for "${project.title}".`, 'info');
  };

  // Delete project — Firestore only
  const handleDeleteProject = async (projectId: string) => {
    if (user && cloudProjects.some((p) => p.id === projectId)) {
      try {
        await deleteProjectFromCloud(projectId);
        addToast('Project Deleted', 'Project removed from your cloud workspace.', 'info');
      } catch (err) {
        addToast('Delete Failed', 'Could not delete project from Firestore.', 'error');
      }
    } else {
      addToast('Sign In Required', 'Projects are stored in your cloud workspace. Sign in to manage them.', 'info');
    }
  };

  const isCurrentSaved = user ? savedCloudIds.includes(currentProjectId) || cloudProjects.some((p) => p.id === currentProjectId) : false;

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col font-sans antialiased selection:bg-purple-600 selection:text-white">
      {/* Toast Notification Container */}
      <ToastContainer toasts={toasts} onDismiss={removeToast} />

      {/* Persistent Left Sidebar */}
      <Sidebar
        currentView={currentView}
        onNavigate={setCurrentView}
        isOpenMobile={isMobileSidebarOpen}
        onCloseMobile={() => setIsMobileSidebarOpen(false)}
        outputsCount={selectedOutputs.length}
      />

      {/* Main Workspace Frame */}
      <div className="lg:pl-72 flex-1 flex flex-col min-w-0">
        {/* Sticky Clean TopBar */}
        <TopBar
          currentView={currentView}
          onNavigate={setCurrentView}
          onOpenMobileSidebar={() => setIsMobileSidebarOpen(true)}
          onOpenAuthModal={(mode) => {
            setAuthModalMode(mode);
            setIsAuthModalOpen(true);
          }}
        />

        {/* Sign In & Sign Up Modal */}
        <AuthModal
          isOpen={isAuthModalOpen}
          onClose={() => setIsAuthModalOpen(false)}
          initialMode={authModalMode}
          onSuccess={(msg) => addToast('Authentication', msg, 'success')}
        />

        {/* Dynamic Page Router */}
        <main className="flex-1 px-4 sm:px-6 lg:px-10 py-6 max-w-7xl w-full mx-auto">
          {currentView === 'dashboard' && (
            <DashboardView
              onNavigate={setCurrentView}
              onQuickStartUpload={handleQuickStartUpload}
            />
          )}

          {currentView === 'new_transformation' && (
            <NewTransformationView
              source={source}
              config={config}
              selectedOutputs={selectedOutputs}
              analysis={analysis}
              uckr={uckr}
              onUpdateSource={setSource}
              onUpdateConfig={setConfig}
              onUpdateAnalysis={setAnalysis}
              onUpdateUckr={setUckr}
              onToggleOutput={handleToggleOutput}
              onSelectAllOutputs={handleSelectAllOutputs}
              onClearOutputs={handleClearOutputs}
              onStartGeneration={handleStartGeneration}
              onShowToast={addToast}
            />
          )}

          {currentView === 'generation_pipeline' && (
            <GenerationPipelineView
              selectedOutputs={selectedOutputs}
              sourceName={source?.name || 'Untitled source'}
              source={source}
              config={config}
              analysis={analysis}
              uckr={uckr}
              onComplete={handlePipelineComplete}
              onError={handlePipelineError}
            />
          )}

          {currentView === 'results' && (
            <ResultsWorkspaceView
              source={source}
              config={config}
              selectedOutputs={selectedOutputs}
              deliverables={deliverables}
              uckr={uckr}
              onUpdateDeliverables={setDeliverables}
              onNavigateNew={() => setCurrentView('new_transformation')}
              onAddDeliverable={handleAddDeliverable}
              onPublishMcp={handlePublishMcp}
              onShowToast={addToast}
              onSaveToCloud={handleSaveToCloud}
              isSavedToCloud={isCurrentSaved}
              isSavingToCloud={isSyncing}
            />
          )}

          {currentView === 'projects' && (
            <ProjectsView
              projects={combinedProjects}
              onSelectProject={handleSelectProject}
              onNewTransformation={() => setCurrentView('new_transformation')}
              onDeleteProject={handleDeleteProject}
            />
          )}

          {currentView === 'outputs' && (
            <OutputsView
              deliverables={deliverables}
              onOpenResults={(filter) => {
                if (filter && !selectedOutputs.includes(filter)) {
                  setSelectedOutputs((prev) => [...prev, filter]);
                }
                setCurrentView('results');
              }}
              onShowToast={addToast}
            />
          )}

          {currentView === 'uckr' && (
            <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
              {uckr ? (
                <UckrPanel
                  uckr={uckr}
                  sourceDocTitle={source?.name || 'No source loaded'}
                />
              ) : (
                <div className="p-12 rounded-2xl border border-dashed border-slate-800 text-center space-y-3 bg-slate-900/30">
                  <h2 className="text-lg font-bold text-white">No knowledge base yet</h2>
                  <p className="text-sm text-slate-400 max-w-md mx-auto">
                    Upload a source and run a transformation to build the Unified Content Knowledge Representation.
                  </p>
                  <button
                    onClick={() => setCurrentView('new_transformation')}
                    className="px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-sm font-semibold cursor-pointer"
                  >
                    Start a Transformation
                  </button>
                </div>
              )}
            </div>
          )}

          {currentView === 'agents' && <AgentsView />}

          {currentView === 'mcp' && <McpView onShowToast={addToast} />}

          {currentView === 'settings' && (
            <SettingsView
              config={config}
              onUpdateConfig={setConfig}
              onShowToast={addToast}
            />
          )}
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <FirebaseProvider>
      <AppContent />
    </FirebaseProvider>
  );
}
