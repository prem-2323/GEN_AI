import React, { useState } from 'react';
import { 
  Sparkles, 
  ArrowRight, 
  FolderKanban, 
  FileText, 
  Cpu, 
  Share2, 
  Clock, 
  UploadCloud, 
  Bot, 
  ShieldCheck, 
  Check, 
  Layers, 
  FileCode2,
  Linkedin,
  Twitter,
  ShieldAlert,
  BarChart3,
  Presentation,
  Video,
  FileCheck2,
  ChevronRight
} from 'lucide-react';
import { ViewState, SourceFile } from '../../types';

interface DashboardViewProps {
  onNavigate: (view: ViewState) => void;
  onQuickStartUpload: (file: Partial<SourceFile>) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  onNavigate,
  onQuickStartUpload
}) => {
  const [activeTab, setActiveTab] = useState<'upload' | 'paste' | 'context'>('upload');
  const [pastedText, setPastedText] = useState('');
  const [contextNotes, setContextNotes] = useState('');
  const [dragActive, setDragActive] = useState(false);

  const stats = [
    { label: 'Sources Processed', value: '0', change: 'Upload your first source', icon: FileText },
    { label: 'Outputs Generated', value: '0', change: 'Across 7 formats', icon: Layers },
    { label: 'Active AI Agents', value: '0', change: 'Connect via API', icon: Bot },
    { label: 'Time Saved', value: '0 hrs', change: 'Run a transformation', icon: Clock }
  ];

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      onQuickStartUpload({
        name: file.name,
        type: file.name.endsWith('.pdf') ? 'PDF' : file.name.endsWith('.docx') ? 'DOCX' : 'TXT',
        size: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
        extractedText: `Uploaded file content from: ${file.name}. Initializing semantic document analysis...`
      });
      onNavigate('new_transformation');
    }
  };

  const handlePastedSubmit = () => {
    if (!pastedText.trim()) return;
    onQuickStartUpload({
      name: 'Direct_Source_Text.txt',
      type: 'TEXT',
      size: `${(pastedText.length / 1024).toFixed(1)} KB`,
      extractedText: pastedText
    });
    onNavigate('new_transformation');
  };

  return (
    <div className="space-y-10 pb-16">
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-2xl border border-slate-800/80 bg-gradient-to-b from-[#12192a] via-[#0d1322] to-[#0b0f17] p-8 lg:p-12 shadow-2xl">
        {/* Subtle background glow */}
        <div className="absolute top-0 right-1/4 -mt-16 w-96 h-96 rounded-full bg-purple-600/10 blur-3xl pointer-events-none" />
        <div className="absolute -bottom-16 left-1/3 w-80 h-80 rounded-full bg-blue-600/10 blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-purple-500/10 border border-purple-500/20 text-purple-300 text-xs font-semibold tracking-wide uppercase mb-4">
            <Sparkles className="w-3.5 h-3.5 text-purple-400" />
            AI Content Transformation Platform
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white leading-tight">
            Transform information into communication.
          </h1>

          <p className="mt-4 text-base sm:text-lg text-slate-300 leading-relaxed max-w-2xl">
            Upload one source. Configure your requirements. Generate multiple professional deliverables with enterprise AI.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-3.5">
            <button
              onClick={() => onNavigate('new_transformation')}
              className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-purple-600 via-indigo-600 to-blue-600 hover:from-purple-500 hover:via-indigo-500 hover:to-blue-500 text-white text-sm font-semibold shadow-lg shadow-purple-600/25 hover:shadow-purple-600/40 transition-all cursor-pointer"
            >
              <Sparkles className="w-4 h-4" />
              <span>+ New Transformation</span>
              <ArrowRight className="w-4 h-4" />
            </button>

            <button
              onClick={() => onNavigate('projects')}
              className="flex items-center gap-2 px-5 py-3 rounded-xl bg-slate-800/80 hover:bg-slate-800 border border-slate-700 text-slate-200 hover:text-white text-sm font-medium transition-colors cursor-pointer"
            >
              <FolderKanban className="w-4 h-4 text-slate-400" />
              <span>View Projects</span>
            </button>
          </div>
        </div>

        {/* Hero Visual: One Source Becoming Multiple Outputs */}
        <div className="mt-10 pt-8 border-t border-slate-800/80">
          <div className="text-xs uppercase font-semibold text-slate-400 tracking-wider mb-4 flex items-center justify-between">
            <span>Transformation Flow</span>
            <span className="text-[11px] text-purple-400 lowercase font-normal">one source → ai analysis → multi-channel deliverables</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-center">
            {/* Source Box */}
            <div className="md:col-span-3 p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-500/15 border border-blue-500/30 flex items-center justify-center shrink-0">
                <FileText className="w-5 h-5 text-blue-400" />
              </div>
              <div className="min-w-0">
                <div className="text-xs font-semibold text-white truncate">1. Source Content</div>
                <div className="text-[11px] text-slate-400 truncate">PDF · DOCX · Reports · Research</div>
              </div>
            </div>

            {/* Transition Arrow 1 */}
            <div className="hidden md:flex md:col-span-1 justify-center text-purple-400">
              <ArrowRight className="w-5 h-5 animate-pulse" />
            </div>

            {/* AI Core Box */}
            <div className="md:col-span-3 p-3.5 rounded-xl bg-purple-950/40 border border-purple-500/40 flex items-center gap-3 shadow-md shadow-purple-900/20">
              <div className="w-10 h-10 rounded-lg bg-purple-500/20 border border-purple-400/40 flex items-center justify-center shrink-0">
                <Cpu className="w-5 h-5 text-purple-300" />
              </div>
              <div className="min-w-0">
                <div className="text-xs font-semibold text-purple-200 truncate">2. AI Understanding</div>
                <div className="text-[11px] text-purple-300/70 truncate">OCR · Semantic · Intent Map</div>
              </div>
            </div>

            {/* Transition Arrow 2 */}
            <div className="hidden md:flex md:col-span-1 justify-center text-purple-400">
              <ArrowRight className="w-5 h-5 animate-pulse" />
            </div>

            {/* Multiple Deliverables Box */}
            <div className="md:col-span-4 p-3.5 rounded-xl bg-slate-900/90 border border-slate-800">
              <div className="text-xs font-semibold text-white mb-2 flex items-center justify-between">
                <span>3. Deliverables</span>
                <span className="text-[10px] text-emerald-400 font-mono">Simultaneous</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                <span className="inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded bg-slate-800 text-slate-200 border border-slate-700">
                  <Linkedin className="w-2.5 h-2.5 text-blue-400" /> LinkedIn
                </span>
                <span className="inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded bg-slate-800 text-slate-200 border border-slate-700">
                  <Twitter className="w-2.5 h-2.5 text-sky-400" /> X / Twitter
                </span>
                <span className="inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded bg-slate-800 text-slate-200 border border-slate-700">
                  <FileText className="w-2.5 h-2.5 text-rose-400" /> Advisory
                </span>
                <span className="inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded bg-slate-800 text-slate-200 border border-slate-700">
                  <BarChart3 className="w-2.5 h-2.5 text-amber-400" /> Infographic
                </span>
                <span className="inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded bg-slate-800 text-slate-200 border border-slate-700">
                  <Presentation className="w-2.5 h-2.5 text-indigo-400" /> Slides
                </span>
                <span className="inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded bg-slate-800 text-slate-200 border border-slate-700">
                  <Video className="w-2.5 h-2.5 text-purple-400" /> Video
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Dashboard Statistics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, i) => {
          const Icon = stat.icon;
          return (
            <div 
              key={i}
              className="p-5 rounded-xl bg-[#0e1422] border border-slate-800/80 hover:border-slate-700 transition-colors"
            >
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-medium">{stat.label}</span>
                <Icon className="w-4 h-4 text-purple-400" />
              </div>
              <div className="text-2xl sm:text-3xl font-bold text-white font-mono tracking-tight tabular-nums">
                {stat.value}
              </div>
              <div className="mt-1 text-[11px] text-slate-400">
                {stat.change}
              </div>
            </div>
          );
        })}
      </div>

      {/* Main Transformation Card: Quick Start / Dropzone */}
      <div className="rounded-2xl border border-slate-800 bg-[#0d121f] p-6 lg:p-8 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">Start a new transformation</h2>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Give the AI your source content and tell it what you need.
            </p>
          </div>

          {/* Input Method Tabs */}
          <div className="flex items-center gap-1 p-1 bg-slate-900 border border-slate-800 rounded-lg self-start sm:self-auto">
            <button
              onClick={() => setActiveTab('upload')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors cursor-pointer ${
                activeTab === 'upload' ? 'bg-purple-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
            >
              Upload Files
            </button>
            <button
              onClick={() => setActiveTab('paste')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors cursor-pointer ${
                activeTab === 'paste' ? 'bg-purple-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
            >
              Paste Text
            </button>
            <button
              onClick={() => setActiveTab('context')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors cursor-pointer ${
                activeTab === 'context' ? 'bg-purple-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
            >
              Add Context
            </button>
          </div>
        </div>

        {/* Tab 1: Upload Files */}
        {activeTab === 'upload' && (
          <div className="space-y-5">
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => onNavigate('new_transformation')}
              className={`
                border-2 border-dashed rounded-xl p-8 sm:p-12 text-center cursor-pointer transition-all duration-200
                ${dragActive 
                  ? 'border-purple-500 bg-purple-500/10' 
                  : 'border-slate-800 hover:border-purple-500/60 bg-slate-900/40 hover:bg-slate-900/80'
                }
              `}
            >
              <div className="mx-auto w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400 mb-3 shadow-inner">
                <UploadCloud className="w-6 h-6" />
              </div>
              <p className="text-sm font-semibold text-white">
                Drop files here or click to browse
              </p>
              <p className="text-xs text-slate-400 mt-1">
                PDF • DOCX • TXT • JPG • PNG • MP4 • Up to 50 MB
              </p>
              <div className="mt-4 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 text-xs font-medium hover:bg-slate-700">
                Browse Files
              </div>
            </div>

            {/* No sample library — real uploads only */}
            <div>
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2.5 flex items-center justify-between">
                <span>Sample library removed</span>
                <span className="text-[11px] text-slate-400 lowercase font-normal">upload your own source to begin</span>
              </div>
              <div className="p-6 rounded-xl bg-slate-900/60 border border-dashed border-slate-800 text-center">
                <p className="text-xs text-slate-400">
                  No preset documents. Drop a file above or paste text to start a real transformation.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Paste Text */}
        {activeTab === 'paste' && (
          <div className="space-y-4">
            <div className="relative">
              <textarea
                value={pastedText}
                onChange={(e) => setPastedText(e.target.value)}
                placeholder="Paste article, report, prompt, advisory, research paper, or any source content..."
                rows={6}
                className="w-full rounded-xl bg-slate-900/90 border border-slate-800 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 p-4 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none transition-colors"
              />
              <div className="flex items-center justify-between mt-2 text-xs text-slate-400">
                <span>{pastedText.length} characters · {pastedText.trim() ? pastedText.trim().split(/\s+/).length : 0} words</span>
                <span className="text-purple-400 font-medium">Auto-detects structure & intent</span>
              </div>
            </div>

            <div className="flex justify-end">
              <button
                onClick={handlePastedSubmit}
                disabled={!pastedText.trim()}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-xs font-semibold transition-all shadow-md cursor-pointer"
              >
                <span>Continue to Transformation</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}

        {/* Tab 3: Add Context */}
        {activeTab === 'context' && (
          <div className="space-y-4">
            <p className="text-xs text-slate-300">
              Provide supplementary background notes, organizational guidelines, target URLs, or tone constraints:
            </p>
            <textarea
              value={contextNotes}
              onChange={(e) => setContextNotes(e.target.value)}
              placeholder="e.g. Target audience is non-technical board members; emphasize financial risk rather than packet-level details; embargo until 09:00 EST..."
              rows={4}
              className="w-full rounded-xl bg-slate-900/90 border border-slate-800 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 p-4 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none transition-colors"
            />
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400">Context is automatically merged with source documents.</span>
              <button
                onClick={() => onNavigate('new_transformation')}
                className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold transition-colors cursor-pointer"
              >
                Apply Context to Transformation
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
