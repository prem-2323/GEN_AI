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
  Sparkles
} from 'lucide-react';
import { PresentationDeliverable, PresentationSlide } from '../../../types';
import { StatusBadge } from '../../common/StatusBadge';

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

  const activeSlide = deliverable.slides[activeSlideIndex] || deliverable.slides[0];

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

  const handleDownloadDeck = () => {
    const deckOutline = {
      title: deliverable.deckTitle,
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
    onShowToast('Exported Slide Deck', 'Presentation outline exported as JSON/PPTX schema.', 'success');
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
            onClick={handleDownloadDeck}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download Deck</span>
          </button>
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

        {/* Center: Large Slide Preview Canvas */}
        <div className="lg:col-span-6 rounded-2xl bg-gradient-to-br from-[#12192a] to-[#090e18] border border-slate-800 p-8 min-h-[460px] flex flex-col justify-between relative shadow-2xl">
          {/* Subtle slide watermark/badge */}
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 rounded-md bg-indigo-500/20 text-indigo-300 font-mono font-bold text-xs flex items-center justify-center border border-indigo-500/30">
                {activeSlide.slideNumber}
              </span>
              <span className="text-[11px] font-mono text-slate-400">
                {deliverable.deckTitle}
              </span>
            </div>
            <span className="text-[10px] uppercase font-bold text-purple-400 tracking-wider">
              GEN TRANSFORM AI
            </span>
          </div>

          {/* Slide Content */}
          <div className="py-6 space-y-4">
            <div>
              <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight leading-snug">
                {activeSlide.title}
              </h2>
              {activeSlide.subtitle && (
                <p className="text-sm text-indigo-300/80 mt-1 font-medium">
                  {activeSlide.subtitle}
                </p>
              )}
            </div>

            <ul className="space-y-3 pt-2">
              {activeSlide.bullets.map((bullet, i) => (
                <li key={i} className="flex items-start gap-2.5 text-xs sm:text-sm text-slate-200 leading-relaxed">
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-2 shrink-0" />
                  <span>{bullet}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Slide Navigation Controls */}
          <div className="pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs">
            <button
              onClick={handlePrevSlide}
              disabled={activeSlideIndex === 0}
              className="flex items-center gap-1 text-slate-300 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer"
            >
              <ChevronLeft className="w-4 h-4" />
              <span>Previous</span>
            </button>

            <span className="font-mono text-slate-400">
              {activeSlideIndex + 1} of {deliverable.slides.length}
            </span>

            <button
              onClick={handleNextSlide}
              disabled={activeSlideIndex === deliverable.slides.length - 1}
              className="flex items-center gap-1 text-slate-300 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer"
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

      {/* Fullscreen Presentation Modal */}
      {isFullscreenPresent && (
        <div className="fixed inset-0 z-50 bg-[#090d16] flex flex-col justify-between p-8 sm:p-12">
          {/* Top bar */}
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div className="text-sm font-semibold text-slate-300">
              {deliverable.deckTitle} · Slide {activeSlide.slideNumber} of {deliverable.slides.length}
            </div>
            <button
              onClick={() => setIsFullscreenPresent(false)}
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Slide Center */}
          <div className="max-w-4xl mx-auto w-full my-auto space-y-8">
            <div>
              <h1 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight leading-tight">
                {activeSlide.title}
              </h1>
              {activeSlide.subtitle && (
                <p className="text-lg text-indigo-400 mt-2 font-medium">
                  {activeSlide.subtitle}
                </p>
              )}
            </div>

            <ul className="space-y-4 pt-4">
              {activeSlide.bullets.map((bullet, i) => (
                <li key={i} className="flex items-start gap-3 text-lg sm:text-xl text-slate-200 leading-relaxed">
                  <span className="w-2.5 h-2.5 rounded-full bg-indigo-400 mt-2 shrink-0" />
                  <span>{bullet}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Bottom Bar */}
          <div className="flex items-center justify-between border-t border-slate-800 pt-4">
            <button
              onClick={handlePrevSlide}
              disabled={activeSlideIndex === 0}
              className="px-4 py-2 rounded-lg bg-slate-800 text-white text-sm font-semibold disabled:opacity-30 cursor-pointer"
            >
              ← Previous Slide
            </button>

            <span className="font-mono text-slate-400 text-sm">
              Press Esc or click Close to exit
            </span>

            <button
              onClick={handleNextSlide}
              disabled={activeSlideIndex === deliverable.slides.length - 1}
              className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold disabled:opacity-30 cursor-pointer"
            >
              Next Slide →
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
