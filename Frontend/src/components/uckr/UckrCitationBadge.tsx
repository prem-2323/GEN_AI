import React, { useState } from 'react';
import { Database, Eye, ShieldCheck, AlertTriangle, XCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { UckrFact, OutputType, DeliverableValidationResult } from '../../types';
import { SourceGroundingModal } from './SourceGroundingModal';

interface UckrCitationBadgeProps {
  deliverableType: OutputType;
  facts: UckrFact[];
  validation?: DeliverableValidationResult | null;
}

export const UckrCitationBadge: React.FC<UckrCitationBadgeProps> = ({ deliverableType, facts, validation }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [activeFact, setActiveFact] = useState<UckrFact | null>(null);

  // Filter facts used in this deliverable (or top relevant)
  const relevantFacts = facts.filter((f) => f.usedInDeliverables?.includes(deliverableType));
  const displayFacts = relevantFacts.length > 0 ? relevantFacts : facts;

  const status = validation?.status || 'verified';
  const unsupportedList = [
    ...(validation?.unsupportedMetrics || []),
    ...(validation?.unsupportedClaims || []),
  ];

  return (
    <div className="rounded-xl bg-purple-950/20 border border-purple-500/25 p-3 space-y-2.5 my-2">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          {status === 'verified' ? (
            <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
              <ShieldCheck className="w-3 h-3 text-emerald-400" />
              <span>✓ UCKR Verified</span>
            </span>
          ) : status === 'needs_review' ? (
            <span className="inline-flex items-center gap-1 text-[11px] font-bold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/20">
              <AlertTriangle className="w-3 h-3 text-amber-400" />
              <span>⚠ Review Required ({unsupportedList.length} warning{unsupportedList.length > 1 ? 's' : ''})</span>
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 text-[11px] font-bold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded-full border border-rose-500/20">
              <XCircle className="w-3 h-3 text-rose-400" />
              <span>✕ Validation Failed</span>
            </span>
          )}

          <span className="text-[11px] text-slate-400 font-mono">
            Grounding: {validation?.groundingScore ?? 100}% · {displayFacts.length} verified facts
          </span>
        </div>

        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-[11px] font-medium text-purple-300 hover:text-white flex items-center gap-1 cursor-pointer transition-colors"
        >
          <Database className="w-3 h-3 text-purple-400" />
          <span>Used knowledge citations</span>
          {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        </button>
      </div>

      {/* Unsupported Claims Banner if any */}
      {unsupportedList.length > 0 && (
        <div className="p-2.5 rounded-lg bg-amber-950/40 border border-amber-500/40 text-xs text-amber-200 space-y-1">
          <div className="font-semibold flex items-center gap-1.5 text-amber-300">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
            <span>Unsupported claims or metrics detected:</span>
          </div>
          <ul className="list-disc pl-5 space-y-0.5 text-[11px]">
            {unsupportedList.map((item, idx) => (
              <li key={idx}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Citations Pill Bar */}
      <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
        {displayFacts.slice(0, isExpanded ? displayFacts.length : 4).map((fact) => (
          <button
            key={fact.id}
            onClick={() => setActiveFact(fact)}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900/90 border border-slate-700/80 hover:border-purple-500 text-slate-300 hover:text-white text-[11px] font-mono transition-colors cursor-pointer group"
            title="Click to view source grounding quote and page"
          >
            <span className="text-purple-400 font-bold group-hover:text-purple-300">{fact.id}</span>
            <span className="text-slate-400 max-w-[170px] truncate text-[10px]">{fact.value}</span>
            <Eye className="w-3 h-3 text-slate-500 group-hover:text-purple-400" />
          </button>
        ))}

        {!isExpanded && displayFacts.length > 4 && (
          <button
            onClick={() => setIsExpanded(true)}
            className="text-[11px] text-purple-400 hover:text-purple-300 font-mono underline ml-1 cursor-pointer"
          >
            +{displayFacts.length - 4} more facts
          </button>
        )}
      </div>

      {/* Modal for source inspection */}
      <SourceGroundingModal
        fact={activeFact}
        onClose={() => setActiveFact(null)}
      />
    </div>
  );
};
