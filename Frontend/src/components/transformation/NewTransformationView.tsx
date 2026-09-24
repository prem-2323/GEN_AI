import React, { useState, useEffect } from 'react';
import { 
  UploadCloud, 
  FileText, 
  Image as ImageIcon, 
  Video as VideoIcon, 
  CheckCircle2, 
  Eye, 
  Trash2, 
  RefreshCw, 
  Sparkles, 
  ChevronDown, 
  ArrowRight, 
  Cpu, 
  Sliders, 
  ShieldAlert, 
  Linkedin, 
  Twitter, 
  BarChart3, 
  Presentation, 
  Layers, 
  X,
  FileCheck,
  Zap,
  Info,
  SlidersHorizontal,
  Bell
} from 'lucide-react';
import { 
  SourceFile, 
  TransformationConfig, 
  OutputType, 
  AIAnalysis, 
  AudienceType, 
  ToneType, 
  LanguageType, 
  DetailLevel, 
  ObjectiveType, 
  ContentStyle,
  UckrKnowledgeBase
} from '../../types';
import { StatusBadge } from '../common/StatusBadge';
import { analyzeSourceContent, buildUckrKnowledge } from '../../services/aiService';

interface NewTransformationViewProps {
  source: SourceFile | null;
  config: TransformationConfig;
  selectedOutputs: OutputType[];
  analysis: AIAnalysis | null;
  uckr?: UckrKnowledgeBase | null;
  onUpdateSource: (source: SourceFile | null) => void;
  onUpdateConfig: (config: TransformationConfig) => void;
  onUpdateAnalysis: (analysis: AIAnalysis | null) => void;
  onUpdateUckr: (uckr: UckrKnowledgeBase | null) => void;
  onToggleOutput: (output: OutputType) => void;
  onSelectAllOutputs: () => void;
  onClearOutputs: () => void;
  onStartGeneration: () => void;
  onShowToast: (title: string, message: string, type?: 'success' | 'info' | 'error') => void;
}

export const NewTransformationView: React.FC<NewTransformationViewProps> = ({
  source,
  config,
  selectedOutputs,
  analysis,
  uckr,
  onUpdateSource,
  onUpdateConfig,
  onUpdateAnalysis,
  onUpdateUckr,
  onToggleOutput,
  onSelectAllOutputs,
  onClearOutputs,
  onStartGeneration,
  onShowToast
}) => {
  const activeUckr = uckr;
  const [inputTab, setInputTab] = useState<'upload' | 'paste' | 'context'>('upload');
  const [pasteContent, setPasteContent] = useState(source?.extractedText || '');
  const [showAnalysisModal, setShowAnalysisModal] = useState(false);
  const [showSourcePreviewModal, setShowSourcePreviewModal] = useState(false);
  const [contextNotes, setContextNotes] = useState(config.customNotes || '');
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Sync textarea if source changes
  useEffect(() => {
    if (source?.extractedText) {
      setPasteContent(source.extractedText);
    }
  }, [source?.extractedText]);

  // Run real AI analysis whenever a new source with text arrives and no analysis exists yet
  useEffect(() => {
    if (!source?.extractedText?.trim() || analysis || isAnalyzing) return;
    let cancelled = false;
    const run = async () => {
      setIsAnalyzing(true);
      try {
        const fresh = await analyzeSourceContent(source);
        if (cancelled) return;
        onUpdateAnalysis(fresh);
        try {
          const knowledge = await buildUckrKnowledge(source, fresh);
          if (!cancelled) onUpdateUckr(knowledge);
        } catch {
          // UCKR is optional — analysis alone unblocks configuration
        }
        onShowToast('Analysis Complete', 'Real AI understanding ready for configuration.', 'success');
      } catch (err) {
        if (!cancelled) {
          onShowToast('Analysis Failed', err instanceof Error ? err.message : 'Could not analyze source.', 'error');
        }
      } finally {
        if (!cancelled) setIsAnalyzing(false);
      }
    };
    run();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [source?.id]);

  const outputCards: {
    id: OutputType;
    name: string;
    description: string;
    icon: React.ElementType;
    badge: string;
    accentColor: string;
  }[] = [
    {
      id: 'linkedin',
      name: 'LinkedIn Post',
      description: 'Professional publication-ready post with hook, body, and CTA',
      icon: Linkedin,
      badge: 'Social',
      accentColor: 'border-blue-500/40 text-blue-400'
    },
    {
      id: 'twitter',
      name: 'Twitter / X Post',
      description: 'Platform-optimized post or multi-part threaded breakdown',
      icon: Twitter,
      badge: 'Social',
      accentColor: 'border-sky-500/40 text-sky-400'
    },
    {
      id: 'advisory',
      name: 'Advisory & Policy Brief',
      description: 'Structured formal advisory with executive overview, impact analysis & strategic action phases',
      icon: Bell,
      badge: 'Document',
      accentColor: 'border-rose-500/40 text-rose-400'
    },
    {
      id: 'infographic',
      name: 'Infographic Package',
      description: 'Key messaging, high-impact statistics, and visual wireframe layout',
      icon: BarChart3,
      badge: 'Visual',
      accentColor: 'border-amber-500/40 text-amber-400'
    },
    {
      id: 'executive_summary',
      name: 'Executive Summary',
      description: 'Concise executive briefing with metrics, findings & strategic roadmap',
      icon: FileCheck,
      badge: 'Document',
      accentColor: 'border-emerald-500/40 text-emerald-400'
    },
    {
      id: 'presentation',
      name: 'Presentation Deck',
      description: 'Multi-slide presentation deck complete with speaker notes and visuals',
      icon: Presentation,
      badge: 'Deck',
      accentColor: 'border-indigo-500/40 text-indigo-400'
    },
    {
      id: 'video',
      name: 'Video Production Package',
      description: 'Full video script, multi-scene storyboard, narration, and SRT subtitles',
      icon: VideoIcon,
      badge: 'Media',
      accentColor: 'border-purple-500/40 text-purple-400'
    }
  ];

  const toneOptions: ToneType[] = [
    'Professional',
    'Formal',
    'Informative',
    'Persuasive',
    'Urgent',
    'Friendly',
    'Technical'
  ];

  const audienceOptions: AudienceType[] = [
    'General Public',
    'Executives',
    'Government Officials',
    'Technical Team',
    'Security Team',
    'Customers',
    'Students',
    'Custom'
  ];

  const languageOptions: LanguageType[] = [
    'English',
    'Tamil',
    'Hindi',
    'Spanish',
    'French',
    'German',
    'Custom'
  ];

  const objectiveOptions: ObjectiveType[] = [
    'Inform',
    'Educate',
    'Alert',
    'Persuade',
    'Summarize',
    'Engage',
    'Brief'
  ];

  const styleOptions: ContentStyle[] = [
    'Professional',
    'Executive',
    'Technical',
    'Social Media',
    'News Style',
    'Storytelling',
    'Academic',
    'Custom'
  ];

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const isPdf = file.name.toLowerCase().endsWith('.pdf');
      const isDoc = file.name.toLowerCase().endsWith('.docx') || file.name.toLowerCase().endsWith('.doc');
      const isImg = file.type.startsWith('image/');
      const isVid = file.type.startsWith('video/');

      const fileType = isPdf ? 'PDF' : isDoc ? 'DOCX' : isImg ? 'IMAGE' : isVid ? 'VIDEO' : 'TXT';

      let extractedText = '';
      try {
        if (!isPdf && !isDoc && !isImg && !isVid && file.size < 5 * 1024 * 1024) {
          extractedText = await file.text();
        }
      } catch {
        extractedText = '';
      }
      if (!extractedText.trim()) {
        onShowToast(
          'Text Extraction Pending',
          `"${file.name}" was added with metadata only — the browser cannot read ${fileType} content directly. Paste the text or wait for backend extraction.`,
          'info'
        );
      }

      onUpdateAnalysis(null);
      onUpdateUckr(null);
      onUpdateSource({
        id: `src-${Date.now()}`,
        name: file.name,
        type: fileType,
        size: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
        pages: undefined,
        status: 'ready',
        uploadedAt: new Date().toISOString(),
        extractedText
      });
    }
  };

  const handleApplyPaste = () => {
    if (!pasteContent.trim()) return;
    onUpdateAnalysis(null);
    onUpdateUckr(null);
    onUpdateSource({
      id: `src-text-${Date.now()}`,
      name: 'Pasted_Source_Text.txt',
      type: 'TEXT',
      size: `${(pasteContent.length / 1024).toFixed(1)} KB`,
      status: 'ready',
      uploadedAt: new Date().toISOString(),
      extractedText: pasteContent
    });
  };

  const handleClearSource = () => {
    onUpdateSource(null);
    onUpdateAnalysis(null);
    onUpdateUckr(null);
  };

  return (
    <div className="space-y-10 pb-28">
      {/* Page Header */}
      <div className="border-b border-slate-800 pb-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-1.5 text-xs font-semibold text-purple-400 uppercase tracking-wider mb-2">
              <Sparkles className="w-3.5 h-3.5" />
              Content Transformation Studio
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Start a new transformation
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Give the AI your source content and tell it what you need.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onSelectAllOutputs}
              className="px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-800/80 hover:bg-slate-800 rounded-lg border border-slate-700 transition-colors"
            >
              Select All (7)
            </button>
            <button
              onClick={onClearOutputs}
              className="px-3 py-1.5 text-xs font-medium text-slate-400 hover:text-slate-200 bg-slate-900 rounded-lg border border-slate-800 transition-colors"
            >
              Clear
            </button>
          </div>
        </div>
      </div>

      {/* SECTION 1: SOURCE INGESTION */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <span className="w-7 h-7 rounded-full bg-purple-600/30 text-purple-300 text-xs font-mono font-bold flex items-center justify-center border border-purple-500/40">
              01
            </span>
            <div>
              <h2 className="text-base sm:text-lg font-bold text-white tracking-tight">
                SOURCE CONTENT
              </h2>
              <p className="text-xs text-slate-400">Upload or select the source material to transform</p>
            </div>
          </div>

          {/* Input Tabs */}
          <div className="flex items-center gap-1 p-1 bg-slate-900/90 border border-slate-800 rounded-lg">
            <button
              onClick={() => setInputTab('upload')}
              className={`px-3 py-1 text-xs font-semibold rounded-md transition-colors cursor-pointer ${
                inputTab === 'upload' ? 'bg-purple-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Upload Files
            </button>
            <button
              onClick={() => setInputTab('paste')}
              className={`px-3 py-1 text-xs font-semibold rounded-md transition-colors cursor-pointer ${
                inputTab === 'paste' ? 'bg-purple-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Paste Text
            </button>
            <button
              onClick={() => setInputTab('context')}
              className={`px-3 py-1 text-xs font-semibold rounded-md transition-colors cursor-pointer ${
                inputTab === 'context' ? 'bg-purple-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Add Context
            </button>
          </div>
        </div>

        {/* Input Tab Contents */}
        {inputTab === 'upload' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Upload Box */}
            <div className="relative border-2 border-dashed border-slate-800 hover:border-purple-500/50 rounded-xl p-6 bg-slate-900/40 hover:bg-slate-900/70 transition-all flex flex-col items-center justify-center text-center">
              <input
                type="file"
                onChange={handleFileUpload}
                className="absolute inset-0 opacity-0 cursor-pointer w-full h-full z-10"
                accept=".pdf,.docx,.doc,.txt,.jpg,.jpeg,.png,.mp4"
              />
              <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400 mb-2">
                <UploadCloud className="w-5 h-5" />
              </div>
              <p className="text-sm font-semibold text-white">
                Drop files here or click to browse
              </p>
              <p className="text-xs text-slate-400 mt-1">
                PDF • DOCX • TXT • JPG • PNG • MP4
              </p>
            </div>

            {/* Currently Active Source Card */}
            <div className="rounded-xl border border-slate-800 bg-[#0d121f] p-4 flex flex-col justify-between">
              {!source ? (
                <div className="p-6 text-center space-y-2">
                  <p className="text-sm font-semibold text-white">No source selected</p>
                  <p className="text-xs text-slate-400">Upload a file or paste text to begin. Real AI analysis runs automatically.</p>
                  {isAnalyzing && <p className="text-xs text-purple-300 animate-pulse">Analyzing with Gemini…</p>}
                </div>
              ) : (
              <div>
                <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Active Source
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-lg bg-purple-500/15 border border-purple-500/30 flex items-center justify-center shrink-0">
                    {source.type === 'PDF' && <FileText className="w-5 h-5 text-purple-400" />}
                    {source.type === 'IMAGE' && <ImageIcon className="w-5 h-5 text-cyan-400" />}
                    {source.type === 'VIDEO' && <VideoIcon className="w-5 h-5 text-amber-400" />}
                    {(source.type === 'DOCX' || source.type === 'TXT' || source.type === 'TEXT') && (
                      <FileText className="w-5 h-5 text-blue-400" />
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-semibold text-white truncate">
                      {source.name}
                    </div>
                    <div className="flex items-center gap-2 text-xs text-slate-400 mt-0.5">
                      <span>Type: {source.type}</span>
                      <span>·</span>
                      {source.pages && <span>{source.pages} pages ·</span>}
                      <span>{source.size}</span>
                    </div>
                  </div>
                </div>

                <div className="mt-3 flex items-center gap-1.5">
                  <StatusBadge status={source.status || 'ready'} size="xs" />
                  {isAnalyzing && <span className="text-[11px] text-purple-300 animate-pulse">Analyzing…</span>}
                  {!isAnalyzing && !analysis && <span className="text-[11px] text-amber-300">Analysis pending — check API key</span>}
                  {!isAnalyzing && analysis && <span className="text-[11px] text-emerald-300">✓ Analyzed: {analysis.detectedTopic.slice(0, 40)}</span>}
                </div>
              </div>
              )}

              <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center gap-2">
                <button
                  onClick={() => setShowSourcePreviewModal(true)}
                  disabled={!source}
                  className="flex-1 flex items-center justify-center gap-1.5 py-1.5 px-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-200 hover:text-white text-xs font-medium transition-colors cursor-pointer"
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>Preview Source</span>
                </button>
                <button
                  onClick={handleClearSource}
                  className="flex items-center justify-center gap-1 py-1.5 px-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white text-xs font-medium transition-colors cursor-pointer"
                  title="Clear current source"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Clear</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {inputTab === 'paste' && (
          <div className="rounded-xl border border-slate-800 bg-[#0d121f] p-4 space-y-3">
            <textarea
              value={pasteContent}
              onChange={(e) => setPasteContent(e.target.value)}
              placeholder="Paste article, report, prompt, advisory, research paper or any source content..."
              rows={6}
              className="w-full rounded-lg bg-slate-900 border border-slate-800 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 p-3.5 text-sm text-slate-200 focus:outline-none"
            />
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400 font-mono">
                {pasteContent.length} characters · {pasteContent.trim() ? pasteContent.trim().split(/\s+/).length : 0} words
              </span>
              <button
                onClick={handleApplyPaste}
                disabled={!pasteContent.trim()}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white font-medium text-xs transition-colors cursor-pointer"
              >
                <span>Save & Parse Source</span>
                <CheckCircle2 className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}

        {inputTab === 'context' && (
          <div className="rounded-xl border border-slate-800 bg-[#0d121f] p-4 space-y-3">
            <p className="text-xs text-slate-300">
              Add contextual nuances such as internal acronym definitions, strict compliance frameworks, or non-public background:
            </p>
            <textarea
              value={contextNotes}
              onChange={(e) => {
                setContextNotes(e.target.value);
                onUpdateConfig({ ...config, customNotes: e.target.value });
              }}
              placeholder="e.g. Target audience is leadership; emphasize executive takeaways; reference corporate policy, governance or statutory frameworks..."
              rows={4}
              className="w-full rounded-lg bg-slate-900 border border-slate-800 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 p-3.5 text-sm text-slate-200 focus:outline-none"
            />
            <span className="text-[11px] text-slate-400 block">
              Context will be injected into all AI agent transformation prompts.
            </span>
          </div>
        )}
      </div>

      {/* SECTION 2: CONFIGURE OUTPUT */}
      <div className="rounded-2xl border border-slate-800 bg-[#0d121f] p-6 space-y-6">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="w-7 h-7 rounded-full bg-purple-600/30 text-purple-300 text-xs font-mono font-bold flex items-center justify-center border border-purple-500/40">
              02
            </span>
            <div>
              <h2 className="text-base sm:text-lg font-bold text-white tracking-tight">
                CONFIGURE OUTPUT
              </h2>
              <p className="text-xs text-slate-400">
                These settings control how the source facts and takeaways are formatted and delivered.
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {/* Target Audience */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-300">Target Audience</label>
            <div className="relative">
              <select
                value={config.targetAudience}
                onChange={(e) => onUpdateConfig({ ...config, targetAudience: e.target.value as AudienceType })}
                className="w-full rounded-xl bg-slate-900 border border-slate-800 p-2.5 text-xs text-white focus:outline-none focus:border-purple-500 appearance-none cursor-pointer"
              >
                {audienceOptions.map((aud) => (
                  <option key={aud} value={aud}>{aud}</option>
                ))}
              </select>
              <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-3 pointer-events-none" />
            </div>
          </div>

          {/* Language */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-300">Language</label>
            <div className="relative">
              <select
                value={config.language}
                onChange={(e) => onUpdateConfig({ ...config, language: e.target.value as LanguageType })}
                className="w-full rounded-xl bg-slate-900 border border-slate-800 p-2.5 text-xs text-white focus:outline-none focus:border-purple-500 appearance-none cursor-pointer"
              >
                {languageOptions.map((lang) => (
                  <option key={lang} value={lang}>{lang}</option>
                ))}
              </select>
              <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-3 pointer-events-none" />
            </div>
          </div>

          {/* Communication Objective */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-300">Communication Objective</label>
            <div className="relative">
              <select
                value={config.objective}
                onChange={(e) => onUpdateConfig({ ...config, objective: e.target.value as ObjectiveType })}
                className="w-full rounded-xl bg-slate-900 border border-slate-800 p-2.5 text-xs text-white focus:outline-none focus:border-purple-500 appearance-none cursor-pointer"
              >
                {objectiveOptions.map((obj) => (
                  <option key={obj} value={obj}>{obj}</option>
                ))}
              </select>
              <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-3 pointer-events-none" />
            </div>
          </div>

          {/* Content Style */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-300">Content Style</label>
            <div className="relative">
              <select
                value={config.contentStyle}
                onChange={(e) => onUpdateConfig({ ...config, contentStyle: e.target.value as ContentStyle })}
                className="w-full rounded-xl bg-slate-900 border border-slate-800 p-2.5 text-xs text-white focus:outline-none focus:border-purple-500 appearance-none cursor-pointer"
              >
                {styleOptions.map((style) => (
                  <option key={style} value={style}>{style}</option>
                ))}
              </select>
              <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-3 pointer-events-none" />
            </div>
          </div>

          {/* Level of Detail Slider */}
          <div className="space-y-2 sm:col-span-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-semibold text-slate-300">Level of Detail</span>
              <span className="text-purple-400 font-semibold">{config.levelOfDetail}</span>
            </div>
            <div className="flex items-center gap-3 pt-1">
              {(['Concise', 'Balanced', 'Detailed'] as DetailLevel[]).map((level) => (
                <button
                  key={level}
                  onClick={() => onUpdateConfig({ ...config, levelOfDetail: level })}
                  className={`flex-1 py-2 text-xs font-medium rounded-lg border transition-all cursor-pointer ${
                    config.levelOfDetail === level
                      ? 'bg-purple-600/20 border-purple-500 text-purple-300 shadow-sm'
                      : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white'
                  }`}
                >
                  {level}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Tone Selectable Cards */}
        <div className="space-y-2 pt-2">
          <label className="text-xs font-semibold text-slate-300">Tone of Voice</label>
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
            {toneOptions.map((tone) => (
              <button
                key={tone}
                onClick={() => onUpdateConfig({ ...config, tone })}
                className={`py-2 px-3 rounded-lg text-xs font-medium border text-center transition-all cursor-pointer ${
                  config.tone === tone
                    ? 'bg-purple-600 text-white border-purple-500 shadow-md shadow-purple-600/20'
                    : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800'
                }`}
              >
                {tone}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* SECTION 3: SELECT DELIVERABLES */}
      <div className="space-y-4">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="w-7 h-7 rounded-full bg-purple-600/30 text-purple-300 text-xs font-mono font-bold flex items-center justify-center border border-purple-500/40">
              03
            </span>
            <div>
              <h2 className="text-base sm:text-lg font-bold text-white tracking-tight">
                SELECT DELIVERABLES
              </h2>
              <p className="text-xs sm:text-sm text-slate-400">
                Choose the deliverables to generate. All outputs draw simultaneously from the analyzed source content.
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5 pt-2">
          {outputCards.map((output) => {
            const isSelected = selectedOutputs.includes(output.id);
            const Icon = output.icon;
            return (
              <div
                key={output.id}
                onClick={() => onToggleOutput(output.id)}
                className={`
                  relative p-4 rounded-xl border transition-all cursor-pointer select-none flex flex-col justify-between
                  ${isSelected 
                    ? 'bg-purple-950/30 border-purple-500 shadow-lg shadow-purple-900/30 ring-1 ring-purple-500/50' 
                    : 'bg-[#0d121f] border-slate-800/80 hover:border-slate-700 hover:bg-slate-900/50'
                  }
                `}
              >
                <div>
                  <div className="flex items-center justify-between mb-2.5">
                    <div className={`w-9 h-9 rounded-lg flex items-center justify-center border bg-slate-900 ${output.accentColor}`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    {/* Checkbox indicator */}
                    <div className={`
                      w-5 h-5 rounded-md border flex items-center justify-center transition-colors
                      ${isSelected ? 'bg-purple-600 border-purple-500 text-white' : 'border-slate-700 bg-slate-900'}
                    `}>
                      {isSelected && <CheckCircle2 className="w-3.5 h-3.5" />}
                    </div>
                  </div>

                  <h3 className="text-sm font-bold text-white">
                    {output.name}
                  </h3>
                  <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                    {output.description}
                  </p>
                </div>

                <div className="mt-4 pt-2.5 border-t border-slate-800/60 flex items-center justify-between text-[11px]">
                  <span className="text-slate-400 font-medium">{output.badge}</span>
                  <span className={isSelected ? 'text-purple-400 font-semibold' : 'text-slate-400'}>
                    {isSelected ? '✓ Selected' : 'Click to select'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Floating Bottom Generation Bar */}
      <div className="fixed bottom-0 left-0 lg:left-72 right-0 z-30 p-4 bg-[#090d16]/95 backdrop-blur-xl border-t border-slate-800/80 shadow-2xl flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-sm font-semibold text-white">
            <span className="w-6 h-6 rounded-full bg-purple-600 text-white text-xs font-mono font-bold flex items-center justify-center">
              {selectedOutputs.length}
            </span>
            <span>deliverables selected</span>
          </div>
          <span className="text-slate-600 hidden sm:inline">|</span>
          <span className="text-xs text-slate-400 hidden sm:inline">
            Source: <strong className="text-slate-200 font-normal">{source?.name || 'No source selected'}</strong>
          </span>
        </div>

        <button
          onClick={onStartGeneration}
          disabled={!source || selectedOutputs.length === 0}
          className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 via-indigo-600 to-blue-600 hover:from-purple-500 hover:via-indigo-500 hover:to-blue-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold text-sm shadow-lg shadow-purple-600/30 transition-all cursor-pointer"
        >
          <Sparkles className="w-4 h-4" />
          <span>Generate Deliverables</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      {/* Modal: View AI Analysis Deep-Dive */}
      {showAnalysisModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-[#0e1422] border border-slate-800 rounded-2xl max-w-2xl w-full max-h-[85vh] overflow-y-auto p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center gap-2.5">
                <Cpu className="w-5 h-5 text-purple-400" />
                <h3 className="text-lg font-bold text-white">AI Understanding & Semantic Graph</h3>
              </div>
              <button
                onClick={() => setShowAnalysisModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {!analysis ? (
              <p className="text-xs text-slate-400">No analysis yet. Upload source content to run real AI understanding.</p>
            ) : (
            <div className="space-y-4 text-xs">
              <div>
                <span className="font-semibold text-slate-400 uppercase tracking-wider block mb-1">Detected Topic</span>
                <p className="text-sm font-bold text-purple-300">{analysis.detectedTopic}</p>
              </div>

              <div>
                <span className="font-semibold text-slate-400 uppercase tracking-wider block mb-1.5">Key Identified Entities</span>
                <div className="flex flex-wrap gap-1.5">
                  {analysis.keyEntities.map((entity, i) => (
                    <span key={i} className="px-2.5 py-1 rounded bg-slate-800 text-slate-200 border border-slate-700">
                      {entity}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <span className="font-semibold text-slate-400 uppercase tracking-wider block mb-1.5">Key Extracted Facts & Metrics</span>
                <ul className="space-y-1.5 list-disc pl-4 text-slate-300">
                  {analysis.importantFacts.map((fact, i) => (
                    <li key={i}>{fact}</li>
                  ))}
                </ul>
              </div>

              <div className="grid grid-cols-2 gap-3 pt-2">
                <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                  <span className="text-slate-400 font-semibold block mb-1">Audience Signals</span>
                  <p className="text-slate-200">{analysis.audienceSignals.join(', ')}</p>
                </div>
                <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                  <span className="text-slate-400 font-semibold block mb-1">Communication Objective</span>
                  <p className="text-slate-200">{analysis.communicationObjective}</p>
                </div>
              </div>
            </div>
            )}

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setShowAnalysisModal(false)}
                className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold"
              >
                Close Analysis
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Source Content Full Preview */}
      {showSourcePreviewModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-[#0e1422] border border-slate-800 rounded-2xl max-w-3xl w-full max-h-[85vh] flex flex-col p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
              <div className="flex items-center gap-2.5">
                <FileText className="w-5 h-5 text-purple-400" />
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-bold text-white">{source?.name || 'No source'}</h3>
                    <StatusBadge status={source?.status || 'ready'} size="xs" />
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">{source?.type} · {source?.size}</p>
                </div>
              </div>
              <button
                onClick={() => setShowSourcePreviewModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">
              {source?.extractedText || 'No extracted text found in source.'}
            </div>

            <div className="flex justify-end pt-4">
              <button
                onClick={() => setShowSourcePreviewModal(false)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
