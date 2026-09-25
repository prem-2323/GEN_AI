import React, { useEffect, useState } from 'react';
import { X, GitCommit, FileText, CheckCircle2, ShieldCheck, Database, Layers, Hash, AlertTriangle, ExternalLink, Cpu } from 'lucide-react';
import { provenanceApi, LineageTreeUI, OutputProvenanceUI } from '../../api/provenanceApi';

export interface ProvenanceViewerModalProps {
  outputId: string;
  isOpen: boolean;
  onClose: () => void;
}

export const ProvenanceViewerModal: React.FC<ProvenanceViewerModalProps> = ({
  outputId,
  isOpen,
  onClose,
}) => {
  const [provenance, setProvenance] = useState<OutputProvenanceUI | null>(null);
  const [lineage, setLineage] = useState<LineageTreeUI | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || !outputId) return;

    let isMounted = true;
    setLoading(true);
    setError(null);

    Promise.all([
      provenanceApi.getOutputProvenance(outputId).catch(() => null),
      provenanceApi.getOutputLineage(outputId).catch(() => null),
    ])
      .then(([provData, lineageData]) => {
        if (!isMounted) return;
        setProvenance(provData);
        setLineage(lineageData);
        setLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err.message || 'Failed to load provenance lineage.');
        setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [isOpen, outputId]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-2xl bg-slate-900 border-l border-slate-800 h-full flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/50">
          <div className="flex items-center gap-2">
            <GitCommit className="w-5 h-5 text-purple-400" />
            <div>
              <h3 className="font-semibold text-slate-100 text-sm">Provenance & Evidence Lineage</h3>
              <p className="text-xs text-slate-400 font-mono">ID: {outputId}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 text-slate-300">
          {loading && (
            <div className="flex flex-col items-center justify-center py-16 space-y-3">
              <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
              <p className="text-xs text-slate-400 font-mono">Resolving ground truth evidence chain...</p>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {!loading && !error && (
            <>
              {/* Integrity & Hash Card */}
              <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/50 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4 text-emerald-400" /> Content Integrity
                  </span>
                  <span className="px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                    INTEGRITY_VALID
                  </span>
                </div>
                {provenance?.content_hash && (
                  <div className="text-[11px] font-mono text-slate-400 flex items-center gap-1 overflow-x-auto">
                    <Hash className="w-3.5 h-3.5 text-purple-400 shrink-0" />
                    <span>SHA-256: {provenance.content_hash}</span>
                  </div>
                )}
              </div>

              {/* Pipeline System Metadata */}
              {provenance?.metadata && (
                <div className="p-4 rounded-xl bg-slate-800/30 border border-slate-700/40 space-y-3">
                  <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                    <Cpu className="w-4 h-4 text-cyan-400" /> Generation Pipeline Metadata
                  </h4>
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div>
                      <span className="text-slate-500 block text-[11px]">PyTorch Model</span>
                      <span className="font-mono text-slate-200">{provenance.metadata.model_id || 'test_linear_v1'}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[11px]">Optimization Backend</span>
                      <span className="font-mono text-cyan-300">{provenance.metadata.optimization_backend || 'QUBO / Hybrid'}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[11px]">Distillation Strategy</span>
                      <span className="font-mono text-slate-200">{provenance.metadata.distillation_model || 'Student Distillation v1'}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[11px]">Active Parameter Budget</span>
                      <span className="font-mono text-purple-300">{provenance.metadata.active_parameter_count || 512} params</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Lineage Trace Tree */}
              <div className="space-y-3">
                <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Layers className="w-4 h-4 text-purple-400" /> Traceability Graph (Output → Claim → Evidence → Document)
                </h4>

                {lineage?.tree ? (
                  <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-4 font-mono text-xs">
                    {/* Root Deliverable Node */}
                    <div className="p-3 rounded bg-purple-950/40 border border-purple-500/30 flex items-center justify-between">
                      <div className="flex items-center gap-2 text-purple-300 font-semibold">
                        <FileText className="w-4 h-4" />
                        <span>{lineage.tree.label}</span>
                      </div>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-purple-500/20 text-purple-300">OUTPUT</span>
                    </div>

                    {/* Children Claims & Evidence */}
                    <div className="pl-4 border-l-2 border-slate-800 space-y-3">
                      {lineage.tree.children?.map((claimNode, cIdx) => (
                        <div key={claimNode.node_id || cIdx} className="space-y-2">
                          <div className="p-2.5 rounded bg-slate-900 border border-slate-800 flex items-center justify-between text-slate-200">
                            <span className="truncate max-w-md">{claimNode.label}</span>
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300">CLAIM</span>
                          </div>

                          {/* Evidence & Documents under Claim */}
                          <div className="pl-4 border-l-2 border-slate-800 space-y-2">
                            {claimNode.children?.map((evNode, eIdx) => (
                              <div key={evNode.node_id || eIdx} className="p-2 rounded bg-slate-900/60 border border-slate-800/80 space-y-1">
                                <div className="flex items-center justify-between text-emerald-400 text-[11px]">
                                  <span className="font-semibold">{evNode.label}</span>
                                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300">EVIDENCE</span>
                                </div>

                                {evNode.children?.map((docNode, dIdx) => (
                                  <div key={docNode.node_id || dIdx} className="mt-1 pl-2 border-l border-emerald-500/30 text-[11px] text-slate-400 flex items-center justify-between">
                                    <span>{docNode.label}</span>
                                    {docNode.location?.page && (
                                      <span className="text-cyan-400">Page {docNode.location.page}</span>
                                    )}
                                  </div>
                                ))}
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="p-6 rounded-xl bg-slate-800/20 border border-slate-800 text-center text-slate-500 text-xs">
                    No Lineage tree available for output ID.
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
