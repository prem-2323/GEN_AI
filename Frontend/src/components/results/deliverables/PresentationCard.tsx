import React, { useState } from 'react';
import { 
  Presentation as PresentationIcon, 
  Download, 
  Edit3, 
  Play, 
  RotateCw, 
  CheckCircle2, 
  ChevronLeft, 
  ChevronRight, 
  Maximize2, 
  X,
  FileText,
  Sparkles,
  Palette,
  Loader2
} from 'lucide-react';
import { PresentationDeliverable, PresentationSlide } from '../../../types';
import { StatusBadge } from '../../common/StatusBadge';
import { PRESENTATION_THEMES, getPresentationTheme, PresentationTheme } from '../../../constants/presentationThemes';

interface PresentationCardProps {
  deliverable: PresentationDeliverable;
  onUpdate: (updated: PresentationDeliverable) => void;
  onShowToast: (title: string, message: string, type?: 'success' | 'info' | 'error') => void;
}

export const PresentationCard: React.FC<PresentationCardProps> = ({
  deliverable,
  onUpdate,
  onShowToast
}) => {
  const [activeSlideIndex, setActiveSlideIndex] = useState(0);
  const [isFullscreenPresent, setIsFullscreenPresent] = useState(false);
  const [isEditingSlide, setIsEditingSlide] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  const activeTheme: PresentationTheme = getPresentationTheme(deliverable.theme);
  const c = activeTheme.colors;

  const activeSlide = deliverable.slides[activeSlideIndex] || deliverable.slides[0];

  const handleSelectTheme = (themeId: string) => {
    if (themeId === deliverable.theme) return;
    const theme = getPresentationTheme(themeId);
    onUpdate({ ...deliverable, theme: theme.id });
    onShowToast('Theme Applied', `Deck theme set to ${theme.label}. Preview updated.`, 'success');
  };

  const handleNextSlide = () => {
    if (activeSlideIndex < deliverable.slides.length - 1) {
      setActiveSlideIndex(activeSlideIndex + 1);
    }
  };

  const handlePrevSlide = () => {
    if (activeSlideIndex > 0) {
      setActiveSlideIndex(activeSlideIndex - 1);
    }
  };

  const handleDownloadPptx = async () => {
    if (isExporting) return;
    setIsExporting(true);
    try {
      // Mirror the deck JSON into the backend generator's expected schema
      const presentation = {
        presentation_title: deliverable.deckTitle || deliverable.presentation_title || 'Executive Presentation',
        subtitle: deliverable.subtitle || activeSlide?.subtitle || '',
        theme: activeTheme.id,
        slides: deliverable.slides.map((s, idx) => ({
          slide_number: s.slideNumber ?? idx + 1,
          title: idx === 0 ? (deliverable.deckTitle || s.title) : s.title,
          layout: idx === 0 ? 'title' : (s.column_left?.length ? 'two_column' : 'bullet_points'),
          subtitle: s.subtitle || '',
          content: s.bullets || [],
          column_left: s.column_left,
          column_right: s.column_right,
          speaker_notes: s.speakerNotes || s.speaker_notes || '',
          visual_recommendation: s.visualRecommendation || s.visual_recommendation || '',
        })),
      };

      const baseUrl = (import.meta as unknown as { env?: Record<string, string | undefined> }).env
        ?.VITE_BACKEND_URL || 'http://127.0.0.1:8000';
      const res = await fetch(`${baseUrl}/api/presentation/export-pptx`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ presentation, theme: activeTheme.id, filename: `${deliverable.deckTitle || 'presentation'}.pptx` }),
      });

      if (!res.ok) {
        throw new Error(`Backend ${res.status}: ${await res.text().catch(() => res.statusText)}`);
      }

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${(deliverable.deckTitle || 'presentation').replace(/[^\w\-]+/g, '_')}.pptx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      onShowToast('PPTX Ready', `Downloaded themed deck (${activeTheme.label}).`, 'success');
    } catch (err) {
      // Fallback: JSON outline (previous behavior)
      const deckOutline = {
        title: deliverable.deckTitle,
        theme: activeTheme.id,
        exportedAt: new Date().toISOString(),
        slides: deliverable.slides.map(s => ({
          slide: s.slideNumber,
          title: s.title,
          subtitle: s.subtitle,
          bulletPoints: s.bullets,
          visualBrief: s.visualRecommendation,
          speakerNotes: s.speakerNotes
        }))
      };
      const blob = new Blob([JSON.stringify(deckOutline, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Slide_Deck_${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);
      onShowToast('Backend Unavailable', 'Exported deck outline as JSON instead of PPTX.', 'info');
    } finally {
      setIsExporting(false);
    }
  };

  const handleSaveSlideEdits = (updatedSlide: PresentationSlide) => {
    const newSlides = [...deliverable.slides];
    newSlides[activeSlideIndex] = updatedSlide;
    onUpdate({
      ...deliverable,
      slides: newSlides
    });
    setIsEditingSlide(false);
    onShowToast('Slide Updated', `Slide ${activeSlide.slideNumber} changes saved.`, 'info');
  };

  const bulletDot = activeTheme.isDarkTheme ? c.accent : c.accent;

  return (
    <div className="rounded-2xl border border-slate-800 bg-[#0d121f] p-6 space-y-6 shadow-xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-500/15 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <PresentationIcon className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-white">Presentation Workspace</h3>
              <StatusBadge status="ready" size="xs" />
              <span className="text-[11px] font-mono text-slate-400">({deliverable.totalSlides} Slides)</span>
            </div>
            <p className="text-xs text-slate-400">Executive slide deck with dedicated speaker notes & visual recommendations</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsFullscreenPresent(true)}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 transition-all cursor-pointer"
          >
            <Play className="w-3.5 h-3.5 fill-white" />
            <span>Present Fullscreen</span>
          </button>

          <button
            onClick={handleDownloadPptx}
            disabled={isExporting}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors disabled:opacity-60 cursor-pointer"
          >
            {isExporting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
            <span>{isExporting ? 'Exporting…' : 'Download PPTX'}</span>
          </button>
        </div>
      </div>

      {/* Theme Picker */}
      <div className="rounded-xl bg-slate-900/60 border border-slate-800 p-4">
        <div className="flex items-center gap-2 mb-3">
          <Palette className="w-3.5 h-3.5 text-indigo-400" />
          <span className="text-[11px] font-semibold text-white uppercase tracking-wider">Deck Theme</span>
          <span className="text-[11px] font-mono text-slate-500 ml-1">— applied live & on PPTX export</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {PRESENTATION_THEMES.map((theme) => {
            const isActive = theme.id === activeTheme.id;
            return (
              <button
                key={theme.id}
                onClick={() => handleSelectTheme(theme.id)}
                title={theme.label}
                className={`
                  group flex items-center gap-2 pl-2 pr-3 py-1.5 rounded-lg border text-xs font-medium transition-all cursor-pointer
                  ${isActive
                    ? 'border-indigo-400 bg-indigo-500/10 text-white ring-1 ring-indigo-400/50'
                    : 'border-slate-700 bg-slate-900 text-slate-300 hover:border-slate-500 hover:text-white'}
                `}
              >
                {/* Mini palette swatch */}
                <span
                  className="w-6 h-4 rounded-sm border border-slate-600/60 flex shrink-0 overflow-hidden"
                  aria-hidden="true"
                >
                  <span className="flex-1" style={{ backgroundColor: theme.colors.dark_bg }} />
                  <span className="flex-1" style={{ backgroundColor: theme.colors.accent }} />
                  <span className="flex-1" style={{ backgroundColor: theme.colors.box_bg }} />
                </span>
                {theme.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Slide Studio: 3-column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* Left: Slide Thumbnails List */}
        <div className="lg:col-span-3 space-y-2 max-h-[520px] overflow-y-auto pr-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Slide Thumbnails ({deliverable.slides.length})
          </span>
          {deliverable.slides.map((slide, idx) => {
            const isSelected = idx === activeSlideIndex;
            return (
              <button
                key={slide.slideNumber}
                onClick={() => setActiveSlideIndex(idx)}
                className={`
                  w-full text-left p-3 rounded-xl border transition-all cursor-pointer flex flex-col justify-between
                  ${isSelected 
                    ? 'bg-indigo-950/40 border-indigo-500 shadow-md ring-1 ring-indigo-500/40' 
                    : 'bg-slate-900/60 border-slate-800 hover:border-slate-700 text-slate-400 hover:text-slate-200'
                  }
                `}
              >
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="font-mono font-bold text-slate-300">
                    Slide {String(slide.slideNumber).padStart(2, '0')}
                  </span>
                  {isSelected && <span className="w-2 h-2 rounded-full bg-indigo-400" />}
                </div>
                <div className="text-xs font-semibold text-white truncate">
                  {slide.title}
                </div>
                <div className="text-[10px] text-slate-400 truncate mt-0.5">
                  {slide.bullets.length} bullet points
                </div>
              </button>
            );
          })}
        </div>

        {/* Center: Large Slide Preview Canvas (theme-styled) */}
        <div
          className="lg:col-span-6 rounded-2xl border p-8 min-h-[460px] flex flex-col justify-between relative shadow-2xl transition-colors"
          style={{
            backgroundColor: activeTheme.isDarkTheme ? c.dark_bg : c.light_bg,
            borderColor: c.card_border,
          }}
        >
          {/* Subtle slide watermark/badge */}
          <div
            className="flex items-center justify-between border-b pb-4"
            style={{ borderColor: activeTheme.isDarkTheme ? c.card_border : c.card_border }}
          >
            <div className="flex items-center gap-2">
              <span
                className="w-6 h-6 rounded-md font-mono font-bold text-xs flex items-center justify-center border"
                style={{
                  backgroundColor: activeTheme.isDarkTheme ? `${c.accent}22` : `${c.accent}1a`,
                  color: activeTheme.isDarkTheme ? c.accent : c.header,
                  borderColor: c.accent,
                }}
              >
                {activeSlide.slideNumber}
              </span>
              <span className="text-[11px] font-mono truncate max-w-[220px]" style={{ color: activeTheme.isDarkTheme ? c.subtitle_dark : c.muted }}>
                {deliverable.deckTitle}
              </span>
            </div>
            <span className="text-[10px] uppercase font-bold tracking-wider" style={{ color: c.accent }}>
              GEN TRANSFORM AI
            </span>
          </div>

          {/* Slide Content */}
          <div className="py-6 space-y-4">
            <div>
              <h2
                className="text-xl sm:text-2xl font-bold tracking-tight leading-snug"
                style={{ color: activeTheme.isDarkTheme ? c.title_dark : c.header }}
              >
                {activeSlide.title}
              </h2>
              {activeSlide.subtitle && (
                <p className="text-sm mt-1 font-medium" style={{ color: c.accent, opacity: 0.85 }}>
                  {activeSlide.subtitle}
                </p>
              )}
            </div>

            <ul className="space-y-3 pt-2">
              {activeSlide.bullets.map((bullet, i) => (
                <li key={i} className="flex items-start gap-2.5 text-xs sm:text-sm leading-relaxed" style={{ color: c.text_body }}>
                  <span
                    className="w-1.5 h-1.5 rounded-full mt-2 shrink-0"
                    style={{ backgroundColor: bulletDot }}
                  />
                  <span>{bullet}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Slide Navigation Controls */}
          <div className="pt-4 border-t flex items-center justify-between text-xs" style={{ borderColor: c.card_border }}>
            <button
              onClick={handlePrevSlide}
              disabled={activeSlideIndex === 0}
              className="flex items-center gap-1 disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer transition-opacity hover:opacity-80"
              style={{ color: activeTheme.isDarkTheme ? c.subtitle_dark : c.text_body }}
            >
              <ChevronLeft className="w-4 h-4" />
              <span>Previous</span>
            </button>

            <span className="font-mono" style={{ color: activeTheme.isDarkTheme ? c.subtitle_dark : c.muted }}>
              {activeSlideIndex + 1} of {deliverable.slides.length}
            </span>

            <button
              onClick={handleNextSlide}
              disabled={activeSlideIndex === deliverable.slides.length - 1}
              className="flex items-center gap-1 disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer transition-opacity hover:opacity-80"
              style={{ color: activeTheme.isDarkTheme ? c.subtitle_dark : c.text_body }}
            >
              <span>Next</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Right: Speaker Notes & Visual Guidance */}
        <div className="lg:col-span-3 space-y-4 text-xs">
          {/* Speaker Notes */}
          <div className="rounded-xl bg-slate-900/80 border border-slate-800 p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-white uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-indigo-400" />
                Speaker Notes
              </span>
            </div>
            <p className="text-slate-300 leading-relaxed text-xs italic bg-slate-950/60 p-3 rounded-lg border border-slate-800/60">
              "{activeSlide.speakerNotes}"
            </p>
          </div>

          {/* Visual Recommendation */}
          <div className="rounded-xl bg-slate-900/80 border border-slate-800 p-4 space-y-2">
            <span className="font-semibold text-white uppercase tracking-wider text-[11px] flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-purple-400" />
              Visual Recommendation
            </span>
            <p className="text-slate-300 leading-relaxed text-[11px] bg-purple-950/20 p-3 rounded-lg border border-purple-500/20">
              {activeSlide.visualRecommendation}
            </p>
          </div>
        </div>
      </div>

      {/* Fullscreen Presentation Modal (theme-styled) */}
      {isFullscreenPresent && (
        <div
          className="fixed inset-0 z-50 flex flex-col justify-between p-8 sm:p-12"
          style={{ backgroundColor: c.dark_bg }}
        >
          {/* Top bar */}
          <div
            className="flex items-center justify-between border-b pb-4"
            style={{ borderColor: activeTheme.isDarkTheme ? c.card_border : `${c.card_border}66` }}
          >
            <div className="text-sm font-semibold" style={{ color: activeTheme.isDarkTheme ? c.subtitle_dark : c.text_body }}>
              {deliverable.deckTitle} · Slide {activeSlide.slideNumber} of {deliverable.slides.length}
            </div>
            <button
              onClick={() => setIsFullscreenPresent(false)}
              className="p-2 rounded-lg text-white cursor-pointer"
              style={{ backgroundColor: activeTheme.isDarkTheme ? c.box_bg : c.header }}
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Slide Center */}
          <div className="max-w-4xl mx-auto w-full my-auto space-y-8">
            <div>
              <h1
                className="text-3xl sm:text-5xl font-extrabold tracking-tight leading-tight"
                style={{ color: activeTheme.isDarkTheme ? c.title_dark : c.header }}
              >
                {activeSlide.title}
              </h1>
              {activeSlide.subtitle && (
                <p className="text-lg mt-2 font-medium" style={{ color: c.accent }}>
                  {activeSlide.subtitle}
                </p>
              )}
            </div>

            <ul className="space-y-4 pt-4">
              {activeSlide.bullets.map((bullet, i) => (
                <li key={i} className="flex items-start gap-3 text-lg sm:text-xl leading-relaxed" style={{ color: c.text_body }}>
                  <span className="w-2.5 h-2.5 rounded-full mt-2 shrink-0" style={{ backgroundColor: c.accent }} />
                  <span>{bullet}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Bottom Bar */}
          <div
            className="flex items-center justify-between border-t pt-4"
            style={{ borderColor: activeTheme.isDarkTheme ? c.card_border : `${c.card_border}66` }}
          >
            <button
              onClick={handlePrevSlide}
              disabled={activeSlideIndex === 0}
              className="px-4 py-2 rounded-lg text-sm font-semibold disabled:opacity-30 cursor-pointer"
              style={{ backgroundColor: activeTheme.isDarkTheme ? c.box_bg : c.box_bg, color: activeTheme.isDarkTheme ? '#fff' : c.header }}
            >
              ← Previous Slide
            </button>

            <span className="font-mono text-sm" style={{ color: activeTheme.isDarkTheme ? c.subtitle_dark : c.muted }}>
              Press Esc or click Close to exit
            </span>

            <button
              onClick={handleNextSlide}
              disabled={activeSlideIndex === deliverable.slides.length - 1}
              className="px-4 py-2 rounded-lg text-sm font-semibold disabled:opacity-30 cursor-pointer"
              style={{ backgroundColor: c.accent, color: activeTheme.isDarkTheme ? '#0b0b0b' : '#ffffff' }}
            >
              Next Slide →
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
