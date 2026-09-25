import React, { useState } from 'react';
import { Search, Send, Sparkles, FileText, X, ExternalLink, Loader2, ArrowRight } from 'lucide-react';
import { ragApi, RagQueryResponse } from '../../api/ragApi';

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
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<RagQueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim() || loading) return;

    setLoading(true);
    setError(null);

    try {
      const res = await ragApi.query({
        query: query.trim(),
        top_k: 5,
        use_optimization: true,
      });
      setResponse(res);
    } catch (err: any) {
      setError(err.message || 'RAG Query failed. Please verify backend connection.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/50">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-cyan-400" />
            <h3 className="font-semibold text-slate-100 text-sm">Ask Knowledge Base (Hybrid Vector + Graph RAG)</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Input Form */}
        <form onSubmit={handleSearch} className="p-4 border-b border-slate-800/80 bg-slate-900/80">
          <div className="relative flex items-center">
            <Search className="w-5 h-5 text-slate-400 absolute left-3 pointer-events-none" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask any question about your ingested documents..."
              className="w-full pl-10 pr-24 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-sm placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition-colors"
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="absolute right-1.5 px-3 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-slate-950 font-semibold text-xs transition-colors flex items-center gap-1.5"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
              <span>Ask RAG</span>
            </button>
          </div>
        </form>

        {/* Query Results */}
        <div className="p-6 max-h-[60vh] overflow-y-auto space-y-4 text-slate-300 text-sm">
          {error && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs">
              {error}
            </div>
          )}

          {response && (
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/50 space-y-2">
                <h4 className="text-xs font-semibold text-cyan-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4" /> Grounded Answer
                </h4>
                <p className="text-slate-100 leading-relaxed text-sm whitespace-pre-wrap">
                  {response.answer}
                </p>
              </div>

              {/* Sources */}
              {response.sources && response.sources.length > 0 && (
                <div className="space-y-2">
                  <h5 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Grounded Source Evidence ({response.sources.length})
                  </h5>
                  <div className="space-y-2">
                    {response.sources.map((src, idx) => (
                      <div
                        key={idx}
                        onClick={() => onSelectEvidence && src.chunk_id && onSelectEvidence(src.chunk_id)}
                        className="p-3 rounded-lg bg-slate-950 border border-slate-800 hover:border-cyan-500/50 transition-colors cursor-pointer space-y-1 text-xs"
                      >
                        <div className="flex items-center justify-between text-cyan-400 font-mono text-[11px] font-semibold">
                          <span className="flex items-center gap-1">
                            <FileText className="w-3.5 h-3.5" />
                            [{src.citation_id || idx + 1}] {src.document_id}
                          </span>
                          {src.page && <span className="text-slate-400">Page {src.page}</span>}
                        </div>
                        {src.text && <p className="text-slate-400 line-clamp-2 text-xs font-sans">{src.text}</p>}
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
              <p>Type a question above to execute Hybrid Vector + Graph RAG retrieval.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
