import React, { useState } from 'react';
import { Database, Eye, ShieldCheck, ChevronDown, ChevronUp } from 'lucide-react';
import { UckrFact, OutputType } from '../../types';
import { SourceGroundingModal } from './SourceGroundingModal';

interface UckrCitationBadgeProps {
  deliverableType: OutputType;
  facts: UckrFact[];
}

export const UckrCitationBadge: React.FC<UckrCitationBadgeProps> = ({ deliverableType, facts }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [activeFact, setActiveFact] = useState<UckrFact | null>(null);

  // Filter facts used in this deliverable (or top relevant)
  const relevantFacts = facts.filter(f => f.usedInDeliverables?.includes(deliverableType));
  const displayFacts = relevantFacts.length > 0 ? relevantFacts : facts.slice(0, 4);

  return (
    <div className="rounded-xl bg-purple-950/20 border border-purple-500/25 p-3 space-y-2 my-2">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
            <ShieldCheck className="w-3 h-3 text-emerald-400" />
            <span>✓ UCKR Verified</span>
          </span>
          <span className="text-[11px] text-slate-400 font-mono">
            Powered by {displayFacts.length} verified facts
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

      {/* Citations Pill Bar */}
      <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
        {displayFacts.slice(0, isExpanded ? displayFacts.length : 3).map((fact) => (
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

        {!isExpanded && displayFacts.length > 3 && (
          <button
            onClick={() => setIsExpanded(true)}
            className="text-[11px] text-purple-400 hover:text-purple-300 font-mono underline ml-1 cursor-pointer"
          >
            +{displayFacts.length - 3} more facts
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
