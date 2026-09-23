import React from 'react';
import { X, FileText, CheckCircle2, ShieldCheck, ExternalLink, Bookmark, Hash } from 'lucide-react';
import { UckrFact } from '../../types';

interface SourceGroundingModalProps {
  fact: UckrFact | null;
  onClose: () => void;
}

export const SourceGroundingModal: React.FC<SourceGroundingModalProps> = ({ fact, onClose }) => {
  if (!fact) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div 
        className="w-full max-w-xl rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-purple-500/15 border border-purple-500/30 flex items-center justify-center text-purple-400">
              <Bookmark className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30">
                  {fact.id}
                </span>
                <span className="text-xs font-medium text-slate-400">Source Grounding Trace</span>
              </div>
              <h3 className="text-sm font-bold text-white mt-0.5">Verified Fact Provenance</h3>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-5 overflow-y-auto">
          {/* Fact Statement */}
          <div className="space-y-1.5">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Extracted Knowledge Fact
            </span>
            <div className="p-3.5 rounded-xl bg-slate-800/80 border border-slate-700/80 text-sm font-medium text-slate-100 leading-relaxed">
              "{fact.value}"
            </div>
          </div>

          {/* Verbatim Source Quote */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-purple-400 uppercase tracking-wider flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5" />
                Verbatim Source Excerpt
              </span>
              <span className="text-[11px] text-emerald-400 font-medium flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> {(fact.confidence * 100).toFixed(0)}% Match
              </span>
            </div>
            <div className="p-4 rounded-xl bg-purple-950/20 border border-purple-500/30 text-xs sm:text-sm text-purple-100/90 font-mono leading-relaxed relative">
              <div className="absolute top-2 right-2 text-purple-500/20 font-serif text-4xl select-none">“</div>
              <p className="italic relative z-10">"{fact.quote}"</p>
            </div>
          </div>

          {/* Location & Metadata Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
              <div className="text-[10px] text-slate-400 uppercase font-semibold">Document</div>
              <div className="text-xs font-semibold text-white truncate mt-1" title={fact.sourceDoc}>
                {fact.sourceDoc}
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
              <div className="text-[10px] text-slate-400 uppercase font-semibold">Page Number</div>
              <div className="text-xs font-semibold text-emerald-400 font-mono mt-1 flex items-center gap-1">
                <Hash className="w-3 h-3 text-emerald-400" />
                Page {fact.page}
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
              <div className="text-[10px] text-slate-400 uppercase font-semibold">Section</div>
              <div className="text-xs font-semibold text-slate-200 truncate mt-1" title={fact.section}>
                {fact.section}
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
              <div className="text-[10px] text-slate-400 uppercase font-semibold">Confidence</div>
              <div className="text-xs font-semibold text-purple-400 font-mono mt-1">
                {(fact.confidence * 100).toFixed(0)}% Match
              </div>
            </div>
          </div>

          {/* Deliverables using this fact */}
          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Deliverables Powered by this Fact:
            </div>
            <div className="flex flex-wrap gap-1.5">
              {fact.usedInDeliverables?.map((delId) => (
                <span 
                  key={delId}
                  className="px-2.5 py-1 rounded-md bg-purple-500/10 text-purple-300 border border-purple-500/20 text-xs font-medium capitalize"
                >
                  {delId.replace('_', ' ')}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between">
          <span className="text-xs text-slate-400 flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            Verified against source file without hallucination
          </span>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold transition-colors cursor-pointer"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};
