import React, { useState } from 'react';
import { 
  Settings, 
  ShieldCheck, 
  Cpu, 
  Sparkles, 
  Sliders, 
  Check, 
  Save, 
  Key, 
  Layers,
  FileCheck2
} from 'lucide-react';
import { 
  TransformationConfig, 
  AudienceType, 
  ToneType, 
  LanguageType,
  DetailLevel,
  ObjectiveType,
  ContentStyle
} from '../../types';

interface SettingsViewProps {
  config: TransformationConfig;
  onUpdateConfig: (config: TransformationConfig) => void;
  onShowToast: (title: string, message: string, type?: 'success' | 'info' | 'error') => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({
  config,
  onUpdateConfig,
  onShowToast
}) => {
  const [selectedModel, setSelectedModel] = useState<'gemini-2.5-flash' | 'gemini-2.5-pro'>('gemini-2.5-flash');
  const [temperature, setTemperature] = useState(0.3);
  const [autoVerify, setAutoVerify] = useState(true);
  const [cacheExtractions, setCacheExtractions] = useState(true);

  const handleSave = () => {
    onShowToast('Preferences Saved', 'Workspace configuration updated successfully.', 'success');
  };

  return (
    <div className="space-y-8 pb-16 max-w-4xl">
      {/* Header */}
      <div className="border-b border-slate-800 pb-6">
        <div className="flex items-center gap-2 text-xs font-semibold text-purple-400 uppercase tracking-wider mb-1">
          <Settings className="w-4 h-4" />
          <span>System Settings</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
          Workspace Preferences
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Tune AI model inference, default audience presets, and enterprise security guardrails.
        </p>
      </div>

      {/* Section 1: AI Model Engine */}
      <div className="rounded-2xl border border-slate-800 bg-[#0d121f] p-6 space-y-5 shadow-xl">
        <div className="flex items-center gap-2.5 border-b border-slate-800 pb-4">
          <Cpu className="w-5 h-5 text-purple-400" />
          <div>
            <h2 className="text-base font-bold text-white">AI Engine Configuration</h2>
            <p className="text-xs text-slate-400">Select model latency profile and inference parameters</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div
            onClick={() => setSelectedModel('gemini-2.5-flash')}
            className={`p-4 rounded-xl border cursor-pointer transition-all ${
              selectedModel === 'gemini-2.5-flash'
                ? 'bg-purple-950/40 border-purple-500 ring-1 ring-purple-500/40'
                : 'bg-slate-900 border-slate-800 hover:border-slate-700'
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="font-bold text-white text-sm">Gemini 2.5 Flash</span>
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-purple-500/20 text-purple-300">
                Fast (~1.2s)
              </span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed mt-1">
              Optimized for high-speed multi-output transformation and responsive social generation.
            </p>
          </div>

          <div
            onClick={() => setSelectedModel('gemini-2.5-pro')}
            className={`p-4 rounded-xl border cursor-pointer transition-all ${
              selectedModel === 'gemini-2.5-pro'
                ? 'bg-purple-950/40 border-purple-500 ring-1 ring-purple-500/40'
                : 'bg-slate-900 border-slate-800 hover:border-slate-700'
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="font-bold text-white text-sm">Gemini 2.5 Pro</span>
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300">
                Deep Analysis
              </span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed mt-1">
              Recommended for complex regulatory compliance, deep technical whitepapers, and multi-page research.
            </p>
          </div>
        </div>

        {/* Temperature slider */}
        <div className="pt-2 space-y-2 text-xs">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-slate-300">Inference Temperature (Creativity vs Determinism)</span>
            <span className="font-mono text-purple-400 font-bold">{temperature}</span>
          </div>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={temperature}
            onChange={(e) => setTemperature(parseFloat(e.target.value))}
            className="w-full accent-purple-500"
          />
          <div className="flex justify-between text-[11px] text-slate-400 font-mono">
            <span>0.0 (Strict & Factual)</span>
            <span>1.0 (Creative Adaptation)</span>
          </div>
        </div>
      </div>

      {/* Section 2: Default Transformation Parameters */}
      <div className="rounded-2xl border border-slate-800 bg-[#0d121f] p-6 space-y-5 shadow-xl">
        <div className="flex items-center gap-2.5 border-b border-slate-800 pb-4">
          <Sliders className="w-5 h-5 text-purple-400" />
          <div>
            <h2 className="text-base font-bold text-white">Default Workspace Presets</h2>
            <p className="text-xs text-slate-400">Pre-fill options for all incoming transformations</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div>
            <label className="font-semibold text-slate-300 block mb-1.5">Default Audience</label>
            <select
              value={config.targetAudience}
              onChange={(e) => onUpdateConfig({ ...config, targetAudience: e.target.value as AudienceType })}
              className="w-full rounded-xl bg-slate-900 border border-slate-800 p-2.5 text-white focus:outline-none focus:border-purple-500 cursor-pointer"
            >
              <option value="General Public">General Public</option>
              <option value="Executives">Executives</option>
              <option value="Government Officials">Government Officials</option>
              <option value="Technical Team">Technical Team</option>
              <option value="Security Team">Security Team</option>
              <option value="Customers">Customers</option>
              <option value="Students">Students</option>
              <option value="Custom">Custom</option>
            </select>
          </div>

          <div>
            <label className="font-semibold text-slate-300 block mb-1.5">Tone of Voice</label>
            <select
              value={config.tone}
              onChange={(e) => onUpdateConfig({ ...config, tone: e.target.value as ToneType })}
              className="w-full rounded-xl bg-slate-900 border border-slate-800 p-2.5 text-white focus:outline-none focus:border-purple-500 cursor-pointer"
            >
              <option value="Professional">Professional</option>
              <option value="Formal">Formal</option>
              <option value="Informative">Informative</option>
              <option value="Persuasive">Persuasive</option>
              <option value="Urgent">Urgent</option>
              <option value="Friendly">Friendly</option>
              <option value="Technical">Technical</option>
            </select>
          </div>

          <div>
            <label className="font-semibold text-slate-300 block mb-1.5">Default Language</label>
            <select
              value={config.language}
              onChange={(e) => onUpdateConfig({ ...config, language: e.target.value as LanguageType })}
              className="w-full rounded-xl bg-slate-900 border border-slate-800 p-2.5 text-white focus:outline-none focus:border-purple-500 cursor-pointer"
            >
              <option value="English">English</option>
              <option value="Tamil">Tamil</option>
              <option value="Hindi">Hindi</option>
              <option value="Malayalam">Malayalam</option>
              <option value="Telugu">Telugu</option>
              <option value="Kannada">Kannada</option>
              <option value="Spanish">Spanish</option>
              <option value="French">French</option>
              <option value="German">German</option>
              <option value="Japanese">Japanese</option>
              <option value="Custom">Custom</option>
            </select>
          </div>

          <div>
            <label className="font-semibold text-slate-300 block mb-1.5">Default Objective</label>
            <select
              value={config.objective}
              onChange={(e) => onUpdateConfig({ ...config, objective: e.target.value as ObjectiveType })}
              className="w-full rounded-xl bg-slate-900 border border-slate-800 p-2.5 text-white focus:outline-none focus:border-purple-500 cursor-pointer"
            >
              <option value="Inform">Inform</option>
              <option value="Educate">Educate</option>
              <option value="Alert">Alert</option>
              <option value="Persuade">Persuade</option>
              <option value="Summarize">Summarize</option>
              <option value="Engage">Engage</option>
              <option value="Brief">Brief</option>
            </select>
          </div>

          <div>
            <label className="font-semibold text-slate-300 block mb-1.5">Content Style</label>
            <select
              value={config.contentStyle}
              onChange={(e) => onUpdateConfig({ ...config, contentStyle: e.target.value as ContentStyle })}
              className="w-full rounded-xl bg-slate-900 border border-slate-800 p-2.5 text-white focus:outline-none focus:border-purple-500 cursor-pointer"
            >
              <option value="Professional">Professional</option>
              <option value="Executive">Executive</option>
              <option value="Technical">Technical</option>
              <option value="Social Media">Social Media</option>
              <option value="News Style">News Style</option>
              <option value="Storytelling">Storytelling</option>
              <option value="Academic">Academic</option>
              <option value="Custom">Custom</option>
            </select>
          </div>

          <div>
            <label className="font-semibold text-slate-300 block mb-1.5">Level of Detail</label>
            <select
              value={config.levelOfDetail}
              onChange={(e) => onUpdateConfig({ ...config, levelOfDetail: e.target.value as DetailLevel })}
              className="w-full rounded-xl bg-slate-900 border border-slate-800 p-2.5 text-white focus:outline-none focus:border-purple-500 cursor-pointer"
            >
              <option value="Concise">Concise</option>
              <option value="Balanced">Balanced</option>
              <option value="Detailed">Detailed</option>
            </select>
          </div>
        </div>
      </div>

      {/* Section 3: Enterprise Security & Verification */}
      <div className="rounded-2xl border border-slate-800 bg-[#0d121f] p-6 space-y-4 shadow-xl">
        <div className="flex items-center gap-2.5 border-b border-slate-800 pb-4">
          <ShieldCheck className="w-5 h-5 text-emerald-400" />
          <div>
            <h2 className="text-base font-bold text-white">Enterprise Guardrails & Integrity</h2>
            <p className="text-xs text-slate-400">Zero-retention policies and automated fact validation</p>
          </div>
        </div>

        <div className="space-y-3 text-xs">
          <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900 border border-slate-800">
            <div>
              <div className="font-semibold text-white">Fact & Consistency Verification Agent</div>
              <div className="text-slate-400 text-[11px]">Run automated audit on all deliverables against source input</div>
            </div>
            <input
              type="checkbox"
              checked={autoVerify}
              onChange={(e) => setAutoVerify(e.target.checked)}
              className="w-4 h-4 accent-purple-600 cursor-pointer"
            />
          </div>

          <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900 border border-slate-800">
            <div>
              <div className="font-semibold text-white">Zero Data Retention Mode</div>
              <div className="text-slate-400 text-[11px]">Temporary memory buffers purged immediately following deliverable export</div>
            </div>
            <span className="text-[11px] font-mono text-slate-400 bg-slate-800/60 px-2 py-0.5 rounded border border-slate-700">
              Backend policy
            </span>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-lg shadow-purple-600/25 transition-all cursor-pointer"
        >
          <Save className="w-4 h-4" />
          <span>Save Changes</span>
        </button>
      </div>
    </div>
  );
};
