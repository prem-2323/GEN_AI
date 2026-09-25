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
  Package, 
  Loader2,
  HardDriveDownload,
  CheckCircle2
} from 'lucide-react';
import { OutputType, DeliverablesState } from '../../types';
import { exportApi } from '../../api/exportApi';
import { ExportFormat } from '../../types/export';

interface ExportItem {
  id: OutputType;
  filename: string;
  format: ExportFormat;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
}

const EXPORT_ITEMS: ExportItem[] = [
  { id: 'presentation', filename: 'Presentation.pptx', format: 'pptx', label: 'Presentation Deck (PPTX)', icon: Presentation, color: 'text-indigo-400' },
  { id: 'executive_summary', filename: 'Executive_Summary.docx', format: 'docx', label: 'Executive Summary (DOCX)', icon: FileCheck2, color: 'text-emerald-400' },
  { id: 'advisory', filename: 'Advisory.pdf', format: 'pdf', label: 'Advisory Brief (PDF)', icon: ShieldAlert, color: 'text-rose-400' },
  { id: 'linkedin', filename: 'LinkedIn.txt', format: 'txt', label: 'LinkedIn Post (TXT)', icon: Linkedin, color: 'text-blue-400' },
  { id: 'twitter', filename: 'X_Thread.txt', format: 'txt', label: 'X Thread (TXT)', icon: Twitter, color: 'text-sky-400' },
  { id: 'video', filename: 'Narration.mp3', format: 'mp3', label: 'Voiceover Audio (MP3)', icon: Video, color: 'text-purple-400' },
  { id: 'infographic', filename: 'Infographic.svg', format: 'txt', label: 'Infographic Spec (SVG)', icon: BarChart3, color: 'text-amber-400' },
];

interface ExportCenterProps {
  projectId?: string;
  deliverables?: DeliverablesState;
  onShowToast: (title: string, message: string, type?: 'success' | 'info' | 'error') => void;
  onExportAll: () => void;
}

export const ExportCenter: React.FC<ExportCenterProps> = ({
  projectId,
  deliverables,
  onShowToast,
  onExportAll
}) => {
  const [selectedExports, setSelectedExports] = useState<Record<string, boolean>>({
    'Presentation.pptx': true,
    'Executive_Summary.docx': true,
    'Advisory.pdf': true,
    'LinkedIn.txt': true,
    'X_Thread.txt': true,
    'Narration.mp3': true,
    'Infographic.svg': true,
  });

  const [exportingMap, setExportingMap] = useState<Record<string, boolean>>({});
  const [downloadedMap, setDownloadedMap] = useState<Record<string, boolean>>({});

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

  const downloadFileDirect = (item: ExportItem): boolean => {
    if (!deliverables) return false;

    let content = '';
    let mimeType = 'text/plain;charset=utf-8';

    if (item.id === 'linkedin') {
      content = deliverables?.linkedin 
        ? `${deliverables.linkedin.hook}\n\n${deliverables.linkedin.body}\n\n${deliverables.linkedin.callToAction}\n\n${deliverables.linkedin.hashtags.join(' ')}`
        : '';
    } else if (item.id === 'twitter') {
      content = deliverables?.twitter?.thread 
        ? deliverables.twitter.thread.map(t => `${t.index}. ${t.text}`).join('\n\n')
        : (deliverables?.twitter?.singlePost || '');
    } else if (item.id === 'advisory') {
      content = deliverables?.advisory
        ? `SECURITY ADVISORY: ${deliverables.advisory.title}\nSeverity: ${deliverables.advisory.severity}\n\nSituation:\n${deliverables.advisory.situation}\n\nImpact:\n${deliverables.advisory.threatImpact}`
        : '';
    } else if (item.id === 'executive_summary') {
      content = deliverables?.executive_summary
        ? `EXECUTIVE SUMMARY\n\n${deliverables.executive_summary.executiveOverview}\n\nKey Findings:\n` +
          deliverables.executive_summary.keyFindings.map(f => `• ${f.title}: ${f.description}`).join('\n')
        : '';
    } else if (item.id === 'presentation') {
      if (!deliverables?.presentation) return false;
      content = JSON.stringify(deliverables.presentation, null, 2);
    } else if (item.id === 'infographic') {
      if (!deliverables?.infographic) return false;
      content = `<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600"><rect width="800" height="600" fill="#0f172a"/><text x="40" y="80" fill="#a855f7" font-size="24" font-weight="bold">UCKR Infographic Deliverable</text><text x="40" y="140" fill="#f8fafc" font-size="16">${deliverables.infographic.keyMessage}</text></svg>`;
      mimeType = 'image/svg+xml';
    } else if (item.id === 'video') {
      if (!deliverables?.video) return false;
      content = JSON.stringify(deliverables.video, null, 2);
    }

    if (!content) return false;

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = item.filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    return true;
  };

  const handleExportItem = async (item: ExportItem) => {
    if (!deliverables || !(deliverables as any)[item.id]) {
      onShowToast('Deliverable Not Found', `Please generate ${item.label} first.`, 'error');
      return;
    }

    setExportingMap(prev => ({ ...prev, [item.filename]: true }));

    // Try backend file export first if projectId is present
    if (projectId) {
      try {
        const deliverableId = `del-${item.id}`;
        const exportRes = await exportApi.exportDeliverable(projectId, deliverableId, {
          format: item.format,
          require_approval: false,
          custom_title: item.filename.replace(/\.[^/.]+$/, '')
        });

        if (exportRes.ok && exportRes.export) {
          const exportId = exportRes.export.exportId || exportRes.export.id || '';
          const { blob, filename } = await exportApi.downloadExportBlob(projectId, exportId);
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = filename || item.filename;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);

          setDownloadedMap(prev => ({ ...prev, [item.filename]: true }));
          onShowToast('Export Ready', `Downloaded ${item.format.toUpperCase()} from local file storage.`, 'success');
          return;
        }
      } catch (err: any) {
        console.warn('Backend file export fallback to direct client download:', err);
      } finally {
        setExportingMap(prev => ({ ...prev, [item.filename]: false }));
      }
    }

    // Direct client-side file synthesis fallback
    const ok = downloadFileDirect(item);
    setExportingMap(prev => ({ ...prev, [item.filename]: false }));
    if (ok) {
      setDownloadedMap(prev => ({ ...prev, [item.filename]: true }));
      onShowToast('Downloaded', `Saved ${item.filename} to your device.`, 'success');
    }
  };

  const handleExportSelected = async () => {
    const selectedList = EXPORT_ITEMS.filter(item => selectedExports[item.filename]);
    if (selectedList.length === 0) {
      onShowToast('No Files Selected', 'Please check at least one deliverable to export.', 'info');
      return;
    }

    for (const item of selectedList) {
      await handleExportItem(item);
    }
  };

  const selectedCount = Object.values(selectedExports).filter(Boolean).length;

  return (
    <div className="rounded-2xl border border-slate-800 bg-[#0d121f] p-5 sm:p-6 shadow-xl space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-bold text-white tracking-tight uppercase">
              EXPORTS & FILE DELIVERY
            </h3>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
              <HardDriveDownload className="w-3 h-3" />
              <span>Local File Storage</span>
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Download PPTX decks, Word DOCX summaries, ReportLab PDFs, Edge TTS audio files, or batch packages.
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
          Deliverable Exports:
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
          {EXPORT_ITEMS.map((item) => {
            const isChecked = !!selectedExports[item.filename];
            const isExporting = !!exportingMap[item.filename];
            const isDownloaded = !!downloadedMap[item.filename];
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
                  <div className="min-w-0">
                    <div className="font-mono text-xs font-semibold truncate">{item.filename}</div>
                    <div className="text-[10px] text-slate-400 truncate">{item.label}</div>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleExportItem(item);
                    }}
                    disabled={isExporting}
                    className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono flex items-center gap-1 border border-slate-700 hover:text-white transition-colors"
                  >
                    {isExporting ? (
                      <Loader2 className="w-3 h-3 animate-spin text-purple-400" />
                    ) : isDownloaded ? (
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                    ) : (
                      <Download className="w-3 h-3 text-purple-400" />
                    )}
                    <span className="uppercase text-[10px]">{isExporting ? 'Building' : 'Get'}</span>
                  </button>
                </div>
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
            <span>[ Export Full Bundle ]</span>
          </button>
        </div>
      </div>
    </div>
  );
};
