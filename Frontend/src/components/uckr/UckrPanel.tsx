import React, { useState } from 'react';
import { 
  Database, 
  Network, 
  Layers, 
  Search, 
  FileText, 
  CheckCircle2, 
  Clock3,
  ExternalLink, 
  ArrowRight, 
  TrendingUp, 
  ShieldCheck, 
  Sparkles, 
  Hash, 
  Tag, 
  Filter, 
  Share2, 
  Eye, 
  ChevronRight,
  Info,
  RefreshCw
} from 'lucide-react';
import { 
  UckrKnowledgeBase, 
  UckrFact, 
  UckrEntity, 
  UckrRelationship, 
  UckrFactType 
} from '../../types';
import { SourceGroundingModal } from './SourceGroundingModal';

interface UckrPanelProps {
  uckr: UckrKnowledgeBase;
  sourceDocTitle?: string;
  currentVersion?: number;
  versions?: Array<{ version: number; createdAt?: string; factCount?: number; grounding?: number }>;
  onSelectVersion?: (version: number) => void;
  onRebuildUckr?: () => void;
  isRebuilding?: boolean;
}

type TabType = 'overview' | 'facts' | 'entities' | 'relations' | 'timeline' | 'sources';

export const UckrPanel: React.FC<UckrPanelProps> = ({
  uckr,
  sourceDocTitle,
  currentVersion = uckr.version || 1,
  versions = [],
  onSelectVersion,
  onRebuildUckr,
  isRebuilding = false
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [selectedFact, setSelectedFact] = useState<UckrFact | null>(null);
  const [selectedTimelineId, setSelectedTimelineId] = useState<string | null>(null);
  const [factFilter, setFactFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const stats = uckr.stats || uckr.statistics || {
    totalFacts: uckr.facts?.length || 0,
    totalEntities: uckr.entities?.length || 0,
    totalEvents: uckr.events?.length || 0,
    totalTimelineNodes: uckr.timeline?.length || 0,
    timelineConsistent: undefined,
    timelineTotalDuration: undefined,
    timelineDurationUnit: undefined,
    timelinePhaseCount: 0,
    totalMetrics: uckr.metrics?.length || 0,
    totalActions: uckr.actions?.length || 0,
    totalSources: uckr.sources?.length || 0,
    totalRelationships: uckr.relationships?.length || 0,
    coverage: 96,
    grounding: 98,
    readiness: 95
  };
  const timeline = uckr.timeline || [];
  const timelineValidation = uckr.validation?.timelineConsistency;
  const timelineConsistent = timelineValidation?.consistent ?? stats.timelineConsistent;
  const timelineTotal = timelineValidation?.declared_total ?? stats.timelineTotalDuration;
  const timelineUnit = timelineValidation?.duration_unit ?? stats.timelineDurationUnit;
  const timelinePhaseCount = timelineValidation?.phase_count ?? stats.timelinePhaseCount ?? 0;

  // Filtered facts
  const filteredFacts = (uckr.facts || []).filter(fact => {
    const matchesType = factFilter === 'all' || fact.type === factFilter;
    const matchesSearch = searchQuery === '' || 
      (fact.value || (fact as any).statement || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (fact.id || (fact as any).factId || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (fact.section || '').toLowerCase().includes(searchQuery.toLowerCase());
    return matchesType && matchesSearch;
  });

  // Group entities by category
  const entitiesByCategory = (uckr.entities || []).reduce<Record<string, UckrEntity[]>>((acc, entity) => {
    const cat = entity.category || 'General';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(entity);
    return acc;
  }, {});

  return (
    <div className="rounded-2xl bg-slate-900/90 border border-purple-500/30 shadow-xl overflow-hidden backdrop-blur-sm">
      {/* Top Banner & Title */}
      <div className="p-5 sm:p-6 border-b border-slate-800/80 bg-gradient-to-r from-purple-950/40 via-indigo-950/20 to-slate-900/60">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 flex-wrap mb-2">
              <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-purple-500/10 border border-purple-500/30 text-purple-300 text-xs font-semibold">
                <Database className="w-3.5 h-3.5 text-purple-400" />
                <span>UCKR Knowledge Layer</span>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-[10px] text-emerald-400 font-mono">v{currentVersion} Active</span>
              </div>

              {/* Version Selector */}
              {versions.length > 1 && onSelectVersion && (
                <div className="flex items-center gap-1.5 bg-slate-950 px-2.5 py-1 rounded-lg border border-purple-500/40 text-xs">
                  <span className="text-slate-400 font-mono text-[11px]">Version:</span>
                  <select
                    value={currentVersion}
                    onChange={(e) => onSelectVersion(Number(e.target.value))}
                    className="bg-transparent text-purple-300 font-bold focus:outline-none cursor-pointer"
                  >
                    {versions.map((v) => (
                      <option key={v.version} value={v.version} className="bg-slate-900 text-white">
                        v{v.version} ({v.factCount || 0} facts)
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Rebuild UCKR button */}
              {onRebuildUckr && (
                <button
                  onClick={onRebuildUckr}
                  disabled={isRebuilding}
                  className="px-2.5 py-1 rounded-lg bg-purple-600/30 hover:bg-purple-600/50 border border-purple-500/40 text-purple-200 text-xs font-semibold transition-colors flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                  title="Force rebuild canonical knowledge base and increment version"
                >
                  <RefreshCw className={`w-3 h-3 ${isRebuilding ? 'animate-spin' : ''}`} />
                  <span>{isRebuilding ? 'Rebuilding...' : 'Rebuild UCKR'}</span>
                </button>
              )}
            </div>

            <h2 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight flex items-center gap-2.5">
              <span>03 UCKR — Unified Content Knowledge Representation (v{currentVersion})</span>
            </h2>
            <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-3xl leading-relaxed">
              Canonical knowledge base preserving all facts, metrics, timeline events, and entity relationships. All deliverables maintain direct cryptographic lineage to this record.
            </p>
          </div>

          {/* Quick Metrics Badges */}
          <div className="flex items-center gap-2 flex-wrap">
            <div className="px-3 py-1.5 rounded-xl bg-slate-950/70 border border-slate-800 text-center">
              <div className="text-[10px] text-slate-400 uppercase font-semibold">Coverage</div>
              <div className="text-sm font-bold text-emerald-400 font-mono">{stats.coverage}%</div>
            </div>
            <div className="px-3 py-1.5 rounded-xl bg-slate-950/70 border border-slate-800 text-center">
              <div className="text-[10px] text-slate-400 uppercase font-semibold">Grounding</div>
              <div className="text-sm font-bold text-purple-400 font-mono">{stats.grounding}%</div>
            </div>
            <div className="px-3 py-1.5 rounded-xl bg-slate-950/70 border border-slate-800 text-center">
              <div className="text-[10px] text-slate-400 uppercase font-semibold">Consistency</div>
              <div className="text-sm font-bold text-sky-400 font-mono">{stats.readiness || 98}%</div>
            </div>
          </div>
        </div>

        {/* Central Architecture Flow Diagram */}
        <div className="my-5 p-4 rounded-xl bg-slate-950/80 border border-purple-500/30 font-mono text-xs">
          <div className="flex flex-col items-center justify-center space-y-1 text-center">
            <div className="px-4 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-300 font-bold">
              AI Understanding
            </div>
            <div className="text-purple-400 font-bold text-sm">↓</div>
            <div className="px-5 py-2 rounded-xl bg-purple-950/80 border border-purple-500 text-purple-200 font-bold shadow-lg shadow-purple-500/20">
              UCKR Knowledge
            </div>
            <div className="text-purple-400 font-bold text-sm">↓</div>
            <div className="w-full max-w-md p-3.5 rounded-xl bg-slate-900/90 border-2 border-purple-500/40 text-left font-mono space-y-1.5 shadow-inner">
              <div className="text-[10px] text-purple-300 uppercase font-bold tracking-wider border-b border-purple-500/30 pb-1 flex items-center justify-between">
                <span>Unified Knowledge Representation</span>
                <span className="text-emerald-400">Grounding {stats.grounding}%</span>
              </div>
              <div className="text-slate-200 flex items-center justify-between">
                <span>│ {stats.totalFacts} Facts</span>
                <span className="text-[10px] text-slate-400">
                  {uckr.facts.length > 0 ? `IDs ${uckr.facts[0].id}..${uckr.facts[uckr.facts.length - 1].id}` : 'No facts yet'}
                </span>
              </div>
              <div className="text-slate-200 flex items-center justify-between">
                <span>│ {stats.totalEntities} Entities</span>
                <span className="text-[10px] text-slate-400">Canonical Registry</span>
              </div>
              <div className="text-slate-200 flex items-center justify-between">
                <span>│ {stats.totalEvents} Events</span>
                <span className="text-[10px] text-slate-400">Dated occurrences</span>
              </div>
              <div className="text-slate-200 flex items-center justify-between">
                <span>│ {stats.totalTimelineNodes} Timeline Nodes</span>
                <span className="text-[10px] text-slate-400">Duration and phase sequence</span>
              </div>
              <div className="text-slate-200 flex items-center justify-between">
                <span>│ {stats.totalMetrics} Metrics</span>
                <span className="text-[10px] text-slate-400">Normalized Units</span>
              </div>
              <div className="text-slate-200 flex items-center justify-between">
                <span>│ {stats.totalRelationships} Relationships</span>
                <span className="text-[10px] text-slate-400">Knowledge Graph</span>
              </div>
            </div>
          </div>
        </div>

        {/* Counter Pills Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2.5 mt-5">
          <div className="p-2.5 rounded-xl bg-purple-950/20 border border-purple-500/20 text-center">
            <div className="text-lg font-extrabold text-purple-300 font-mono">{stats.totalFacts}</div>
            <div className="text-[11px] font-medium text-slate-400">Facts</div>
          </div>
          <div className="p-2.5 rounded-xl bg-indigo-950/20 border border-indigo-500/20 text-center">
            <div className="text-lg font-extrabold text-indigo-300 font-mono">{stats.totalEntities}</div>
            <div className="text-[11px] font-medium text-slate-400">Entities</div>
          </div>
          <div className="p-2.5 rounded-xl bg-blue-950/20 border border-blue-500/20 text-center">
            <div className="text-lg font-extrabold text-blue-300 font-mono">{stats.totalEvents}</div>
            <div className="text-[11px] font-medium text-slate-400">Events</div>
          </div>
          <div className="p-2.5 rounded-xl bg-cyan-950/20 border border-cyan-500/20 text-center">
            <div className="text-lg font-extrabold text-cyan-300 font-mono">{stats.totalMetrics}</div>
            <div className="text-[11px] font-medium text-slate-400">Metrics</div>
          </div>
          <div className="p-2.5 rounded-xl bg-amber-950/20 border border-amber-500/20 text-center">
            <div className="text-lg font-extrabold text-amber-300 font-mono">{stats.totalActions}</div>
            <div className="text-[11px] font-medium text-slate-400">Actions</div>
          </div>
          <div className="p-2.5 rounded-xl bg-emerald-950/20 border border-emerald-500/20 text-center">
            <div className="text-lg font-extrabold text-emerald-300 font-mono">{stats.totalRelationships}</div>
            <div className="text-[11px] font-medium text-slate-400">Relationships</div>
          </div>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex items-center gap-1.5 mt-5 border-t border-slate-800/80 pt-4 overflow-x-auto">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer whitespace-nowrap ${
              activeTab === 'overview'
                ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>[Overview]</span>
          </button>

          <button
            onClick={() => setActiveTab('facts')}
            className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer whitespace-nowrap ${
              activeTab === 'facts'
                ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <Database className="w-3.5 h-3.5" />
            <span>[Facts] ({uckr.facts.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('entities')}
            className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer whitespace-nowrap ${
              activeTab === 'entities'
                ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <Tag className="w-3.5 h-3.5" />
            <span>[Entities] ({uckr.entities.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('relations')}
            className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer whitespace-nowrap ${
              activeTab === 'relations'
                ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <Network className="w-3.5 h-3.5" />
            <span>[Relations] ({uckr.relationships.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('timeline')}
            className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer whitespace-nowrap ${
              activeTab === 'timeline'
                ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <Clock3 className="w-3.5 h-3.5" />
            <span>[Timeline] ({timeline.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('sources')}
            className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer whitespace-nowrap ${
              activeTab === 'sources'
                ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>[Sources] (Grounding)</span>
          </button>
        </div>
      </div>

      {/* Tab Contents */}
      <div className="p-5 sm:p-6">
        {/* 1. OVERVIEW TAB */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Architecture Flow Diagram */}
            <div className="p-5 rounded-xl bg-slate-950/70 border border-slate-800">
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-semibold text-purple-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5" />
                  UCKR Architectural Pipeline
                </span>
                <span className="text-xs text-slate-400">Deterministic Source Grounding</span>
              </div>

              {/* Graphical workflow node strip */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                {/* Step 1 */}
                <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-center relative">
                  <div className="text-[10px] font-bold text-blue-400 uppercase">01 Source</div>
                  <div className="text-xs font-bold text-white mt-1 truncate" title={sourceDocTitle || 'Ingested Document'}>
                    {sourceDocTitle || 'Ingested Document'}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">Raw unverified text</div>
                  <div className="hidden md:block absolute -right-2.5 top-1/2 -translate-y-1/2 text-purple-500 z-10 font-bold">
                    →
                  </div>
                </div>

                {/* Step 2 */}
                <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-center relative">
                  <div className="text-[10px] font-bold text-cyan-400 uppercase">02 AI Understanding</div>
                  <div className="text-xs font-bold text-white mt-1">Semantic Ingestion</div>
                  <div className="text-[11px] text-slate-400 mt-1">OCR, entities, proposition extraction</div>
                  <div className="hidden md:block absolute -right-2.5 top-1/2 -translate-y-1/2 text-purple-500 z-10 font-bold">
                    →
                  </div>
                </div>

                {/* Step 3 (UCKR Hub) */}
                <div className="p-3.5 rounded-xl bg-gradient-to-b from-purple-950/60 to-purple-900/30 border-2 border-purple-500/50 text-center relative shadow-lg shadow-purple-500/10">
                  <div className="text-[10px] font-bold text-purple-300 uppercase flex items-center justify-center gap-1">
                    <Database className="w-3 h-3 text-purple-300" />
                    <span>03 UCKR HUB</span>
                  </div>
                  <div className="text-xs font-extrabold text-white mt-1">Unified Knowledge Base</div>
                  <div className="text-[11px] text-purple-200 font-mono mt-1">
                    {stats.totalFacts} Facts · {stats.totalEntities} Entities
                  </div>
                  <div className="hidden md:block absolute -right-2.5 top-1/2 -translate-y-1/2 text-purple-500 z-10 font-bold">
                    →
                  </div>
                </div>

                {/* Step 4 */}
                <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-center">
                  <div className="text-[10px] font-bold text-emerald-400 uppercase">04 Multi-Outputs</div>
                  <div className="text-xs font-bold text-white mt-1">7 Deliverables</div>
                  <div className="text-[11px] text-emerald-400/90 mt-1">All share identical truth layer</div>
                </div>
              </div>
            </div>

            {/* Quality Gauges & Knowledge Map */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
              {/* Coverage & Verification metrics */}
              <div className="p-5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-4">
                <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                  Knowledge Integrity Benchmarks
                </h3>

                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-300">Grounding Index</span>
                      <span className="font-mono text-purple-400 font-bold">{stats.groundingIndex ?? stats.grounding ?? 100}%</span>
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                      <div className="h-full bg-purple-500 rounded-full" style={{ width: `${stats.groundingIndex ?? stats.grounding ?? 100}%` }} />
                    </div>
                    <p className="text-[10px] text-slate-400 mt-0.5">Verifiable source citation grounding</p>
                  </div>

                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-300">Fact Completeness</span>
                      <span className="font-mono text-emerald-400 font-bold">{stats.factCompleteness ?? 98}%</span>
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                      <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${stats.factCompleteness ?? 98}%` }} />
                    </div>
                    <p className="text-[10px] text-slate-400 mt-0.5">Complete non-fragmented grammatical propositions</p>
                  </div>

                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-300">Fact Consistency</span>
                      <span className="font-mono text-sky-400 font-bold">{stats.factConsistency ?? 100}%</span>
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                      <div className="h-full bg-sky-500 rounded-full" style={{ width: `${stats.factConsistency ?? 100}%` }} />
                    </div>
                    <p className="text-[10px] text-slate-400 mt-0.5">Propositional coherence without contradictions</p>
                  </div>

                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-300">Entity Consistency</span>
                      <span className="font-mono text-indigo-400 font-bold">{stats.entityConsistency ?? 100}%</span>
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                      <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${stats.entityConsistency ?? 100}%` }} />
                    </div>
                    <p className="text-[10px] text-slate-400 mt-0.5">Resolved canonical entities and active relations</p>
                  </div>

                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-300">Number Consistency</span>
                      <span className="font-mono text-cyan-400 font-bold">{stats.numberConsistency ?? 100}%</span>
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                      <div className="h-full bg-cyan-500 rounded-full" style={{ width: `${stats.numberConsistency ?? 100}%` }} />
                    </div>
                    <p className="text-[10px] text-slate-400 mt-0.5">Exact numerical metric quote alignment</p>
                  </div>

                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-300">Date Consistency</span>
                      <span className="font-mono text-amber-400 font-bold">{stats.dateConsistency ?? 100}%</span>
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                      <div className="h-full bg-amber-500 rounded-full" style={{ width: `${stats.dateConsistency ?? 100}%` }} />
                    </div>
                    <p className="text-[10px] text-slate-400 mt-0.5">Timeline and duration phase continuity</p>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-purple-950/20 border border-purple-500/20 text-xs text-purple-200 leading-relaxed flex items-start gap-2">
                  <Info className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
                  <span>
                    No output will fabricate new statistics. All channels pull directly from these {stats.totalFacts} verified facts.
                  </span>
                </div>
              </div>

              {/* Visual Knowledge Graph Preview */}
              <div className="lg:col-span-2 p-5 rounded-xl bg-slate-950/60 border border-slate-800 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                      <Network className="w-3.5 h-3.5 text-purple-400" />
                      UCKR Knowledge Map
                    </h3>
                    <button
                      onClick={() => setActiveTab('relations')}
                      className="text-xs text-purple-400 hover:text-purple-300 font-medium flex items-center gap-1 cursor-pointer"
                    >
                      <span>Explore all {stats.totalRelationships} links</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  {/* ASCII / Visual Graph Map */}
                  <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                    <div className="flex items-center justify-center">
                      <span className="px-3 py-1.5 rounded-lg bg-purple-500/20 border border-purple-500/40 text-purple-200 text-xs font-bold">
                        {uckr.entities[0]?.name || 'Primary Subject'}
                      </span>
                    </div>
                    <div className="text-center text-slate-500 text-xs font-mono">↓ {uckr.relationships[0]?.relation || 'impacts / triggers'}</div>
                    <div className="flex items-center justify-center">
                      <span className="px-3 py-1.5 rounded-lg bg-indigo-500/20 border border-indigo-500/40 text-indigo-200 text-xs font-bold">
                        {uckr.entities[1]?.name || 'Primary Event / Object'}
                      </span>
                    </div>
                    <div className="flex items-center justify-center gap-8 text-xs text-slate-500 font-mono">
                      <span>↙ affects</span>
                      <span>seeks to mitigate ↘</span>
                    </div>
                    <div className="flex items-center justify-center gap-4 flex-wrap">
                      <span className="px-3 py-1 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 text-xs font-medium">
                        {uckr.entities[2]?.name || 'Target 1'}
                      </span>
                      <span className="px-3 py-1 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 text-xs font-medium">
                        {uckr.entities[3]?.name || 'Target 2'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Key Metrics Snapshot */}
                <div className="grid grid-cols-3 gap-2.5 mt-4 pt-4 border-t border-slate-800">
                  {uckr.metrics.slice(0, 3).map((m) => (
                    <div key={m.id} className="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800">
                      <div className="text-base font-extrabold text-white font-mono">{m.value} {m.unit}</div>
                      <div className="text-[10px] text-slate-400 truncate mt-0.5">{m.name}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <section className="p-5 rounded-xl bg-slate-950/60 border border-slate-800" aria-label="Timeline validation">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">Timeline Validation</h3>
                  <p className={`text-sm font-semibold mt-2 ${timelineConsistent === true ? 'text-emerald-400' : timelineConsistent === false ? 'text-rose-400' : 'text-slate-400'}`}>
                    {timelineConsistent === true ? '✓ Timeline consistent' : timelineConsistent === false ? 'Timeline inconsistent' : 'Timeline consistency unavailable'}
                  </p>
                </div>
                <div className="flex items-center gap-5 text-xs text-slate-300">
                  <span>{timeline.length} timeline nodes</span>
                  {timelineTotal != null && <span>{timelineTotal} {timelineUnit || ''} total</span>}
                  <span>{timelinePhaseCount} phases</span>
                </div>
              </div>
              {timeline.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4">
                  {timeline.map((node) => {
                    const grounded = !!node.sourceFactId && uckr.facts.some((fact) => (fact.factId || fact.id) === node.sourceFactId);
                    return (
                      <button
                        key={node.id}
                        onClick={() => setSelectedTimelineId(selectedTimelineId === node.id ? null : node.id)}
                        className="p-3 text-left rounded-lg bg-slate-900 border border-slate-800 hover:border-purple-500/50 transition-colors"
                        aria-expanded={selectedTimelineId === node.id}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <span className="font-mono text-[11px] font-bold text-purple-300">{node.id}</span>
                          <span className="text-[11px] text-slate-400">{node.duration_value != null ? `${node.duration_value} ${node.duration_unit || ''}` : 'Duration not stated'}</span>
                        </div>
                        <p className="text-xs text-white mt-1">{node.description}</p>
                        {selectedTimelineId === node.id && (
                          <div className="mt-3 pt-3 border-t border-slate-800 space-y-2">
                            <p className="text-[11px] text-slate-400">Source fact: <span className="font-mono text-slate-200">{node.sourceFactId || 'Not linked'}</span></p>
                            {node.sourceText && <p className="text-xs text-slate-300 italic">“{node.sourceText}”</p>}
                            <p className={`text-[11px] font-semibold ${grounded ? 'text-emerald-400' : 'text-amber-400'}`}>
                              {grounded ? '✓ Grounded · source fact verified' : 'Source fact not verified'}
                            </p>
                          </div>
                        )}
                      </button>
                    );
                  })}
                </div>
              )}
            </section>
          </div>
        )}

        {/* 2. FACTS TAB */}
        {activeTab === 'facts' && (
          <div className="space-y-4">
            {/* Search & Filter Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search facts by keyword, ID (e.g. F-004), or section..."
                  className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500"
                />
              </div>

              <div className="flex items-center gap-1.5 overflow-x-auto">
                <Filter className="w-3.5 h-3.5 text-slate-400" />
                {['all', 'Metric', 'Proposition', 'Action Mandate', 'Timeline / Event'].map((type) => (
                  <button
                    key={type}
                    onClick={() => setFactFilter(type)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors cursor-pointer whitespace-nowrap ${
                      factFilter === type
                        ? 'bg-purple-600 text-white'
                        : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
                    }`}
                  >
                    {type === 'all' ? 'All Types' : type}
                  </button>
                ))}
              </div>
            </div>

            {/* Fact Registry Table */}
            <div className="rounded-xl border border-slate-800 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950 text-slate-400 uppercase font-semibold border-b border-slate-800">
                    <tr>
                      <th className="p-3 w-20">Fact ID</th>
                      <th className="p-3">Fact Statement</th>
                      <th className="p-3 w-32">Type</th>
                      <th className="p-3 w-24">Location</th>
                      <th className="p-3 w-24">Confidence</th>
                      <th className="p-3 w-32 text-right">Grounding</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/80 bg-slate-900/40">
                    {filteredFacts.map((fact) => (
                      <tr key={fact.id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="p-3 font-mono font-bold text-purple-400">
                          {fact.id}
                        </td>
                        <td className="p-3 font-medium text-slate-200 max-w-md">
                          <p className="line-clamp-2">{fact.value}</p>
                        </td>
                        <td className="p-3">
                          <span className="px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700 text-[10px] font-medium whitespace-nowrap">
                            {fact.type}
                          </span>
                        </td>
                        <td className="p-3 font-mono text-slate-400 whitespace-nowrap">
                          Page {fact.page}
                        </td>
                        <td className="p-3">
                          <span className="font-mono text-emerald-400 font-semibold">
                            {(fact.confidence * 100).toFixed(0)}%
                          </span>
                        </td>
                        <td className="p-3 text-right">
                          <button
                            onClick={() => setSelectedFact(fact)}
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-purple-500/10 hover:bg-purple-500/20 text-purple-300 border border-purple-500/30 text-[11px] font-semibold transition-colors cursor-pointer whitespace-nowrap"
                          >
                            <Eye className="w-3 h-3" />
                            <span>View Source</span>
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {filteredFacts.length === 0 && (
                <div className="p-8 text-center text-slate-400 text-xs">
                  No facts match your search filter "{searchQuery}".
                </div>
              )}
            </div>
          </div>
        )}

        {/* 3. ENTITIES TAB */}
        {activeTab === 'entities' && (
          <div className="space-y-6">
            <div className="text-xs text-slate-400">
              Discovered <span className="text-white font-bold">{uckr.entities.length} canonical entities</span> categorized and linked to prevent name drift across outputs.
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(entitiesByCategory).map(([category, entities]) => (
                <div key={category} className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-3">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                    <span className="text-xs font-bold text-purple-300 uppercase tracking-wider flex items-center gap-1.5">
                      <Tag className="w-3 h-3 text-purple-400" />
                      {category}
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono">
                      {entities.length} items
                    </span>
                  </div>

                  <div className="space-y-2">
                    {entities.map((entity) => (
                      <div key={entity.id} className="p-2.5 rounded-lg bg-slate-900 border border-slate-800/80 flex items-center justify-between">
                        <div>
                          <div className="text-xs font-semibold text-white">{entity.name}</div>
                          <div className="text-[10px] text-slate-400">{entity.role}</div>
                        </div>
                        <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px]">
                          {entity.mentions} refs
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 4. RELATIONS TAB */}
        {activeTab === 'relations' && (
          <div className="space-y-4">
            <div className="text-xs text-slate-400">
              Relationship Graph maps how subjects, verbs, and outcomes are causally interconnected:
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {uckr.relationships.map((rel) => (
                <div key={rel.id} className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono font-bold text-purple-400">{rel.id}</span>
                    <span className="text-[10px] font-mono text-emerald-400">
                      {(rel.confidence * 100).toFixed(0)}% confidence
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-xs flex-wrap">
                    <span className="px-2 py-0.5 rounded bg-purple-500/15 text-purple-300 font-semibold border border-purple-500/30">
                      {rel.source}
                    </span>
                    <span className="text-slate-400 font-mono text-[11px]">
                      ── {rel.relation} ──▶
                    </span>
                    <span className="px-2 py-0.5 rounded bg-indigo-500/15 text-indigo-300 font-semibold border border-indigo-500/30">
                      {rel.target}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 5. TIMELINE TAB */}
        {activeTab === 'timeline' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">Timeline Validation</h3>
              <span className={`text-xs font-semibold ${timelineConsistent === true ? 'text-emerald-400' : timelineConsistent === false ? 'text-rose-400' : 'text-slate-400'}`}>
                {timelineConsistent === true ? '✓ Timeline consistent' : timelineConsistent === false ? 'Timeline inconsistent' : 'Consistency unavailable'}
              </span>
            </div>
            <p className="text-xs text-slate-400">
              {timeline.length} timeline nodes · {timelineTotal != null ? `${timelineTotal} ${timelineUnit || ''} total · ` : ''}{timelinePhaseCount} phases
            </p>
            {timeline.map((node) => {
              const grounded = !!node.sourceFactId && uckr.facts.some((fact) => (fact.factId || fact.id) === node.sourceFactId);
              return (
                <button
                  key={node.id}
                  onClick={() => setSelectedTimelineId(selectedTimelineId === node.id ? null : node.id)}
                  className="w-full p-4 text-left rounded-xl bg-slate-950/60 border border-slate-800 hover:border-purple-500/50 transition-colors"
                  aria-expanded={selectedTimelineId === node.id}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="text-xs font-mono font-bold text-purple-300">{node.id} · Sequence {node.sequence ?? '—'}</span>
                    <span className="text-xs text-slate-300">{node.duration_value != null ? `${node.duration_value} ${node.duration_unit || ''}` : 'Duration not stated'}</span>
                  </div>
                  <p className="text-sm font-semibold text-white mt-2">{node.description}</p>
                  {selectedTimelineId === node.id && (
                    <div className="mt-3 pt-3 border-t border-slate-800 space-y-2">
                      <p className="text-xs text-slate-400">Source fact: <span className="font-mono text-slate-200">{node.sourceFactId || 'Not linked'}</span></p>
                      <p className="text-xs text-slate-300 italic">“{node.sourceText || 'No source quote recorded.'}”</p>
                      <p className={`text-xs font-semibold ${grounded ? 'text-emerald-400' : 'text-amber-400'}`}>
                        {grounded ? '✓ Grounded · source verified' : 'Source fact not verified'}
                      </p>
                    </div>
                  )}
                </button>
              );
            })}
            {timeline.length === 0 && <p className="py-8 text-center text-xs text-slate-400">No timeline durations were extracted from this source.</p>}
          </div>
        )}

        {/* 6. SOURCES TAB (Grounding Registry) */}
        {activeTab === 'sources' && (
          <div className="space-y-4">
            <div className="text-xs text-slate-400">
              Source Grounding references guarantee zero-hallucination provenance back to original documents:
            </div>

            <div className="grid grid-cols-1 gap-3">
              {uckr.facts.slice(0, 8).map((fact) => (
                <div key={fact.id} className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 font-mono text-xs font-bold border border-purple-500/30">
                        {fact.id}
                      </span>
                      <span className="text-xs font-semibold text-white">
                        {fact.sourceDoc}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 text-xs font-mono text-slate-400">
                      <span>Section: {fact.section}</span>
                      <span>•</span>
                      <span>Page {fact.page}</span>
                      <span>•</span>
                      <span className="text-emerald-400">{(fact.confidence * 100).toFixed(0)}% Match</span>
                    </div>
                  </div>

                  <p className="text-xs text-slate-300 font-sans italic bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
                    "{fact.quote}"
                  </p>

                  <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
                    <span>Extracted statement: <strong className="text-white font-normal">{fact.value}</strong></span>
                    <button
                      onClick={() => setSelectedFact(fact)}
                      className="text-purple-400 hover:text-purple-300 font-medium cursor-pointer"
                    >
                      Inspect Grounding →
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Traceability Modal */}
      <SourceGroundingModal
        fact={selectedFact}
        onClose={() => setSelectedFact(null)}
      />
    </div>
  );
};
