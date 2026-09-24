import React, { useState } from 'react';
import { 
  Layers, 
  Search, 
  Copy, 
  Check, 
  ExternalLink, 
  Download, 
  Linkedin, 
  Twitter, 
  Bell, 
  BarChart3, 
  Presentation, 
  Video, 
  FileCheck,
  CheckCircle2
} from 'lucide-react';
import { OutputType, DeliverablesState } from '../../types';
import { StatusBadge } from '../common/StatusBadge';

interface OutputsViewProps {
  deliverables: DeliverablesState;
  onOpenResults: (filter?: OutputType) => void;
  onShowToast: (title: string, message: string, type?: 'success' | 'info' | 'error') => void;
}

export const OutputsView: React.FC<OutputsViewProps> = ({
  deliverables,
  onOpenResults,
  onShowToast
}) => {
  const [selectedType, setSelectedType] = useState<string>('all');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const hasAny = Object.keys(deliverables || {}).length > 0;
  const outputsList = [
    {
      id: 'linkedin',
      type: 'LinkedIn Post',
      icon: Linkedin,
      title: deliverables.linkedin ? 'LinkedIn Post ready' : 'LinkedIn Post — not generated',
      summary: deliverables.linkedin?.hook || 'No content yet — run a transformation to generate.',
      fullText: deliverables.linkedin ? `${deliverables.linkedin.hook}\n\n${deliverables.linkedin.body}` : '',
      status: 'ready' as const,
      timestamp: deliverables.linkedin ? 'Generated' : 'Empty',
      generated: Boolean(deliverables.linkedin)
    },
    {
      id: 'twitter',
      type: 'Twitter / X Thread',
      icon: Twitter,
      title: deliverables.twitter ? 'X Thread ready' : 'X Thread — not generated',
      summary: deliverables.twitter?.singlePost || 'No content yet — run a transformation to generate.',
      fullText: deliverables.twitter ? deliverables.twitter.thread.map((t: { text: string }) => t.text).join('\n\n') : '',
      status: 'ready' as const,
      timestamp: deliverables.twitter ? 'Generated' : 'Empty',
      generated: Boolean(deliverables.twitter)
    },
    {
      id: 'advisory',
      type: 'Advisory & Policy Brief',
      icon: Bell,
      title: deliverables.advisory?.title || 'Advisory — not generated',
      summary: deliverables.advisory?.situation || 'No content yet — run a transformation to generate.',
      fullText: deliverables.advisory?.situation || '',
      status: 'ready' as const,
      timestamp: deliverables.advisory ? 'Generated' : 'Empty',
      generated: Boolean(deliverables.advisory)
    },
    {
      id: 'infographic',
      type: 'Infographic Package',
      icon: BarChart3,
      title: deliverables.infographic?.keyMessage || 'Infographic — not generated',
      summary: deliverables.infographic?.keyMessage || 'No content yet — run a transformation to generate.',
      fullText: deliverables.infographic?.keyMessage || '',
      status: 'ready' as const,
      timestamp: deliverables.infographic ? 'Generated' : 'Empty',
      generated: Boolean(deliverables.infographic)
    },
    {
      id: 'executive_summary',
      type: 'Executive Summary',
      icon: FileCheck,
      title: 'Executive Summary',
      summary: deliverables.executive_summary?.executiveOverview || 'No content yet — run a transformation to generate.',
      fullText: deliverables.executive_summary?.executiveOverview || '',
      status: 'ready' as const,
      timestamp: deliverables.executive_summary ? 'Generated' : 'Empty',
      generated: Boolean(deliverables.executive_summary)
    },
    {
      id: 'presentation',
      type: 'Presentation Deck',
      icon: Presentation,
      title: deliverables.presentation?.deckTitle || 'Presentation — not generated',
      summary: deliverables.presentation ? 'Slide deck with speaker notes.' : 'No content yet — run a transformation to generate.',
      fullText: deliverables.presentation?.deckTitle || '',
      status: 'ready' as const,
      timestamp: deliverables.presentation ? 'Generated' : 'Empty',
      generated: Boolean(deliverables.presentation)
    },
    {
      id: 'video',
      type: 'Video Package',
      icon: Video,
      title: deliverables.video?.title || 'Video — not generated',
      summary: 'No content yet — run a transformation to generate.',
      fullText: deliverables.video?.script || '',
      status: 'ready' as const,
      timestamp: deliverables.video ? 'Generated' : 'Empty',
      generated: Boolean(deliverables.video)
    }
  ];

  const filtered = selectedType === 'all' 
    ? outputsList 
    : outputsList.filter(o => o.id === selectedType);

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    onShowToast('Copied', 'Output text copied to clipboard.', 'success');
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-purple-400 uppercase tracking-wider mb-1">
            <Layers className="w-4 h-4" />
            <span>Asset Library</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Generated Outputs
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Cross-channel deliverables synthesized from your source materials.
          </p>
          {!hasAny && (
            <p className="text-xs text-amber-300 mt-2">No outputs generated yet — upload a source and run a transformation.</p>
          )}
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2">
        <button
          onClick={() => setSelectedType('all')}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-colors cursor-pointer ${
            selectedType === 'all'
              ? 'bg-purple-600 text-white'
              : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-white'
          }`}
        >
          All Formats ({outputsList.length})
        </button>

        {outputsList.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              onClick={() => setSelectedType(item.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors cursor-pointer ${
                selectedType === item.id
                  ? 'bg-purple-600 text-white'
                  : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{item.type}</span>
            </button>
          );
        })}
      </div>

      {/* Outputs List Table / Cards */}
      <div className="space-y-3">
        {filtered.map((item) => {
          const Icon = item.icon;
          const isCopied = copiedId === item.id;

          return (
            <div
              key={item.id}
              className="p-5 rounded-xl border border-slate-800 bg-[#0d121f] hover:border-slate-700 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-4"
            >
              <div className="flex items-start gap-3.5 min-w-0 flex-1">
                <div className="w-10 h-10 rounded-xl bg-purple-500/15 border border-purple-500/30 flex items-center justify-center text-purple-400 shrink-0">
                  <Icon className="w-5 h-5" />
                </div>

                <div className="min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-xs font-semibold text-purple-300">
                      {item.type}
                    </span>
                    {item.generated ? (
                      <StatusBadge status={item.status} size="xs" />
                    ) : (
                      <span className="text-[10px] font-mono font-semibold text-slate-500 uppercase">Not generated</span>
                    )}
                  </div>

                  <h3 className="text-sm font-bold text-white truncate">
                    {item.title}
                  </h3>

                  <p className="text-xs text-slate-400 mt-0.5 line-clamp-1">
                    {item.summary}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0 self-end sm:self-auto">
                <button
                  onClick={() => handleCopy(item.id, item.fullText)}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors cursor-pointer"
                  title="Copy content"
                >
                  {isCopied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{isCopied ? 'Copied' : 'Copy'}</span>
                </button>

                <button
                  onClick={() => onOpenResults(item.id as OutputType)}
                  className="flex items-center gap-1 px-3.5 py-1.5 rounded-lg bg-purple-600/20 hover:bg-purple-600/30 border border-purple-500/40 text-purple-300 text-xs font-semibold transition-colors cursor-pointer"
                >
                  <span>Open in Workspace</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
