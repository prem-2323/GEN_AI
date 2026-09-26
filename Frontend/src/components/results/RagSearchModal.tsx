import React, { useState } from 'react';
import { Search, Send, Sparkles, FileText, X, Loader2, CheckCircle2, AlertTriangle, Cpu, ShieldCheck } from 'lucide-react';
import { ragApi, GroundedAnswerResponse } from '../../api/ragApi';

export interface RagSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectEvidence?: (evidenceId: string) => void;
}

export const RagSearchModal: React.FC<RagSearchModalProps> = ({
  isOpen,
  onClose,
  onSelectEvidence,
}) => {
  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(5);
  const [quboK, setQuboK] = useState(3);
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<GroundedAnswerResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim() || loading) return;

    if (quboK > topK) {
      setError('QUBO selection (qubo_k) cannot exceed candidate pool size (top_k).');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await ragApi.answer({
        query: query.trim(),
        top_k: topK,
        qubo_k: quboK,
        enable_qubo: true,
      });
      setResponse(res);
    } catch (err: any) {
      let userMsg = 'Unable to complete grounded answer request. Please check backend services.';
      if (err?.status === 503) {
        userMsg = 'Service temporarily unavailable. Please verify Neo4j and embedding services.';
      } else if (err?.message && !err.message.includes('Traceback')) {
        userMsg = err.message;
      }
      setError(userMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-3xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl flex flex-col overflow-hidden max-h-[90vh]">
        {/* Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/70">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-100 text-sm">DocLink Grounded RAG + QLoRA Student</h3>
              <p className="text-slate-400 text-xs">Hybrid Neo4j + FAISS + RRF + QUBO Evidence Optimization</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Input Form */}
        <form onSubmit={handleSearch} className="p-4 border-b border-slate-800 bg-slate-900/90 space-y-3">
          <div className="relative flex items-center">
            <Search className="w-5 h-5 text-slate-400 absolute left-3.5 pointer-events-none" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a question (e.g. 'What sensors were used in the IoT architecture?')..."
              className="w-full pl-11 pr-28 py-3 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-sm placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition-colors"
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="absolute right-2 px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-slate-950 font-semibold text-xs transition-colors flex items-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Solving...</span>
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  <span>Ask RAG</span>
                </>
              )}
            </button>
          </div>

          <div className="flex items-center justify-between text-xs text-slate-400 px-1">
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-1.5">
                <span>RRF Pool (top_k):</span>
                <input
                  type="number"
                  min={1}
                  max={20}
                  value={topK}
                  onChange={(e) => setTopK(parseInt(e.target.value) || 5)}
                  className="w-12 px-1.5 py-0.5 rounded bg-slate-950 border border-slate-800 text-center text-cyan-400 font-mono"
                />
              </label>
              <label className="flex items-center gap-1.5">
                <span>QUBO Evidence (qubo_k):</span>
                <input
                  type="number"
                  min={1}
                  max={topK}
                  value={quboK}
                  onChange={(e) => setQuboK(parseInt(e.target.value) || 3)}
                  className="w-12 px-1.5 py-0.5 rounded bg-slate-950 border border-slate-800 text-center text-cyan-400 font-mono"
                />
              </label>
            </div>
            <span className="text-[11px] text-slate-500 font-mono">Qwen2.5-0.5B Student Active</span>
          </div>
        </form>

        {/* Results Body */}
        <div className="p-6 overflow-y-auto space-y-5 text-slate-300 text-sm">
          {loading && (
            <div className="py-12 flex flex-col items-center justify-center text-center space-y-3">
              <div className="relative">
                <Loader2 className="w-10 h-10 text-cyan-400 animate-spin" />
                <Cpu className="w-5 h-5 text-cyan-500 absolute inset-0 m-auto" />
              </div>
              <p className="text-slate-300 font-medium text-sm">Executing Hybrid Retrieval & QUBO Evidence Optimization...</p>
              <p className="text-slate-500 text-xs">FAISS Vector + Neo4j Graph ➔ RRF Fusion ➔ QUBO Solver ➔ QLoRA Student</p>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-start gap-2.5">
              <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-rose-300">Processing Error</p>
                <p className="mt-0.5 text-rose-400/90">{error}</p>
              </div>
            </div>
          )}

          {response && !loading && (
            <div className="space-y-5">
              {/* Question Header */}
              <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 text-xs text-slate-300 flex items-center justify-between">
                <div>
                  <span className="text-slate-500 font-medium mr-2">QUESTION:</span>
                  <span className="text-slate-100 font-semibold">{response.query}</span>
                </div>
                <span className="text-slate-400 font-mono text-[11px] bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                  {response.total_latency_ms.toFixed(1)} ms
                </span>
              </div>

              {/* Grounded Answer Card */}
              <div className="p-5 rounded-xl bg-slate-850 border border-slate-800 space-y-3 shadow-lg">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-cyan-400" />
                    <h4 className="text-xs font-semibold text-cyan-400 uppercase tracking-wider">
                      Grounded Answer
                    </h4>
                  </div>

                  {/* Grounding Badge */}
                  <div className="flex items-center gap-2">
                    {response.grounding.grounding_pass ? (
                      <span className="px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-semibold flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Grounded: PASS
                      </span>
                    ) : (
                      <span className="px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 text-xs font-semibold flex items-center gap-1.5">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        Grounded: REVIEW
                      </span>
                    )}
                  </div>
                </div>

                <p className="text-slate-100 leading-relaxed text-sm whitespace-pre-wrap font-sans">
                  {response.answer}
                </p>

                {/* Grounding & Numerical Status Details */}
                <div className="pt-2 flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-800/50 font-mono">
                  <span className="flex items-center gap-1">
                    <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
                    Numerical Fact Preservation: {response.grounding.numerical_valid ? '100% Verified' : 'Check Context'}
                  </span>
                  <span>
                    QUBO Solver: {response.qubo?.solver_type || 'Exact / SA'} (Energy: {response.qubo?.total_energy?.toFixed(4) ?? '0.0000'})
                  </span>
                </div>
              </div>

              {/* Citations & Evidence Sources */}
              {response.evidence && response.evidence.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h5 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Selected Evidence Sources ({response.evidence.length})
                    </h5>
                    <span className="text-[11px] text-slate-500 font-mono">
                      Citations: {response.citations.join(', ') || 'None'}
                    </span>
                  </div>

                  <div className="grid gap-2.5">
                    {response.evidence.map((ev, idx) => (
                      <div
                        key={idx}
                        onClick={() => onSelectEvidence && ev.chunk_id && onSelectEvidence(ev.chunk_id)}
                        className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 hover:border-cyan-500/50 transition-colors cursor-pointer space-y-1.5 text-xs"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-mono text-cyan-400 font-bold flex items-center gap-1.5">
                            <FileText className="w-3.5 h-3.5" />
                            [{ev.evidence_id}] {ev.document_id}
                          </span>
                          <div className="flex items-center gap-2 text-slate-400 font-mono text-[11px]">
                            <span>Page {ev.page_number}</span>
                            {ev.qubo_score !== undefined && (
                              <span className="bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800 text-slate-300">
                                energy: {ev.qubo_score.toFixed(3)}
                              </span>
                            )}
                          </div>
                        </div>
                        <p className="text-slate-300 line-clamp-3 text-xs leading-relaxed font-sans">
                          {ev.text}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {!response && !loading && !error && (
            <div className="py-12 text-center text-slate-500 text-xs space-y-2">
              <Sparkles className="w-8 h-8 text-slate-700 mx-auto" />
              <p>Type a question above to execute real Hybrid Vector + Graph RAG & QLoRA Student generation.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
