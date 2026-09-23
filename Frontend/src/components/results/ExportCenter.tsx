import React, { useState } from 'react';
import { 
  Download, 
  FileText, 
  Linkedin, 
  Twitter, 
  ShieldAlert, 
  BarChart3, 
  Presentation, 
  Video, 
  FileCheck2, 
  Check, 
  CheckSquare, 
  Square, 
  Package, 
  Sparkles,
  ExternalLink
} from 'lucide-react';
import { OutputType, DeliverablesState } from '../../types';

interface ExportItem {
  id: OutputType;
  filename: string;
  format: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
}

const EXPORT_ITEMS: ExportItem[] = [
  { id: 'linkedin', filename: 'LinkedIn.txt', format: 'TXT', label: 'LinkedIn Post', icon: Linkedin, color: 'text-blue-400' },
  { id: 'twitter', filename: 'X Thread.txt', format: 'TXT', label: 'X Thread', icon: Twitter, color: 'text-sky-400' },
  { id: 'advisory', filename: 'Advisory.pdf', format: 'PDF', label: 'Advisory Brief', icon: ShieldAlert, color: 'text-rose-400' },
  { id: 'executive_summary', filename: 'Summary.pdf', format: 'PDF', label: 'Executive Summary', icon: FileCheck2, color: 'text-emerald-400' },
  { id: 'presentation', filename: 'Presentation.pptx', format: 'PPTX', label: 'Presentation Deck', icon: Presentation, color: 'text-indigo-400' },
  { id: 'infographic', filename: 'Infographic.svg', format: 'SVG', label: 'Infographic Package', icon: BarChart3, color: 'text-amber-400' },
  { id: 'video', filename: 'Video Package.zip', format: 'ZIP', label: 'Video Production Package', icon: Video, color: 'text-purple-400' },
];

interface ExportCenterProps {
  deliverables?: DeliverablesState;
  onShowToast: (title: string, message: string, type?: 'success' | 'info' | 'error') => void;
  onExportAll: () => void;
}

export const ExportCenter: React.FC<ExportCenterProps> = ({
  deliverables,
  onShowToast,
  onExportAll
}) => {
  // All checked by default as requested: ☑ LinkedIn.txt, ☑ X Thread.txt, etc.
  const [selectedExports, setSelectedExports] = useState<Record<string, boolean>>({
    'LinkedIn.txt': true,
    'X Thread.txt': true,
    'Advisory.pdf': true,
    'Summary.pdf': true,
    'Presentation.pptx': true,
    'Infographic.svg': true,
    'Video Package.zip': true,
  });

  const toggleItem = (filename: string) => {
    setSelectedExports(prev => ({
      ...prev,
      [filename]: !prev[filename]
    }));
  };

  const handleSelectAll = (select: boolean) => {
    const updated: Record<string, boolean> = {};
    EXPORT_ITEMS.forEach(item => {
      updated[item.filename] = select;
    });
    setSelectedExports(updated);
  };

  const downloadFile = (item: ExportItem) => {
    let content = '';
    let mimeType = 'text/plain;charset=utf-8';

    if (item.id === 'linkedin') {
      content = deliverables?.linkedin 
        ? `${deliverables.linkedin.hook}\n\n${deliverables.linkedin.body}\n\n${deliverables.linkedin.callToAction}\n\n${deliverables.linkedin.hashtags.join(' ')}`
        : 'Enterprise Intelligence LinkedIn Post';
    } else if (item.id === 'twitter') {
      content = deliverables?.twitter?.thread 
        ? deliverables.twitter.thread.map(t => `${t.index}. ${t.text}`).join('\n\n')
        : (deliverables?.twitter?.singlePost || 'Enterprise Intelligence X Post');
    } else if (item.id === 'advisory') {
      content = deliverables?.advisory
        ? `SECURITY ADVISORY: ${deliverables.advisory.title}\nSeverity: ${deliverables.advisory.severity}\n\nSituation:\n${deliverables.advisory.situation}\n\nImpact:\n${deliverables.advisory.threatImpact}`
        : 'Security Advisory Document';
      mimeType = 'application/pdf';
    } else if (item.id === 'executive_summary') {
      content = deliverables?.executive_summary
        ? `EXECUTIVE SUMMARY\n\n${deliverables.executive_summary.executiveOverview}\n\nKey Findings:\n` +
          deliverables.executive_summary.keyFindings.map(f => `• ${f.title}: ${f.description}`).join('\n')
        : 'Executive Summary Briefing';
      mimeType = 'application/pdf';
    } else if (item.id === 'presentation') {
      content = JSON.stringify(deliverables?.presentation || { title: 'Presentation Deck' }, null, 2);
      mimeType = 'application/vnd.openxmlformats-officedocument.presentationml.presentation';
    } else if (item.id === 'infographic') {
      content = `<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600"><rect width="800" height="600" fill="#0f172a"/><text x="40" y="80" fill="#a855f7" font-size="24" font-weight="bold">UCKR Infographic Deliverable</text><text x="40" y="140" fill="#f8fafc" font-size="16">${deliverables?.infographic?.keyMessage || 'Key Insights'}</text></svg>`;
      mimeType = 'image/svg+xml';
    } else if (item.id === 'video') {
      content = JSON.stringify(deliverables?.video || { package: 'Full Video Production Package' }, null, 2);
      mimeType = 'application/zip';
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = item.filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportSelected = () => {
    const selectedList = EXPORT_ITEMS.filter(item => selectedExports[item.filename]);
    if (selectedList.length === 0) {
      onShowToast('No Files Selected', 'Please check at least one deliverable to export.', 'info');
      return;
    }

    selectedList.forEach(item => {
      downloadFile(item);
    });

    onShowToast('Export Complete', `Exported ${selectedList.length} files successfully.`, 'success');
  };

  const selectedCount = Object.values(selectedExports).filter(Boolean).length;

  return (
    <div className="rounded-2xl border border-slate-800 bg-[#0d121f] p-5 sm:p-6 shadow-xl space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-bold text-white tracking-tight uppercase">
              EXPORT
            </h3>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-purple-500/10 text-purple-300 border border-purple-500/20">
              CENTRAL DOWNLOAD HUB
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Download individual artifacts or batch export full multi-channel packages
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <button
            onClick={() => handleSelectAll(true)}
            className="text-purple-400 hover:text-purple-300 font-medium cursor-pointer"
          >
            Select All
          </button>
          <span className="text-slate-600">|</span>
          <button
            onClick={() => handleSelectAll(false)}
            className="text-slate-400 hover:text-white font-medium cursor-pointer"
          >
            Deselect All
          </button>
        </div>
      </div>

      {/* Checklist Grid */}
      <div className="space-y-2.5">
        <div className="text-xs font-mono font-semibold text-slate-400 uppercase tracking-wider mb-2">
          Download:
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
          {EXPORT_ITEMS.map((item) => {
            const isChecked = !!selectedExports[item.filename];
            const Icon = item.icon;

            return (
              <div
                key={item.filename}
                onClick={() => toggleItem(item.filename)}
                className={`p-3 rounded-xl border transition-all cursor-pointer select-none flex items-center justify-between gap-3 ${
                  isChecked 
                    ? 'bg-purple-950/20 border-purple-500/40 text-white' 
                    : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <div className={`w-4 h-4 rounded flex items-center justify-center border transition-colors ${
                    isChecked ? 'bg-purple-600 border-purple-500 text-white' : 'border-slate-600 bg-slate-950'
                  }`}>
                    {isChecked && <Check className="w-3 h-3 stroke-[3]" />}
                  </div>
                  <Icon className={`w-4 h-4 ${item.color} shrink-0`} />
                  <span className="font-mono text-xs font-semibold truncate">{item.filename}</span>
                </div>

                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-950 text-slate-400 border border-slate-800">
                  {item.format}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Action Buttons: [ Export Selected ] [ Export All ] */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-800/80">
        <span className="text-xs font-mono text-slate-400">
          Selected: <strong className="text-white font-normal">{selectedCount} of {EXPORT_ITEMS.length} files</strong>
        </span>

        <div className="flex items-center gap-3">
          <button
            onClick={handleExportSelected}
            disabled={selectedCount === 0}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white text-xs font-semibold shadow-md shadow-purple-600/20 transition-all cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>[ Export Selected ]</span>
          </button>

          <button
            onClick={onExportAll}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white text-xs font-semibold transition-all cursor-pointer"
          >
            <Package className="w-3.5 h-3.5 text-purple-400" />
            <span>[ Export All ]</span>
          </button>
        </div>
      </div>
    </div>
  );
};
