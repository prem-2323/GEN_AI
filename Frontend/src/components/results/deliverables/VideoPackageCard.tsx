import React, { useState } from 'react';
import { 
  Video as VideoIcon, 
  Play, 
  Square, 
  Download, 
  Volume2, 
  VolumeX, 
  CheckCircle2, 
  Clock, 
  FileText, 
  Layers, 
  Film, 
  Sparkles,
  Sliders,
  ChevronRight,
  Monitor,
  Smartphone,
  Maximize2,
  Loader2,
  ArrowDown
} from 'lucide-react';
import { VideoDeliverable, VideoScene } from '../../../types';
import { speakText, stopSpeaking } from '../../../services/aiService';
import { StatusBadge } from '../../common/StatusBadge';

interface VideoPackageCardProps {
  deliverable: VideoDeliverable;
  onUpdate: (updated: VideoDeliverable) => void;
  onShowToast: (title: string, message: string, type?: 'success' | 'info' | 'error') => void;
}

export const VideoPackageCard: React.FC<VideoPackageCardProps> = ({
  deliverable,
  onUpdate,
  onShowToast
}) => {
  const [activeTab, setActiveTab] = useState<'storyboard' | 'script' | 'narration' | 'subtitles'>('storyboard');
  const [aspectRatio, setAspectRatio] = useState<'16:9' | '9:16' | '1:1'>(deliverable.aspectRatio);
  const [style, setStyle] = useState<'Professional' | 'News' | 'Documentary' | 'Corporate'>(deliverable.style);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [selectedSceneIndex, setSelectedSceneIndex] = useState(0);
  const [isPreviewPlayerOpen, setIsPreviewPlayerOpen] = useState(false);
  const [currentPlaySceneIdx, setCurrentPlaySceneIdx] = useState(0);

  const activeScene = deliverable.scenes[selectedSceneIndex] || deliverable.scenes[0];

  const handleToggleVoice = () => {
    if (isPlayingAudio) {
      stopSpeaking();
      setIsPlayingAudio(false);
      onShowToast('Voice Stopped', 'Narration playback paused.', 'info');
    } else {
      const textToSpeak = deliverable.scenes.map(s => s.narration).join(' ');
      setIsPlayingAudio(true);
      speakText(textToSpeak, () => setIsPlayingAudio(false));
      onShowToast('AI Voice Playing', 'Playing synthesized voice narration for video package.', 'success');
    }
  };

  const handleDownloadSrt = () => {
    const blob = new Blob([deliverable.subtitlesSrt], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Subtitles_${Date.now()}.srt`;
    a.click();
    URL.revokeObjectURL(url);
    onShowToast('Downloaded Subtitles', 'SRT closed captions file saved.', 'success');
  };

  const handleExportMp4Package = () => {
    const pkg = {
      title: deliverable.title,
      aspectRatio,
      style,
      totalDurationSeconds: deliverable.totalDurationSeconds,
      productionPackage: {
        scenes: deliverable.scenes,
        script: deliverable.script,
        subtitlesSrt: deliverable.subtitlesSrt
      },
      exportTimestamp: new Date().toISOString()
    };

    const blob = new Blob([JSON.stringify(pkg, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Video_Production_Package_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    onShowToast('Exported Video Package', 'Complete video production assets and timeline exported.', 'success');
  };

  const handleStartSimulatedPreview = () => {
    setIsPreviewPlayerOpen(true);
    setCurrentPlaySceneIdx(0);
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-[#0d121f] p-6 space-y-6 shadow-xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-purple-500/15 border border-purple-500/30 flex items-center justify-center text-purple-400">
            <VideoIcon className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-white">Video Production Package</h3>
              <StatusBadge status="ready" size="xs" />
              <span className="text-[11px] font-mono text-slate-400">({deliverable.totalDurationSeconds}s Total)</span>
            </div>
            <p className="text-xs text-slate-400">Multi-scene storyboard, timed narration voiceover, and synchronized subtitles</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleToggleVoice}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all cursor-pointer ${
              isPlayingAudio
                ? 'bg-rose-500/20 border-rose-500 text-rose-300'
                : 'bg-purple-600/20 border-purple-500 text-purple-300 hover:bg-purple-600/30'
            }`}
          >
            {isPlayingAudio ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
            <span>{isPlayingAudio ? 'Stop Voice' : 'Generate Voice'}</span>
          </button>

          <button
            onClick={handleStartSimulatedPreview}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-md shadow-purple-600/20 transition-all cursor-pointer"
          >
            <Play className="w-3.5 h-3.5 fill-white" />
            <span>Preview Video</span>
          </button>
        </div>
      </div>

      {/* Video Production Pipeline Architectural Architecture & Status */}
      <div className="p-5 rounded-2xl bg-gradient-to-br from-slate-950 via-[#0d1322] to-purple-950/20 border border-purple-500/30 space-y-4 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
          <div>
            <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Film className="w-4 h-4 text-purple-400" />
              <span>VIDEO GENERATION ARCHITECTURE</span>
            </h4>
            <p className="text-xs text-slate-400 mt-0.5">
              Deterministic sequence from structured UCKR knowledge to final rendered package
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-300 border border-purple-500/30">
              6 PIPELINE STAGES
            </span>
          </div>
        </div>

        {/* Pipeline Flow: SCRIPT -> STORYBOARD -> VISUALS -> VOICE -> SUBTITLES -> FINAL VIDEO */}
        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-3">
          <div className="text-[11px] font-mono font-bold text-slate-400 uppercase tracking-wider">
            Execution Flow
          </div>

          <div className="flex items-center justify-between gap-1 overflow-x-auto pb-1 text-xs font-mono">
            {/* 1. SCRIPT */}
            <div className="px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-center shrink-0">
              <span className="text-white font-bold">SCRIPT</span>
            </div>
            <span className="text-purple-400 font-bold px-1">↓</span>

            {/* 2. STORYBOARD */}
            <div className="px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-center shrink-0">
              <span className="text-white font-bold">STORYBOARD</span>
            </div>
            <span className="text-purple-400 font-bold px-1">↓</span>

            {/* 3. VISUALS */}
            <div className="px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-center shrink-0">
              <span className="text-white font-bold">VISUALS</span>
            </div>
            <span className="text-purple-400 font-bold px-1">↓</span>

            {/* 4. VOICE */}
            <div className="px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-center shrink-0">
              <span className="text-white font-bold">VOICE</span>
            </div>
            <span className="text-purple-400 font-bold px-1">↓</span>

            {/* 5. SUBTITLES */}
            <div className="px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-center shrink-0">
              <span className="text-white font-bold">SUBTITLES</span>
            </div>
            <span className="text-purple-400 font-bold px-1">↓</span>

            {/* 6. FINAL VIDEO */}
            <div className="px-3 py-1.5 rounded-lg bg-purple-600/30 border border-purple-500 text-center shrink-0">
              <span className="text-purple-200 font-bold">FINAL VIDEO</span>
            </div>
          </div>
        </div>

        {/* Live Stage Status: Script, Storyboard, Visual prompts, Narration, SRT, Rendering */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2.5 text-xs font-mono">
          <div className="p-2.5 rounded-xl bg-slate-900 border border-emerald-500/30 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <div className="truncate">
              <div className="text-white font-semibold">Script</div>
              <div className="text-[10px] text-emerald-400">Complete</div>
            </div>
          </div>

          <div className="p-2.5 rounded-xl bg-slate-900 border border-emerald-500/30 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <div className="truncate">
              <div className="text-white font-semibold">Storyboard</div>
              <div className="text-[10px] text-emerald-400">Complete</div>
            </div>
          </div>

          <div className="p-2.5 rounded-xl bg-slate-900 border border-emerald-500/30 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <div className="truncate">
              <div className="text-white font-semibold">Visual prompts</div>
              <div className="text-[10px] text-emerald-400">Complete</div>
            </div>
          </div>

          <div className="p-2.5 rounded-xl bg-slate-900 border border-emerald-500/30 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <div className="truncate">
              <div className="text-white font-semibold">Narration</div>
              <div className="text-[10px] text-emerald-400">Complete</div>
            </div>
          </div>

          <div className="p-2.5 rounded-xl bg-slate-900 border border-emerald-500/30 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <div className="truncate">
              <div className="text-white font-semibold">SRT</div>
              <div className="text-[10px] text-emerald-400">Complete</div>
            </div>
          </div>

          <div className="p-2.5 rounded-xl bg-purple-950/40 border border-purple-500/50 flex items-center gap-2 shadow-sm">
            <div className="w-4 h-4 rounded-full border-2 border-purple-400 border-t-transparent animate-spin shrink-0" />
            <div className="truncate">
              <div className="text-purple-200 font-bold flex items-center gap-1">
                <span>◉ Rendering</span>
              </div>
              <div className="text-[10px] text-purple-300">Active engine</div>
            </div>
          </div>
        </div>
      </div>

      {/* Video Settings Bar */}
      <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-wrap items-center justify-between gap-4 text-xs">
        {/* Aspect Ratio */}
        <div className="flex items-center gap-2">
          <span className="text-slate-400 font-semibold">Aspect Ratio:</span>
          <div className="flex items-center gap-1 p-0.5 bg-slate-950 rounded-lg border border-slate-800">
            {(['16:9', '9:16', '1:1'] as const).map((ratio) => (
              <button
                key={ratio}
                onClick={() => {
                  setAspectRatio(ratio);
                  onUpdate({ ...deliverable, aspectRatio: ratio });
                }}
                className={`px-2.5 py-1 rounded-md font-mono text-[11px] font-semibold transition-colors cursor-pointer ${
                  aspectRatio === ratio ? 'bg-purple-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                {ratio}
              </button>
            ))}
          </div>
        </div>

        {/* Video Style */}
        <div className="flex items-center gap-2">
          <span className="text-slate-400 font-semibold">Style:</span>
          <div className="flex items-center gap-1 p-0.5 bg-slate-950 rounded-lg border border-slate-800">
            {(['Professional', 'News', 'Documentary', 'Corporate'] as const).map((s) => (
              <button
                key={s}
                onClick={() => {
                  setStyle(s);
                  onUpdate({ ...deliverable, style: s });
                }}
                className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors cursor-pointer ${
                  style === s ? 'bg-purple-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        {/* Total Scenes Badge */}
        <div className="text-slate-400 font-mono text-xs">
          Duration: <strong className="text-white font-normal">{deliverable.totalDurationSeconds}s</strong> · {deliverable.scenes.length} Scenes
        </div>
      </div>

      {/* Tabs for Storyboard, Script, Narration, Subtitles */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-3 text-xs">
        <button
          onClick={() => setActiveTab('storyboard')}
          className={`px-3 py-1.5 rounded-lg font-semibold transition-colors cursor-pointer ${
            activeTab === 'storyboard' ? 'bg-purple-600 text-white' : 'text-slate-400 hover:text-white bg-slate-900'
          }`}
        >
          Storyboard Timeline
        </button>
        <button
          onClick={() => setActiveTab('script')}
          className={`px-3 py-1.5 rounded-lg font-semibold transition-colors cursor-pointer ${
            activeTab === 'script' ? 'bg-purple-600 text-white' : 'text-slate-400 hover:text-white bg-slate-900'
          }`}
        >
          Full Script
        </button>
        <button
          onClick={() => setActiveTab('narration')}
          className={`px-3 py-1.5 rounded-lg font-semibold transition-colors cursor-pointer ${
            activeTab === 'narration' ? 'bg-purple-600 text-white' : 'text-slate-400 hover:text-white bg-slate-900'
          }`}
        >
          Narration Text
        </button>
        <button
          onClick={() => setActiveTab('subtitles')}
          className={`px-3 py-1.5 rounded-lg font-semibold transition-colors cursor-pointer ${
            activeTab === 'subtitles' ? 'bg-purple-600 text-white' : 'text-slate-400 hover:text-white bg-slate-900'
          }`}
        >
          Subtitles (SRT)
        </button>
      </div>

      {/* Tab 1: Storyboard Timeline */}
      {activeTab === 'storyboard' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {deliverable.scenes.map((scene, idx) => {
              const isSelected = idx === selectedSceneIndex;
              return (
                <div
                  key={scene.sceneNumber}
                  onClick={() => setSelectedSceneIndex(idx)}
                  className={`
                    p-4 rounded-xl border transition-all cursor-pointer flex flex-col justify-between
                    ${isSelected 
                      ? 'bg-purple-950/30 border-purple-500 shadow-md ring-1 ring-purple-500/40' 
                      : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                    }
                  `}
                >
                  <div>
                    <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
                      <span className="font-mono font-bold text-purple-300">
                        Scene {String(scene.sceneNumber).padStart(2, '0')}
                      </span>
                      <span className="flex items-center gap-1 font-mono text-[11px]">
                        <Clock className="w-3 h-3" /> {scene.durationSeconds}s
                      </span>
                    </div>

                    <h4 className="text-xs font-bold text-white mb-1">
                      {scene.title}
                    </h4>

                    <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">
                      {scene.sceneDescription}
                    </p>
                  </div>

                  <div className="mt-3 pt-2.5 border-t border-slate-800/60 text-[10px] text-slate-400 font-mono">
                    Text: "{scene.onScreenText.slice(0, 30)}..."
                  </div>
                </div>
              );
            })}
          </div>

          {/* Active Scene Detailed Card */}
          <div className="rounded-xl bg-slate-950/80 border border-slate-800 p-5 space-y-4 text-xs">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-md bg-purple-500/20 text-purple-300 font-mono font-bold text-xs flex items-center justify-center">
                  {activeScene.sceneNumber}
                </span>
                <span className="text-sm font-bold text-white">{activeScene.title}</span>
              </div>
              <span className="text-xs font-mono text-purple-400">{activeScene.durationSeconds} Seconds</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <span className="font-semibold text-slate-400 uppercase tracking-wider text-[10px] block">
                  Visual Recommendation
                </span>
                <p className="text-slate-200 bg-slate-900 p-3 rounded-lg border border-slate-800 leading-relaxed">
                  {activeScene.visualRecommendation}
                </p>
              </div>

              <div className="space-y-1.5">
                <span className="font-semibold text-slate-400 uppercase tracking-wider text-[10px] block">
                  On-Screen Lower Third / Typography
                </span>
                <p className="text-purple-300 font-mono bg-purple-950/30 p-3 rounded-lg border border-purple-500/30 leading-relaxed">
                  {activeScene.onScreenText}
                </p>
              </div>
            </div>

            <div className="space-y-1.5 pt-2">
              <span className="font-semibold text-slate-400 uppercase tracking-wider text-[10px] block">
                Scene Narration Voiceover
              </span>
              <p className="text-slate-300 bg-slate-900 p-3 rounded-lg border border-slate-800 italic leading-relaxed">
                "{activeScene.narration}"
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Full Script */}
      {activeTab === 'script' && (
        <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs text-slate-300 whitespace-pre-wrap leading-relaxed">
          {deliverable.script}
        </div>
      )}

      {/* Tab 3: Narration Text */}
      {activeTab === 'narration' && (
        <div className="space-y-3">
          <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 leading-relaxed space-y-4">
            {deliverable.scenes.map((s) => (
              <div key={s.sceneNumber} className="border-b border-slate-800/80 pb-3 last:border-b-0">
                <span className="font-mono text-purple-400 font-bold block mb-1">
                  [SCENE {s.sceneNumber} — {s.title}]
                </span>
                <p className="italic text-slate-300">"{s.narration}"</p>
              </div>
            ))}
          </div>

          <button
            onClick={handleToggleVoice}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold cursor-pointer"
          >
            <Volume2 className="w-3.5 h-3.5" />
            <span>{isPlayingAudio ? 'Stop Speech Narration' : 'Play Narration Voice'}</span>
          </button>
        </div>
      )}

      {/* Tab 4: Subtitles (SRT) */}
      {activeTab === 'subtitles' && (
        <div className="space-y-3">
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs text-slate-300 whitespace-pre-wrap leading-relaxed max-h-72 overflow-y-auto">
            {deliverable.subtitlesSrt}
          </div>
          <button
            onClick={handleDownloadSrt}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download Subtitles (.srt)</span>
          </button>
        </div>
      )}

      {/* Footer Actions */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-800">
        <div className="flex items-center gap-2">
          <button
            onClick={handleExportMp4Package}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-md shadow-purple-600/20 cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Production Package</span>
          </button>

          <button
            onClick={handleDownloadSrt}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium cursor-pointer"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>SRT File</span>
          </button>
        </div>

        <div className="flex items-center gap-1.5">
          <StatusBadge status="ready" size="xs" />
          <span className="text-xs text-slate-400 font-mono">Pipeline Target</span>
        </div>
      </div>

      {/* Simulated Video Player Modal */}
      {isPreviewPlayerOpen && (
        <div className="fixed inset-0 z-50 bg-black/90 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-[#0e1422] border border-slate-800 rounded-2xl max-w-3xl w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <span className="font-bold text-white text-sm">
                Video Package Simulator ({aspectRatio})
              </span>
              <button
                onClick={() => setIsPreviewPlayerOpen(false)}
                className="text-slate-400 hover:text-white text-xs p-1"
              >
                ✕ Close
              </button>
            </div>

            {/* Simulated 16:9 Screen */}
            <div className="relative aspect-video bg-black rounded-xl overflow-hidden border border-slate-800 flex flex-col justify-between p-6 text-center">
              <div className="text-[10px] uppercase font-mono text-purple-400 tracking-wider">
                {deliverable.scenes[currentPlaySceneIdx].title} · Scene {currentPlaySceneIdx + 1} of {deliverable.scenes.length}
              </div>

              <div className="my-auto space-y-2">
                <div className="text-base sm:text-xl font-bold text-white max-w-lg mx-auto">
                  {deliverable.scenes[currentPlaySceneIdx].onScreenText}
                </div>
                <p className="text-xs text-slate-400 max-w-md mx-auto italic">
                  "{deliverable.scenes[currentPlaySceneIdx].narration}"
                </p>
              </div>

              {/* Lower Third */}
              <div className="p-2 rounded bg-purple-900/40 border border-purple-500/30 text-xs text-purple-200">
                Visual Concept: {deliverable.scenes[currentPlaySceneIdx].visualRecommendation}
              </div>
            </div>

            {/* Scene Stepper */}
            <div className="flex items-center justify-between text-xs">
              <button
                onClick={() => setCurrentPlaySceneIdx(Math.max(0, currentPlaySceneIdx - 1))}
                disabled={currentPlaySceneIdx === 0}
                className="px-3 py-1.5 rounded bg-slate-800 disabled:opacity-30 text-white"
              >
                Previous Scene
              </button>
              <span className="font-mono text-slate-400">
                Scene {currentPlaySceneIdx + 1} / {deliverable.scenes.length} ({deliverable.scenes[currentPlaySceneIdx].durationSeconds}s)
              </span>
              <button
                onClick={() => setCurrentPlaySceneIdx(Math.min(deliverable.scenes.length - 1, currentPlaySceneIdx + 1))}
                disabled={currentPlaySceneIdx === deliverable.scenes.length - 1}
                className="px-3 py-1.5 rounded bg-purple-600 disabled:opacity-30 text-white"
              >
                Next Scene
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
