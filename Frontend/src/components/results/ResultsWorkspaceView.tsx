import React, { useState } from 'react';
import { 
  FileText, 
  Download, 
  Share2, 
  Sparkles, 
  RotateCw, 
  ArrowLeft, 
  Layers, 
  CheckCircle2, 
  SlidersHorizontal,
  Search,
  ExternalLink,
  Plus,
  Send,
  Linkedin,
  Twitter,
  Bell,
  BarChart3,
  Presentation,
  Video,
  FileCheck,
  Cloud,
  Check,
  Loader2,
  ShieldCheck,
  Database,
  AlertTriangle
} from 'lucide-react';
import {
  SourceFile,
  TransformationConfig,
  OutputType,
  DeliverablesState,
  UckrKnowledgeBase
} from '../../types';
import { LinkedInCard } from './deliverables/LinkedInCard';
import { TwitterCard } from './deliverables/TwitterCard';
import { AdvisoryCard } from './deliverables/AdvisoryCard';
import { ExecutiveSummaryCard } from './deliverables/ExecutiveSummaryCard';
import { InfographicCard } from './deliverables/InfographicCard';
import { PresentationCard } from './deliverables/PresentationCard';
import { VideoPackageCard } from './deliverables/VideoPackageCard';
import { StatusBadge } from '../common/StatusBadge';
import { UckrCitationBadge } from '../uckr/UckrCitationBadge';

interface ResultsWorkspaceViewProps {
  source: SourceFile | null;
  config: TransformationConfig;
  selectedOutputs: OutputType[];
  deliverables: DeliverablesState;
  uckr?: UckrKnowledgeBase | null;
  onUpdateDeliverables: (updated: DeliverablesState) => void;
  onNavigateNew: () => void;
  onAddDeliverable: (type: OutputType) => void;
  onPublishMcp: (deliverableType: string) => void;
  onShowToast: (title: string, message: string, type?: 'success' | 'info' | 'error') => void;
  onSaveToCloud?: () => void;
  isSavedToCloud?: boolean;
  isSavingToCloud?: boolean;
}

export const ResultsWorkspaceView: React.FC<ResultsWorkspaceViewProps> = ({
  source,
  config,
  selectedOutputs,
  deliverables,
  uckr,
  onUpdateDeliverables,
  onNavigateNew,
  onAddDeliverable,
  onPublishMcp,
  onShowToast,
  onSaveToCloud,
  isSavedToCloud,
  isSavingToCloud
}) => {
  const [activeFilter, setActiveFilter] = useState<'all' | OutputType>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const activeUckr = uckr;
  const facts = activeUckr?.facts || [];
  const grounding = activeUckr?.stats.grounding || 0;

  // Consistency checkpoints are derived from real UCKR stats — no hardcoded claims
  const checkpoints = activeUckr
    ? [
        { label: 'Facts preserved', detail: `${activeUckr.stats.totalFacts} verified`, ok: activeUckr.stats.totalFacts > 0 },
        { label: 'Numbers consistent', detail: `${activeUckr.stats.totalMetrics} metrics`, ok: activeUckr.stats.totalMetrics > 0 },
        { label: 'Entities consistent', detail: `${activeUckr.stats.totalEntities} resolved`, ok: activeUckr.stats.totalEntities > 0 },
        { label: 'Dates consistent', detail: `${activeUckr.stats.totalEvents} timeline nodes`, ok: activeUckr.stats.totalEvents > 0 },
        { label: 'Knowledge graph', detail: `${activeUckr.stats.totalRelationships} relations`, ok: activeUckr.stats.totalRelationships > 0 }
      ]
    : [];

  if (!source) {
    return (
      <div className="p-12 rounded-2xl border border-dashed border-slate-800 text-center space-y-3 bg-slate-900/30">
        <h2 className="text-lg font-bold text-white">No transformation yet</h2>
        <p className="text-sm text-slate-400 max-w-md mx-auto">Upload a source and run generation to see deliverables here.</p>
        <button onClick={onNavigateNew} className="px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-sm font-semibold cursor-pointer">
          Start a Transformation
        </button>
      </div>
    );
  }

  const allAvailableOutputs: { id: OutputType; label: string; icon: React.ElementType }[] = [
    { id: 'linkedin', label: 'LinkedIn', icon: Linkedin },
    { id: 'twitter', label: 'Twitter / X', icon: Twitter },
    { id: 'advisory', label: 'Advisory & Policy', icon: Bell },
    { id: 'infographic', label: 'Infographic', icon: BarChart3 },
    { id: 'executive_summary', label: 'Executive Summary', icon: FileCheck },
    { id: 'presentation', label: 'Presentation', icon: Presentation },
    { id: 'video', label: 'Video Package', icon: Video },
  ];

  const handleExportAll = () => {
    const fullArchive = {
      project: 'GEN TRANSFORM AI Deliverable Bundle',
      exportedAt: new Date().toISOString(),
      source: {
        name: source.name,
        type: source.type,
        pages: source.pages,
        size: source.size
      },
      configuration: config,
      deliverables: {
        linkedin: deliverables.linkedin,
        twitter: deliverables.twitter,
        advisory: deliverables.advisory,
        executiveSummary: deliverables.executive_summary,
        infographic: deliverables.infographic,
        presentation: deliverables.presentation,
        video: deliverables.video
      }
    };

    const blob = new Blob([JSON.stringify(fullArchive, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `GEN_TRANSFORM_ALL_DELIVERABLES_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    onShowToast('Archive Exported', 'All generated deliverables exported in unified enterprise package.', 'success');
  };

  const handleShareWorkspace = () => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(window.location.href);
      onShowToast('Link Copied', 'Collaborative workspace URL copied to clipboard.', 'info');
    }
  };

  return (
    <div className="space-y-8 pb-24">
      {/* Workspace Header */}
      <div className="rounded-2xl border border-slate-800 bg-gradient-to-b from-[#12192a] via-[#0d1322] to-[#0b0f17] p-6 lg:p-8 shadow-xl space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
          <div className="flex items-start gap-4">
            <button
              onClick={onNavigateNew}
              className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white transition-colors shrink-0 cursor-pointer"
              title="Return to Transformation Studio"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>

            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs uppercase font-semibold text-purple-400">
                  Transformation Results Workspace
                </span>
                <StatusBadge status="ready" size="xs" />
              </div>

              <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight flex items-center gap-2">
                <span>{source.name}</span>
              </h1>

              <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 mt-1.5">
                <span>Type: <strong className="text-slate-200 font-normal">{source.type}</strong></span>
                <span>·</span>
                {source.pages && <span>{source.pages} pages ·</span>}
                <span>{source.size}</span>
                <span>·</span>
                <span>Audience: <strong className="text-purple-300 font-normal">{config.targetAudience}</strong></span>
                <span>·</span>
                <span>Tone: <strong className="text-purple-300 font-normal">{config.tone}</strong></span>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            <button
              onClick={onNavigateNew}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white text-xs font-semibold transition-colors cursor-pointer"
            >
              <RotateCw className="w-3.5 h-3.5" />
              <span>Re-transform</span>
            </button>

            <button
              onClick={handleShareWorkspace}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white text-xs font-semibold transition-colors cursor-pointer"
            >
              <Share2 className="w-3.5 h-3.5" />
              <span>Share</span>
            </button>

            {onSaveToCloud && (
              <button
                onClick={onSaveToCloud}
                disabled={isSavingToCloud}
                className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold border transition-all cursor-pointer ${
                  isSavedToCloud
                    ? 'bg-amber-950/40 border-amber-500/50 text-amber-300'
                    : 'bg-slate-800 hover:bg-slate-700 border-slate-700 text-slate-200 hover:text-white'
                }`}
                title="Persist this transformation and deliverables to Firebase Firestore"
              >
                {isSavingToCloud ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-400" />
                ) : isSavedToCloud ? (
                  <Check className="w-3.5 h-3.5 text-amber-400" />
                ) : (
                  <Cloud className="w-3.5 h-3.5 text-amber-400" />
                )}
                <span>{isSavingToCloud ? 'Saving...' : isSavedToCloud ? 'Saved to Cloud' : 'Save to Firebase'}</span>
              </button>
            )}

            <button
              onClick={handleExportAll}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-semibold shadow-lg shadow-purple-600/25 transition-all cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export All Deliverables</span>
            </button>
          </div>
        </div>

        {/* UCKR Cross-Deliverable Consistency Card */}
        {!activeUckr ? (
          <div className="p-5 rounded-2xl border border-dashed border-slate-800 bg-slate-900/40 text-center">
            <p className="text-xs font-semibold text-white uppercase tracking-wider">UCKR consistency unavailable</p>
            <p className="text-xs text-slate-400 mt-1">No verified knowledge base for this transformation yet. Outputs are generated directly from source analysis.</p>
          </div>
        ) : (
        <div className="p-5 sm:p-6 rounded-2xl bg-gradient-to-br from-[#0d121f] via-purple-950/20 to-slate-900 border border-purple-500/30 shadow-xl space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shrink-0">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-bold text-white uppercase tracking-wider">
                    UCKR CONSISTENCY VALIDATION
                  </h2>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                    grounding > 0
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                      : 'bg-slate-800/60 text-slate-400 border-slate-700'
                  }`}>
                    {grounding > 0 ? 'GROUNDING REPORTED' : 'GROUNDING PENDING'}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-0.5">
                  Unified Content Knowledge Representation linked to {selectedOutputs.length} generated deliverables
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3 self-start sm:self-auto">
              <div className="text-right">
                <div className="text-2xl font-bold font-mono text-emerald-400">{grounding}%</div>
                <div className="text-[10px] text-slate-400 uppercase tracking-wider font-mono">Grounding Index</div>
              </div>
            </div>
          </div>

          {/* Consistency Progress Bar */}
          <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
            <div
              className="h-full bg-gradient-to-r from-purple-500 via-indigo-500 to-emerald-400 rounded-full"
              style={{ width: `${grounding}%` }}
            />
          </div>

          {/* Data-driven consistency checkpoints */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-1 text-xs">
            {checkpoints.map((cp) => (
              <div
                key={cp.label}
                className={`flex items-center gap-2 p-2.5 rounded-xl bg-slate-900/80 border last:col-span-2 sm:last:col-span-1 ${
                  cp.ok ? 'border-slate-800/80' : 'border-amber-500/30'
                }`}
              >
                {cp.ok ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                )}
                <div>
                  <div className="font-semibold text-white">{cp.label}</div>
                  <div className="text-[11px] text-slate-400 font-mono">{cp.detail}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
        )}

        {/* Filter Navigation Tabs */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 max-w-full">
            <button
              onClick={() => setActiveFilter('all')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-colors cursor-pointer ${
                activeFilter === 'all'
                  ? 'bg-purple-600 text-white shadow-sm'
                  : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
              }`}
            >
              All Deliverables ({selectedOutputs.length})
            </button>

            {allAvailableOutputs.map((out) => {
              const isSelected = selectedOutputs.includes(out.id);
              const isActive = activeFilter === out.id;
              const Icon = out.icon;

              return (
                <button
                  key={out.id}
                  onClick={() => setActiveFilter(out.id)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors cursor-pointer ${
                    isActive
                      ? 'bg-purple-600 text-white shadow-sm'
                      : isSelected
                        ? 'bg-slate-900 text-slate-200 border border-slate-800 hover:border-slate-700'
                        : 'bg-slate-950/60 text-slate-500 border border-slate-900 hover:text-slate-400'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{out.label}</span>
                  {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />}
                </button>
              );
            })}
          </div>

          <div className="flex items-center gap-2">
            <div className="relative">
              <input
                type="text"
                placeholder="Filter output content..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="rounded-lg bg-slate-900 border border-slate-800 px-3 py-1.5 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-purple-500 w-48"
              />
              <Search className="w-3.5 h-3.5 text-slate-500 absolute right-2.5 top-2.5 pointer-events-none" />
            </div>
          </div>
        </div>
      </div>

      {/* Deliverables Stack */}
      <div className="space-y-8">
        {/* 1. LinkedIn */}
        {(activeFilter === 'all' || activeFilter === 'linkedin') && (
          selectedOutputs.includes('linkedin') ? (
            deliverables.linkedin && (
              <div className="space-y-2">
                <UckrCitationBadge deliverableType="linkedin" facts={facts} />
                <LinkedInCard
                  deliverable={deliverables.linkedin}
                  onUpdate={(up) => onUpdateDeliverables({ ...deliverables, linkedin: up })}
                  onPublishToMcp={() => onPublishMcp('LinkedIn')}
                  onShowToast={onShowToast}
                />
              </div>
            )
          ) : activeFilter === 'linkedin' ? (
            <div className="p-8 rounded-2xl border border-dashed border-slate-800 text-center space-y-3 bg-slate-900/30">
              <Linkedin className="w-8 h-8 text-slate-600 mx-auto" />
              <h3 className="text-base font-bold text-white">LinkedIn Post not in current selection</h3>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                Generate a professional publication-ready post optimized for thought leadership.
              </p>
              <button
                onClick={() => onAddDeliverable('linkedin')}
                className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold cursor-pointer"
              >
                + Generate LinkedIn Deliverable
              </button>
            </div>
          ) : null
        )}

        {/* 2. Twitter / X */}
        {(activeFilter === 'all' || activeFilter === 'twitter') && (
          selectedOutputs.includes('twitter') ? (
            deliverables.twitter && (
              <div className="space-y-2">
                <UckrCitationBadge deliverableType="twitter" facts={facts} />
                <TwitterCard
                  deliverable={deliverables.twitter}
                  onUpdate={(up) => onUpdateDeliverables({ ...deliverables, twitter: up })}
                  onPublishToMcp={() => onPublishMcp('X')}
                  onShowToast={onShowToast}
                />
              </div>
            )
          ) : activeFilter === 'twitter' ? (
            <div className="p-8 rounded-2xl border border-dashed border-slate-800 text-center space-y-3 bg-slate-900/30">
              <Twitter className="w-8 h-8 text-slate-600 mx-auto" />
              <h3 className="text-base font-bold text-white">Twitter / X not generated</h3>
              <button
                onClick={() => onAddDeliverable('twitter')}
                className="px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold cursor-pointer"
              >
                + Generate Twitter / X Deliverable
              </button>
            </div>
          ) : null
        )}

        {/* 3. Advisory */}
        {(activeFilter === 'all' || activeFilter === 'advisory') && (
          selectedOutputs.includes('advisory') ? (
            deliverables.advisory && (
              <div className="space-y-2">
                <UckrCitationBadge deliverableType="advisory" facts={facts} />
                <AdvisoryCard
                  deliverable={deliverables.advisory}
                  onUpdate={(up) => onUpdateDeliverables({ ...deliverables, advisory: up })}
                  onShowToast={onShowToast}
                />
              </div>
            )
          ) : activeFilter === 'advisory' ? (
            <div className="p-8 rounded-2xl border border-dashed border-slate-800 text-center space-y-3 bg-slate-900/30">
              <Bell className="w-8 h-8 text-slate-600 mx-auto" />
              <h3 className="text-base font-bold text-white">Advisory & Policy Brief not generated</h3>
              <button
                onClick={() => onAddDeliverable('advisory')}
                className="px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold cursor-pointer"
              >
                + Generate Advisory Deliverable
              </button>
            </div>
          ) : null
        )}

        {/* 4. Infographic */}
        {(activeFilter === 'all' || activeFilter === 'infographic') && (
          selectedOutputs.includes('infographic') ? (
            deliverables.infographic && (
              <div className="space-y-2">
                <UckrCitationBadge deliverableType="infographic" facts={facts} />
                <InfographicCard
                  deliverable={deliverables.infographic}
                  onUpdate={(up) => onUpdateDeliverables({ ...deliverables, infographic: up })}
                  onShowToast={onShowToast}
                />
              </div>
            )
          ) : activeFilter === 'infographic' ? (
            <div className="p-8 rounded-2xl border border-dashed border-slate-800 text-center space-y-3 bg-slate-900/30">
              <BarChart3 className="w-8 h-8 text-slate-600 mx-auto" />
              <h3 className="text-base font-bold text-white">Infographic Package not generated</h3>
              <button
                onClick={() => onAddDeliverable('infographic')}
                className="px-4 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold cursor-pointer"
              >
                + Generate Infographic Deliverable
              </button>
            </div>
          ) : null
        )}

        {/* 5. Executive Summary */}
        {(activeFilter === 'all' || activeFilter === 'executive_summary') && (
          selectedOutputs.includes('executive_summary') ? (
            deliverables.executive_summary && (
              <div className="space-y-2">
                <UckrCitationBadge deliverableType="executive_summary" facts={facts} />
                <ExecutiveSummaryCard
                  deliverable={deliverables.executive_summary}
                  onUpdate={(up) => onUpdateDeliverables({ ...deliverables, executive_summary: up })}
                  onShowToast={onShowToast}
                />
              </div>
            )
          ) : activeFilter === 'executive_summary' ? (
            <div className="p-8 rounded-2xl border border-dashed border-slate-800 text-center space-y-3 bg-slate-900/30">
              <FileCheck className="w-8 h-8 text-slate-600 mx-auto" />
              <h3 className="text-base font-bold text-white">Executive Summary not generated</h3>
              <button
                onClick={() => onAddDeliverable('executive_summary')}
                className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold cursor-pointer"
              >
                + Generate Executive Summary
              </button>
            </div>
          ) : null
        )}

        {/* 6. Presentation */}
        {(activeFilter === 'all' || activeFilter === 'presentation') && (
          selectedOutputs.includes('presentation') ? (
            deliverables.presentation && (
              <div className="space-y-2">
                <UckrCitationBadge deliverableType="presentation" facts={facts} />
                <PresentationCard
                  deliverable={deliverables.presentation}
                  onUpdate={(up) => onUpdateDeliverables({ ...deliverables, presentation: up })}
                  onShowToast={onShowToast}
                />
              </div>
            )
          ) : activeFilter === 'presentation' ? (
            <div className="p-8 rounded-2xl border border-dashed border-slate-800 text-center space-y-3 bg-slate-900/30">
              <Presentation className="w-8 h-8 text-slate-600 mx-auto" />
              <h3 className="text-base font-bold text-white">Presentation Deck not generated</h3>
              <button
                onClick={() => onAddDeliverable('presentation')}
                className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold cursor-pointer"
              >
                + Generate Presentation Deck
              </button>
            </div>
          ) : null
        )}

        {/* 7. Video Package */}
        {(activeFilter === 'all' || activeFilter === 'video') && (
          selectedOutputs.includes('video') ? (
            deliverables.video && (
              <div className="space-y-2">
                <UckrCitationBadge deliverableType="video" facts={facts} />
                <VideoPackageCard
                  deliverable={deliverables.video}
                  onUpdate={(up) => onUpdateDeliverables({ ...deliverables, video: up })}
                  onShowToast={onShowToast}
                />
              </div>
            )
          ) : activeFilter === 'video' ? (
            <div className="p-8 rounded-2xl border border-dashed border-slate-800 text-center space-y-3 bg-slate-900/30">
              <Video className="w-8 h-8 text-slate-600 mx-auto" />
              <h3 className="text-base font-bold text-white">Video Package not generated</h3>
              <button
                onClick={() => onAddDeliverable('video')}
                className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold cursor-pointer"
              >
                + Generate Video Production Package
              </button>
            </div>
          ) : null
        )}
      </div>
    </div>
  );
};
