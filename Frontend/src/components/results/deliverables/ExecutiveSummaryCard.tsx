import React, { useState } from 'react';
import { 
  FileCheck, 
  Copy, 
  Check, 
  Download, 
  Printer, 
  Edit3, 
  CheckCircle2, 
  TrendingUp, 
  AlertCircle, 
  Target,
  ArrowRight
} from 'lucide-react';
import { ExecutiveSummaryDeliverable } from '../../../types';
import { StatusBadge } from '../../common/StatusBadge';

interface ExecutiveSummaryCardProps {
  deliverable: ExecutiveSummaryDeliverable;
  onUpdate: (updated: ExecutiveSummaryDeliverable) => void;
  onShowToast: (title: string, message: string, type?: 'success' | 'info' | 'error') => void;
}

export const ExecutiveSummaryCard: React.FC<ExecutiveSummaryCardProps> = ({
  deliverable,
  onUpdate,
  onShowToast
}) => {
  const [copied, setCopied] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [overview, setOverview] = useState(deliverable.executiveOverview);

  const handleCopy = () => {
    const text = `EXECUTIVE SUMMARY BRIEFING\nPriority: ${deliverable.priority}\n\nOVERVIEW:\n${deliverable.executiveOverview}\n\nKEY FINDINGS:\n${deliverable.keyFindings.map(f => `• ${f.metric ? `[${f.metric}] ` : ''}${f.title}: ${f.description}`).join('\n')}\n\nIMPLICATIONS:\n${deliverable.implications.map(i => `• ${i}`).join('\n')}\n\nSTRATEGIC ACTIONS:\n${deliverable.strategicActions.map(a => `• ${a}`).join('\n')}`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    onShowToast('Copied', 'Executive briefing text copied to clipboard.', 'success');
    setTimeout(() => setCopied(false), 2000);
  };

  const handlePrintPdf = () => {
    const printWindow = window.open('', '_blank');
    if (!printWindow) {
      onShowToast('Popup Blocked', 'Please allow popups to print/export PDF.', 'error');
      return;
    }

    const html = `
      <!DOCTYPE html>
      <html>
        <head>
          <title>Executive Summary Briefing</title>
          <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 40px; color: #0f172a; max-width: 800px; margin: 0 auto; line-height: 1.6; }
            .header { border-bottom: 2px solid #e2e8f0; padding-bottom: 16px; margin-bottom: 24px; }
            .metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px; }
            .metric-card { background: #f8fafc; border: 1px solid #e2e8f0; padding: 12px; border-radius: 6px; }
            .metric-val { font-size: 20px; font-weight: bold; color: #7c3aed; }
            .metric-lbl { font-size: 11px; color: #64748b; text-transform: uppercase; }
            h3 { font-size: 14px; text-transform: uppercase; color: #475569; letter-spacing: 0.05em; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; margin-top: 24px; }
            ul { padding-left: 20px; }
          </style>
        </head>
        <body>
          <div class="header">
            <span style="font-size: 11px; color: #7c3aed; font-weight: bold; text-transform: uppercase;">EXECUTIVE BRIEFING REPORT</span>
            <h1 style="font-size: 22px; margin: 4px 0;">Executive Summary: Strategic Findings & Mandated Actions</h1>
            <div style="font-size: 12px; color: #64748b;">Priority Level: ${deliverable.priority} · Prepared for Leadership</div>
          </div>

          <div class="metric-grid">
            ${deliverable.keyFindings.map(f => `
              <div class="metric-card">
                <div class="metric-val">${f.metric || '—'}</div>
                <div class="metric-lbl">${f.title}</div>
              </div>
            `).join('')}
          </div>

          <h3>Executive Overview</h3>
          <p>${deliverable.executiveOverview}</p>

          <h3>Key Strategic Findings</h3>
          <ul>
            ${deliverable.keyFindings.map(f => `<li><strong>${f.title}:</strong> ${f.description}</li>`).join('')}
          </ul>

          <h3>Business & Operational Implications</h3>
          <ul>
            ${deliverable.implications.map(imp => `<li>${imp}</li>`).join('')}
          </ul>

          <h3>Recommended Strategic Actions</h3>
          <ul>
            ${deliverable.strategicActions.map(action => `<li>${action}</li>`).join('')}
          </ul>

          <div style="margin-top: 40px; padding-top: 16px; border-top: 1px solid #e2e8f0; font-size: 11px; color: #94a3b8; text-align: center;">
            GEN TRANSFORM AI PLATFORM · EXECUTIVE BRIEFING ARCHIVE
          </div>
          <script>
            window.onload = function() { window.print(); }
          </script>
        </body>
      </html>
    `;

    printWindow.document.open();
    printWindow.document.write(html);
    printWindow.document.close();
    onShowToast('Print Ready', 'Executive summary formatted for PDF print.', 'success');
  };

  const handleSaveEdits = () => {
    onUpdate({
      ...deliverable,
      executiveOverview: overview
    });
    setIsEditing(false);
    onShowToast('Saved', 'Executive overview updated.', 'info');
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-[#0d121f] p-6 space-y-6 shadow-xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <FileCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-white">Executive Summary</h3>
              <StatusBadge status="verified" size="xs" />
            </div>
            <p className="text-xs text-slate-400">Concise executive briefing for board & executive committee review</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-mono font-bold px-2.5 py-1 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
            Priority: {deliverable.priority}
          </span>
        </div>
      </div>

      {/* 3 Executive Metric Highlights */}
      <div className="grid grid-cols-3 gap-3">
        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Priority</span>
          <span className="text-xl sm:text-2xl font-bold text-rose-400 font-mono mt-0.5 block">{deliverable.priority}</span>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Key Findings</span>
          <span className="text-xl sm:text-2xl font-bold text-purple-400 font-mono mt-0.5 block">{deliverable.keyFindings.length}</span>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Recommendations</span>
          <span className="text-xl sm:text-2xl font-bold text-emerald-400 font-mono mt-0.5 block">{deliverable.strategicActions.length}</span>
        </div>
      </div>

      {/* Main Briefing Container */}
      <div className="rounded-xl bg-slate-950/80 border border-slate-800 p-6 space-y-6 text-xs sm:text-sm text-slate-200">
        {/* Executive Overview */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-xs font-bold text-purple-400 uppercase tracking-wider">
              Executive Overview
            </h4>
            <button
              onClick={() => setIsEditing(!isEditing)}
              className="text-[11px] text-slate-400 hover:text-white flex items-center gap-1"
            >
              <Edit3 className="w-3 h-3" />
              <span>{isEditing ? 'Cancel Edit' : 'Edit Text'}</span>
            </button>
          </div>

          {isEditing ? (
            <div className="space-y-2">
              <textarea
                value={overview}
                onChange={(e) => setOverview(e.target.value)}
                rows={4}
                className="w-full rounded-lg bg-slate-900 border border-slate-800 p-3 text-xs text-white focus:outline-none focus:border-purple-500"
              />
              <button
                onClick={handleSaveEdits}
                className="px-3 py-1 rounded bg-purple-600 text-white text-xs font-semibold"
              >
                Save Overview
              </button>
            </div>
          ) : (
            <p className="leading-relaxed text-slate-300 bg-slate-900/50 p-4 rounded-xl border border-slate-800/60 font-sans">
              {deliverable.executiveOverview}
            </p>
          )}
        </div>

        {/* Key Findings with Metrics */}
        <div className="space-y-3">
          <h4 className="text-xs font-bold text-purple-400 uppercase tracking-wider">
            Key Findings
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {deliverable.keyFindings.map((finding, idx) => (
              <div key={idx} className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 flex items-start gap-3">
                {finding.metric && (
                  <div className="px-2.5 py-1 rounded-lg bg-purple-500/15 border border-purple-500/30 font-mono font-bold text-purple-300 text-sm shrink-0">
                    {finding.metric}
                  </div>
                )}
                <div>
                  <div className="font-semibold text-white text-xs">{finding.title}</div>
                  <div className="text-xs text-slate-400 mt-0.5 leading-relaxed">{finding.description}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Business & Technical Implications */}
        <div className="space-y-2">
          <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider">
            Implications
          </h4>
          <ul className="space-y-1.5 pl-4 list-disc text-xs sm:text-sm text-slate-300">
            {deliverable.implications.map((imp, idx) => (
              <li key={idx} className="leading-relaxed">{imp}</li>
            ))}
          </ul>
        </div>

        {/* Recommended Strategic Actions */}
        <div className="space-y-2.5 pt-2 border-t border-slate-800/60">
          <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider">
            Recommended Actions
          </h4>
          <div className="space-y-2">
            {deliverable.strategicActions.map((action, idx) => (
              <div key={idx} className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-500/20 text-emerald-200 text-xs flex items-center gap-2.5">
                <Target className="w-4 h-4 text-emerald-400 shrink-0" />
                <span className="leading-relaxed">{action}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer Actions */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
        <div className="flex items-center gap-2">
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Copied' : 'Copy Summary'}</span>
          </button>

          <button
            onClick={handlePrintPdf}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-md shadow-purple-600/20 transition-all cursor-pointer"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Export PDF</span>
          </button>
        </div>

        <span className="text-xs text-slate-400 font-mono">
          Ready for C-Suite Briefing
        </span>
      </div>
    </div>
  );
};
