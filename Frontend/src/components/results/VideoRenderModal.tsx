import React, { useState } from 'react';
import {
  Film,
  Loader2,
  Download,
  X,
  Clapperboard,
  Mic,
  Image as ImageIcon,
  CheckCircle2,
  AlertTriangle,
  Clock,
} from 'lucide-react';
import {
  VideoResponse,
  videoStudioApi,
  mediaFileUrl,
  mediaFileDownloadUrl,
} from '../../api/mediaApi';

interface VideoRenderModalProps {
  isOpen: boolean;
  onClose: () => void;
  /** Source text used to (re)plan scenes and render the video. */
  sourceText: string;
  /** Suggested video title shown in the header. */
  title?: string;
  /** Pre-selected narration tone. */
  tone?: string;
  onShowToast: (title: string, message: string, type?: 'success' | 'info' | 'error') => void;
}

const TONES = ['Professional', 'Cinematic', 'Inspiring', 'Educational', 'Authoritative', 'Casual'];
const PACINGS: Array<{ id: 'fast' | 'balanced' | 'cinematic'; label: string }> = [
  { id: 'fast', label: 'Fast (3-4s/scene)' },
  { id: 'balanced', label: 'Balanced (5s/scene)' },
  { id: 'cinematic', label: 'Cinematic (6-8s/scene)' },
];
const VOICES: Array<{ id: string; label: string }> = [
  { id: 'en-US-AriaNeural', label: 'Aria (EN-US Female)' },
  { id: 'en-US-GuyNeural', label: 'Guy (EN-US Male)' },
  { id: 'en-GB-SoniaNeural', label: 'Sonia (EN-UK Female)' },
  { id: 'en-IN-NeerjaNeural', label: 'Neerja (EN-IN Female)' },
  { id: 'ta-IN-PallaviNeural', label: 'Pallavi (Tamil Female)' },
  { id: 'hi-IN-SwaraNeural', label: 'Swara (Hindi Female)' },
];

/**
 * Full backend render pipeline:
 * Intelligent planning -> Forge scene images -> Edge TTS narration ->
 * FFmpeg scene MP4s -> concat -> SRT -> subtitle burn -> final MP4.
 */
export const VideoRenderModal: React.FC<VideoRenderModalProps> = ({
  isOpen,
  onClose,
  sourceText,
  title = 'AI Video',
  tone: initialTone = 'Professional',
  onShowToast,
}) => {
  const [targetDuration, setTargetDuration] = useState(30);
  const [pacing, setPacing] = useState<'fast' | 'balanced' | 'cinematic'>('balanced');
  const [tone, setTone] = useState(initialTone);
  const [voice, setVoice] = useState('en-US-AriaNeural');
  const [resolution, setResolution] = useState<'512' | '768'>('512');
  const [isRendering, setIsRendering] = useState(false);
  const [result, setResult] = useState<VideoResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleRender = async () => {
    if (!sourceText.trim()) {
      onShowToast('No Source', 'There is no source content to render a video from.', 'error');
      return;
    }
    setIsRendering(true);
    setError(null);
    setResult(null);
    try {
      const response = await videoStudioApi.generateVideo({
        text: sourceText.slice(0, 8000),
        target_duration: targetDuration,
        pacing,
        tone,
        voice,
        language: 'English',
        width: resolution === '768' ? 768 : 512,
        height: resolution === '768' ? 768 : 512,
        steps: 20,
      });
      setResult(response);
      onShowToast(
        'Video Rendered',
        `${response.scenes} scenes · ${response.duration}s final MP4 rendered by the backend pipeline.`,
        'success',
      );
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'The backend video pipeline failed.';
      setError(message);
      onShowToast('Render Failed', message, 'error');
    } finally {
      setIsRendering(false);
    }
  };

  const stage = isRendering
    ? 'Rendering: planning scenes, generating Forge visuals, synthesizing narration, and encoding with FFmpeg…'
    : null;

  return (
    <div className="fixed inset-0 z-50 bg-black/90 backdrop-blur-md flex items-center justify-center p-4">
      <div className="bg-[#0e1422] border border-slate-800 rounded-2xl max-w-3xl w-full p-6 space-y-5 shadow-2xl max-h-[92vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-purple-500/15 border border-purple-500/30 flex items-center justify-center text-purple-400">
              <Clapperboard className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-white text-sm">AI Video Renderer</h3>
              <p className="text-[11px] text-slate-400">
                Forge visuals · Edge TTS narration · FFmpeg encode with burned subtitles
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={isRendering}
            className="text-slate-400 hover:text-white text-xs p-1 disabled:opacity-40 cursor-pointer disabled:cursor-not-allowed"
          >
            ✕ Close
          </button>
        </div>

        {/* Render controls */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
          <div className="space-y-1.5">
            <label className="flex items-center gap-1.5 font-semibold text-slate-400 uppercase tracking-wider text-[10px]">
              <Clock className="w-3 h-3" /> Target Duration
            </label>
            <div className="flex items-center gap-2">
              <input
                type="range"
                min={10}
                max={180}
                step={5}
                value={targetDuration}
                onChange={(e) => setTargetDuration(Number(e.target.value))}
                className="flex-1 accent-purple-500 cursor-pointer"
                disabled={isRendering}
              />
              <span className="font-mono text-purple-300 w-12 text-right">{targetDuration}s</span>
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="font-semibold text-slate-400 uppercase tracking-wider text-[10px] block">
              Pacing
            </label>
            <select
              value={pacing}
              onChange={(e) => setPacing(e.target.value as 'fast' | 'balanced' | 'cinematic')}
              className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-white cursor-pointer"
              disabled={isRendering}
            >
              {PACINGS.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.label}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="font-semibold text-slate-400 uppercase tracking-wider text-[10px] block">
              Tone
            </label>
            <select
              value={tone}
              onChange={(e) => setTone(e.target.value)}
              className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-white cursor-pointer"
              disabled={isRendering}
            >
              {TONES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5 col-span-2 sm:col-span-2">
            <label className="flex items-center gap-1.5 font-semibold text-slate-400 uppercase tracking-wider text-[10px]">
              <Mic className="w-3 h-3" /> Narration Voice
            </label>
            <select
              value={voice}
              onChange={(e) => setVoice(e.target.value)}
              className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-white cursor-pointer"
              disabled={isRendering}
            >
              {VOICES.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.label}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="flex items-center gap-1.5 font-semibold text-slate-400 uppercase tracking-wider text-[10px]">
              <ImageIcon className="w-3 h-3" /> Resolution
            </label>
            <div className="flex items-center gap-1 p-0.5 bg-slate-950 rounded-lg border border-slate-800">
              {(['512', '768'] as const).map((r) => (
                <button
                  key={r}
                  onClick={() => setResolution(r)}
                  disabled={isRendering}
                  className={`flex-1 px-2 py-1 rounded-md font-mono text-[11px] font-semibold transition-colors cursor-pointer disabled:cursor-not-allowed ${
                    resolution === r ? 'bg-purple-600 text-white' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {r}px
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Render button */}
        <button
          onClick={handleRender}
          disabled={isRendering || !sourceText.trim()}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-gradient-to-r from-purple-600 via-indigo-600 to-blue-600 hover:from-purple-500 hover:via-indigo-500 hover:to-blue-500 text-white text-sm font-bold shadow-lg shadow-purple-600/25 transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isRendering ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Rendering Video…</span>
            </>
          ) : (
            <>
              <Film className="w-4 h-4" />
              <span>Render AI Video on Backend</span>
            </>
          )}
        </button>

        {stage && (
          <div className="p-3 rounded-xl bg-purple-950/30 border border-purple-500/30 text-[11px] text-purple-200 leading-relaxed">
            <div className="flex items-center gap-2">
              <Loader2 className="w-3.5 h-3.5 animate-spin shrink-0" />
              <span>{stage}</span>
            </div>
            <p className="mt-1.5 text-purple-300/70">
              A 30s video typically takes 2-6 minutes depending on GPU load. Keep this tab open.
            </p>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-500/40 text-[11px] text-rose-200 flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">Backend render failed</p>
              <p className="mt-0.5 text-rose-300/80 break-words">{error}</p>
              <p className="mt-1.5 text-rose-300/60">
                Check that Forge (port 7860), Ollama (11434), FFmpeg, and the FastAPI backend (8000) are running.
              </p>
            </div>
          </div>
        )}

        {/* Result player */}
        {result && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span className="font-semibold text-white">{result.scenes} scenes</span>
                <span className="text-slate-400 font-mono">· {result.duration}s total</span>
              </div>
              <a
                href={mediaFileDownloadUrl(result.video_file.split(/[/\\]/).pop() || '')}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold cursor-pointer"
              >
                <Download className="w-3.5 h-3.5" /> Download MP4
              </a>
            </div>

            <video
              controls
              className="w-full rounded-xl border border-slate-800 bg-black"
              src={mediaFileUrl(result.video_file.split(/[/\\]/).pop() || '')}
            />

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-[11px] text-slate-300 font-mono space-y-1">
              <div>
                <span className="text-slate-500">video_file:</span> {result.video_file}
              </div>
              <div>
                <span className="text-slate-500">subtitle_file:</span> {result.subtitle_file}
              </div>
            </div>

            {(result.scene_details ?? []).length > 0 && (
              <div className="max-h-48 overflow-y-auto rounded-xl border border-slate-800 divide-y divide-slate-800/80">
                {(result.scene_details ?? []).map((s) => (
                  <div key={s.scene_number} className="p-3 bg-slate-900/60 text-[11px] space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-bold text-purple-300">
                        Scene {String(s.scene_number).padStart(2, '0')}
                      </span>
                      <span className="text-slate-400 font-mono">
                        {s.start_time?.toFixed(1)}s → {s.end_time?.toFixed(1)}s ·{' '}
                        {s.visual_tier || 'MEDIUM'}
                      </span>
                    </div>
                    <p className="text-slate-300 italic">"{s.narration}"</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
