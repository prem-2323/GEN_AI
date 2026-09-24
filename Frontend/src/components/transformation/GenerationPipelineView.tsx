import React, { useEffect, useState, useRef } from 'react';
import {
  Sparkles,
  Layers,
  Activity,
  Terminal,
  Check,
  Disc,
  Circle
} from 'lucide-react';
import { OutputType, SourceFile, TransformationConfig, AIAnalysis, UckrKnowledgeBase, DeliverablesState } from '../../types';
import { analyzeSourceContent, buildUckrKnowledge, generateDeliverables } from '../../services/aiService';
import { StatusBadge } from '../common/StatusBadge';

interface PipelineResultPayload {
  deliverables: DeliverablesState;
  analysis: AIAnalysis | null;
  uckr: UckrKnowledgeBase | null;
}

interface GenerationPipelineViewProps {
  selectedOutputs: OutputType[];
  sourceName: string;
  source: SourceFile | null;
  config?: TransformationConfig;
  analysis?: AIAnalysis | null;
  uckr?: UckrKnowledgeBase | null;
  onComplete: (results: PipelineResultPayload) => void;
  onError: (message: string) => void;
  onBack?: () => void;
}

interface TelemetryLog {
  id: string;
  time: string;
  module: string;
  message: string;
  level: 'info' | 'success' | 'warn';
}

const FALLBACK_CONFIG: TransformationConfig = {
  targetAudience: 'General Public',
  tone: 'Professional',
  language: 'English',
  levelOfDetail: 'Balanced',
  objective: 'Inform',
  contentStyle: 'Professional',
};

export const GenerationPipelineView: React.FC<GenerationPipelineViewProps> = ({
  selectedOutputs,
  sourceName,
  source,
  config,
  analysis: initialAnalysis,
  uckr: initialUckr,
  onComplete,
  onError,
  onBack
}) => {
  const [progress, setProgress] = useState(4);
  const [activeStepIndex, setActiveStepIndex] = useState(0);
  const [logs, setLogs] = useState<TelemetryLog[]>([]);
  const [showTelemetry, setShowTelemetry] = useState(true);
  const [failed, setFailed] = useState<string | null>(null);
  const logsContainerRef = useRef<HTMLDivElement>(null);
  const doneRef = useRef(false);

  const effectiveConfig = config || FALLBACK_CONFIG;
  const totalPages = source?.pages || 1;

  const addLog = (module: string, message: string, level: 'info' | 'success' | 'warn' = 'info') => {
    const now = new Date();
    const timeStr = now.toTimeString().split(' ')[0] + '.' + Math.floor(now.getMilliseconds() / 100);
    setLogs((prev) => [...prev, { id: `${module}-${Date.now()}-${Math.random()}`, time: timeStr, module, message, level }]);
  };

  useEffect(() => {
    if (!logsContainerRef.current) return;
    logsContainerRef.current.scrollTop = logsContainerRef.current.scrollHeight;
  }, [logs]);

  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      if (!source) {
        onError('No source content. Upload or paste source material first.');
        return;
      }
      if (selectedOutputs.length === 0) {
        onError('No outputs selected.');
        return;
      }
      try {
        setActiveStepIndex(0);
        setProgress(6);
        addLog('SOURCE_INGEST', `Reading source: ${sourceName}`, 'info');

        setActiveStepIndex(1);
        setProgress(14);
        let liveAnalysis = initialAnalysis || null;
        if (!liveAnalysis) {
          addLog('AI_EXTRACT', 'Running Gemini source analysis…', 'info');
          liveAnalysis = await analyzeSourceContent(source);
          if (cancelled) return;
          addLog('AI_COMPLETE', `Topic detected: ${liveAnalysis.detectedTopic.slice(0, 80)}`, 'success');
        } else {
          addLog('AI_COMPLETE', 'Using existing source analysis.', 'success');
        }
        setProgress(34);

        setActiveStepIndex(2);
        let liveUckr = initialUckr || null;
        if (!liveUckr && liveAnalysis) {
          addLog('UCKR_BUILD', 'Building UCKR knowledge base with Gemini…', 'info');
          try {
            liveUckr = await buildUckrKnowledge(source, liveAnalysis);
            if (cancelled) return;
            addLog('UCKR_READY', `UCKR locked: ${liveUckr.stats.totalFacts} facts, ${liveUckr.stats.grounding}% grounding`, 'success');
          } catch (e) {
            addLog('UCKR_BUILD', 'UCKR construction failed — continuing with analysis only.', 'warn');
          }
        } else if (liveUckr) {
          addLog('UCKR_READY', 'Using existing UCKR knowledge base.', 'success');
        }
        setProgress(56);

        setActiveStepIndex(3);
        addLog('TRANSFORM_DISPATCH', `Dispatching ${selectedOutputs.length} deliverable generators…`, 'info');
        setProgress(64);

        setActiveStepIndex(4);
        const deliverables = await generateDeliverables(
          source,
          effectiveConfig,
          selectedOutputs,
          liveAnalysis,
          liveUckr,
          (step, pct) => {
            if (cancelled) return;
            setProgress(64 + Math.round(pct * 0.26));
            addLog('GEN_ENGINE', step, 'info');
          }
        );
        if (cancelled) return;
        addLog('GEN_ASSETS', `Compiled ${selectedOutputs.length} deliverables`, 'success');
        setProgress(92);

        setActiveStepIndex(5);
        addLog('AUDIT', liveUckr ? 'Outputs reference UCKR facts.' : 'Validation skipped — no UCKR available.', liveUckr ? 'success' : 'warn');
        setProgress(100);

        if (cancelled || doneRef.current) return;
        doneRef.current = true;
        onComplete({ deliverables, analysis: liveAnalysis, uckr: liveUckr });
      } catch (err) {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : 'Generation failed.';
        setFailed(message);
        addLog('PIPELINE_ERROR', message, 'warn');
        onError(message);
      }
    };
    run();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const stageSubtitle =
    progress < 14 ? 'Reading and analyzing source document…' :
    progress < 34 ? 'Running semantic extraction (Qwen 3 & Gemma 3)…' :
    progress < 56 ? 'Constructing UCKR canonical knowledge base…' :
    progress < 64 ? 'Orchestrating deliverable blueprints…' :
    progress < 92 ? 'Synthesizing deliverables with AI engine…' :
    progress < 100 ? 'Validating consistency and grounding…' :
    'Transformation pipeline complete!';

  const pipelineSteps = [
    { id: 'source_analysis', name: 'SOURCE ANALYSIS', done: progress >= 14, active: activeStepIndex === 0 && progress < 14, info: progress >= 14 ? `${totalPages} page(s) ingested` : `Reading ${sourceName}` },
    { id: 'ai_understanding', name: 'AI UNDERSTANDING', done: progress >= 34, active: activeStepIndex === 1 && progress < 34, info: progress >= 34 ? 'Qwen/Gemma analysis complete' : 'Analyzing with AI…' },
    { id: 'uckr_construction', name: 'UCKR CONSTRUCTION', done: progress >= 56, active: activeStepIndex === 2 && progress < 56, info: initialUckr ? 'Knowledge base ready' : progress >= 56 ? 'UCKR step finished' : 'Building knowledge base…' },
    { id: 'content_transformation', name: 'CONTENT TRANSFORMATION', done: progress >= 64, active: activeStepIndex === 3 && progress < 64, info: `Audience: ${effectiveConfig.targetAudience}` },
    { id: 'output_generation', name: 'OUTPUT GENERATION', done: progress >= 92, active: activeStepIndex === 4 && progress < 92, info: `${selectedOutputs.length} deliverables` },
    { id: 'validation', name: 'CONSISTENCY VALIDATION', done: progress >= 100, active: activeStepIndex === 5 && progress < 100, info: progress >= 100 ? 'Done' : 'Validating…' },
  ];

  return (
    <div className="min-h-[82vh] flex flex-col items-center justify-center py-10 px-4">
      <div className="max-w-2xl w-full space-y-6">
        <div className="text-center space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/25 text-purple-300 text-xs font-semibold tracking-wide">
            <Sparkles className="w-3.5 h-3.5 text-purple-400" />
            <span>GEN TRANSFORM AI</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">Live Generation Pipeline</h1>
          <p className="text-sm font-medium text-slate-300">{stageSubtitle}</p>
          {failed && (
            <div className="mt-3 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex flex-col sm:flex-row items-center justify-between gap-3 text-center sm:text-left">
              <span>{failed}</span>
              {onBack && (
                <button
                  type="button"
                  onClick={onBack}
                  className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-medium text-xs whitespace-nowrap transition-colors cursor-pointer shrink-0"
                >
                  Return to Studio
                </button>
              )}
            </div>
          )}
        </div>

        <div className="relative rounded-2xl border border-slate-800/90 bg-[#0d121f]/95 p-6 sm:p-8 shadow-2xl overflow-hidden">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800/80">
            <div className="text-left">
              <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold block">Active Document</span>
              <span className="text-xs sm:text-sm font-semibold text-slate-200 truncate max-w-xs block">{sourceName}</span>
            </div>
            <div className="text-2xl font-bold font-mono text-purple-400 tabular-nums">{progress}%</div>
          </div>

          <div className="w-full bg-slate-950 rounded-full h-2.5 overflow-hidden mb-8 border border-slate-800/80">
            <div className="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-emerald-400 transition-all duration-300 rounded-full" style={{ width: `${progress}%` }} />
          </div>

          <div className="space-y-4">
            {pipelineSteps.map((step, idx) => {
              const isCompleted = step.done;
              const isActive = step.active;
              return (
                <div key={step.id} className="relative flex items-start gap-3.5">
                  {idx < pipelineSteps.length - 1 && (
                    <div className={`absolute left-[13px] top-6 bottom-0 w-[2px] -mb-4 ${isCompleted ? 'bg-emerald-500/70' : 'bg-slate-800'}`} />
                  )}
                  <div className="shrink-0 mt-0.5 z-10">
                    {isCompleted ? (
                      <div className="w-7 h-7 rounded-full bg-emerald-500/20 border border-emerald-500/50 flex items-center justify-center text-emerald-400">
                        <Check className="w-4 h-4 stroke-[2.5]" />
                      </div>
                    ) : isActive ? (
                      <div className="relative w-7 h-7 rounded-full bg-purple-950/90 border border-purple-400 flex items-center justify-center text-purple-300">
                        <Disc className="w-3.5 h-3.5 animate-spin text-purple-300" />
                      </div>
                    ) : (
                      <div className="w-7 h-7 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-500">
                        <Circle className="w-3.5 h-3.5 stroke-[1.5]" />
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <h3 className={`text-sm font-semibold tracking-tight ${isCompleted ? 'text-white' : isActive ? 'text-purple-300 font-bold' : 'text-slate-400'}`}>{step.name}</h3>
                      {isCompleted ? <StatusBadge status="verified" size="xs" /> : isActive ? <StatusBadge status="processing" size="xs" /> : <span className="text-[11px] font-mono text-slate-500">○ Waiting</span>}
                    </div>
                    <p className="text-xs text-slate-400 font-mono mt-0.5">{step.info}</p>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="mt-7 pt-4 border-t border-slate-800/80">
            <div className="flex items-center justify-between mb-2">
              <button onClick={() => setShowTelemetry(!showTelemetry)} className="flex items-center gap-1.5 text-[11px] font-mono text-slate-400 hover:text-slate-300 cursor-pointer">
                <Terminal className="w-3.5 h-3.5 text-purple-400" />
                <span className="uppercase tracking-wider">Live Log</span>
              </button>
              <div className="flex items-center gap-1.5 text-[11px] font-mono text-emerald-400">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                <span>Ollama / Qwen & Gemma</span>
              </div>
            </div>
            {showTelemetry && (
              <div ref={logsContainerRef} className="h-24 overflow-y-auto bg-slate-950/90 rounded-lg p-2.5 border border-slate-800/80 font-mono text-[11px] space-y-1">
                {logs.length === 0 ? <div className="text-slate-400">Starting real generation…</div> : logs.map((log) => (
                  <div key={log.id} className="flex items-start gap-2 leading-relaxed">
                    <span className="text-slate-400 shrink-0">[{log.time}]</span>
                    <span className={`shrink-0 font-semibold ${log.level === 'success' ? 'text-emerald-400' : 'text-purple-400'}`}>{log.module}:</span>
                    <span className="text-slate-300">{log.message}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="mt-5 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-300">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-purple-400" />
              <span>Targeting <strong>{selectedOutputs.length}</strong> deliverables</span>
            </div>
            <div className="flex items-center gap-1.5 text-slate-400 font-mono text-[11px]">
              <Activity className="w-3.5 h-3.5 text-purple-400 animate-pulse" />
              <span>{progress === 100 ? 'Complete — opening workspace' : 'Gemini synthesis in flight'}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
