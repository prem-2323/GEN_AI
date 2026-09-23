import React, { useState } from 'react';
import { 
  Share2, 
  CheckCircle2, 
  XCircle, 
  Settings, 
  ExternalLink, 
  Sliders, 
  Plus, 
  Terminal, 
  Lock, 
  Radio,
  Check,
  ArrowDown,
  ArrowRight,
  ShieldCheck,
  HardDrive,
  MessageSquare,
  Linkedin,
  Twitter,
  Sparkles,
  Send,
  Upload,
  Globe
} from 'lucide-react';
import { McpIntegration } from '../../types';

interface McpViewProps {
  onShowToast: (title: string, message: string, type?: 'success' | 'info' | 'error') => void;
}

export const McpView: React.FC<McpViewProps> = ({ onShowToast }) => {
  const [integrations, setIntegrations] = useState<McpIntegration[]>([]);
  const [configuringItem, setConfiguringItem] = useState<McpIntegration | null>(null);

  const toggleIntegration = (id: string) => {
    const targetItem = integrations.find(item => item.id === id);
    if (!targetItem) return;

    const nextConnected = !targetItem.isConnected;
    setIntegrations(prev => prev.map(item => {
      if (item.id === id) {
        return { 
          ...item, 
          isConnected: nextConnected,
          status: nextConnected ? 'active' : 'needs_review'
        };
      }
      return item;
    }));

    onShowToast(
      `${targetItem.name} ${nextConnected ? 'Connected' : 'Disconnected'}`,
      `MCP endpoint ${targetItem.endpoint || `mcp://${targetItem.id}.corp.internal:8080`} ${nextConnected ? 'is now online' : 'has been unmounted'}.`,
      nextConnected ? 'success' : 'info'
    );
  };

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-purple-400 uppercase tracking-wider mb-1">
            <Share2 className="w-4 h-4" />
            <span>Model Context Protocol (MCP)</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            MCP Enterprise Integrations
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Securely route and publish generated deliverables across corporate communications, social media, and knowledge bases.
          </p>
        </div>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 text-xs font-mono">
          <Terminal className="w-3.5 h-3.5 text-purple-400" />
          <span>MCP Server: v2026.3-LTS</span>
        </div>
      </div>

      {/* MCP Architectural Workflow Flowchart */}
      <div className="rounded-2xl border border-purple-500/30 bg-gradient-to-br from-[#0e1424] via-[#0d121f] to-slate-900 p-6 shadow-xl space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-xs font-bold text-purple-300 uppercase tracking-wider flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-400" />
              <span>MCP AUTOMATION PIPELINE WORKFLOW</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Zero-friction orchestration: automatically distributes verified UCKR deliverables to subscribed enterprise endpoints.
            </p>
          </div>
          <div className="px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[10px] font-mono font-semibold">
            PROTOCOL STATUS: TLS 1.3 ACTIVE
          </div>
        </div>

        {/* Workflow Diagram Box: GENERATED OUTPUT -> MCP -> [LinkedIn, Slack, Drive] */}
        <div className="p-5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-4">
          {/* Stage 1: GENERATED OUTPUT */}
          <div className="flex flex-col items-center">
            <div className="px-5 py-2.5 rounded-xl bg-purple-600 text-white text-xs font-extrabold tracking-wide uppercase shadow-lg shadow-purple-600/30 border border-purple-400/40 flex items-center gap-2">
              <Sparkles className="w-4 h-4" />
              <span>GENERATED OUTPUT</span>
            </div>
            
            <div className="my-1.5 flex flex-col items-center text-purple-400">
              <span className="text-xs font-mono font-bold">↓</span>
            </div>

            {/* Stage 2: MCP Hub */}
            <div className="px-6 py-2.5 rounded-xl bg-indigo-950/90 text-indigo-200 border-2 border-indigo-500/60 text-xs font-bold tracking-wider font-mono shadow-md flex items-center gap-2">
              <Share2 className="w-4 h-4 text-indigo-400" />
              <span>MCP (Model Context Protocol Hub)</span>
            </div>

            <div className="my-1.5 flex flex-col items-center text-indigo-400">
              <span className="text-xs font-mono font-bold">↓</span>
            </div>
          </div>

          {/* Fork Tree Diagram */}
          <div className="max-w-2xl mx-auto">
            <div className="hidden sm:block text-slate-500 font-mono text-center text-xs leading-none select-none">
              ┌─────────────────────────┼─────────────────────────┐<br />
              ↓                         ↓                         ↓
            </div>

            {/* 3 Channels */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
              <div className="p-3 rounded-xl bg-slate-900 border border-blue-500/30 text-center space-y-1">
                <div className="flex items-center justify-center gap-1.5 text-xs font-bold text-white">
                  <Linkedin className="w-3.5 h-3.5 text-blue-400" />
                  <span>LinkedIn</span>
                </div>
                <div className="text-[10px] text-slate-400">Social Broadcasting</div>
                <span className="inline-flex items-center gap-1 text-[10px] text-emerald-400 font-mono">
                  <CheckCircle2 className="w-3 h-3" /> Auto-publish hook
                </span>
              </div>

              <div className="p-3 rounded-xl bg-slate-900 border border-purple-500/30 text-center space-y-1">
                <div className="flex items-center justify-center gap-1.5 text-xs font-bold text-white">
                  <MessageSquare className="w-3.5 h-3.5 text-purple-400" />
                  <span>Slack</span>
                </div>
                <div className="text-[10px] text-slate-400">Team Alerts & Policy</div>
                <span className="inline-flex items-center gap-1 text-[10px] text-emerald-400 font-mono">
                  <CheckCircle2 className="w-3 h-3" /> Real-time channel post
                </span>
              </div>

              <div className="p-3 rounded-xl bg-slate-900 border border-amber-500/30 text-center space-y-1">
                <div className="flex items-center justify-center gap-1.5 text-xs font-bold text-white">
                  <HardDrive className="w-3.5 h-3.5 text-amber-400" />
                  <span>Drive</span>
                </div>
                <div className="text-[10px] text-slate-400">Enterprise Archival</div>
                <span className="inline-flex items-center gap-1 text-[10px] text-emerald-400 font-mono">
                  <CheckCircle2 className="w-3 h-3" /> Artifact storage & sync
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Integration Grid */}
      {integrations.length === 0 ? (
        <div className="p-12 rounded-2xl border border-dashed border-slate-800 text-center space-y-3 bg-slate-900/30">
          <Share2 className="w-8 h-8 text-slate-600 mx-auto" />
          <h3 className="text-base font-bold text-white">No integrations connected</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">Connect publishing endpoints to route deliverables. Publishing from results still works as a simulated queue.</p>
        </div>
      ) : (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {integrations.map((item) => {
          const isConnected = item.isConnected;

          return (
            <div
              key={item.id}
              className={`rounded-2xl border ${isConnected ? 'border-purple-500/30 bg-[#0d121f]' : 'border-slate-800 bg-[#0d121f]/60'} p-6 hover:border-purple-500/50 transition-all flex flex-col justify-between shadow-xl space-y-5`}
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center font-bold text-sm text-purple-300">
                      {item.icon}
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-white">{item.name}</h3>
                      <span className="text-[10px] font-mono text-slate-400 truncate block max-w-[140px]">
                        {item.endpoint || `mcp://${item.id}.corp.internal`}
                      </span>
                    </div>
                  </div>

                  {/* Toggle Switch */}
                  <button
                    onClick={() => toggleIntegration(item.id)}
                    className={`
                      w-12 h-6 rounded-full transition-colors relative p-0.5 cursor-pointer
                      ${isConnected ? 'bg-purple-600' : 'bg-slate-800'}
                    `}
                    title={`Toggle ${item.name}`}
                  >
                    <div className={`
                      w-5 h-5 rounded-full bg-white transition-transform
                      ${isConnected ? 'translate-x-6' : 'translate-x-0'}
                    `} />
                  </button>
                </div>

                {/* Status indicator: Connected ✓ */}
                <div className="mb-3">
                  {isConnected ? (
                    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Connected ✓</span>
                    </div>
                  ) : (
                    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-800 text-slate-400 text-xs font-medium">
                      <span>Disconnected</span>
                    </div>
                  )}
                </div>

                <p className="text-xs text-slate-400 leading-relaxed mb-4">
                  {item.description}
                </p>

                {/* Explicit Permissions Checklist */}
                <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2 text-xs">
                  <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block font-mono">
                    Permissions:
                  </span>
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2 text-slate-200">
                      <Check className={`w-3.5 h-3.5 ${isConnected ? 'text-emerald-400' : 'text-slate-600'}`} />
                      <span className={isConnected ? 'text-white' : 'text-slate-400'}>Create post</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-200">
                      <Check className={`w-3.5 h-3.5 ${isConnected ? 'text-emerald-400' : 'text-slate-600'}`} />
                      <span className={isConnected ? 'text-white' : 'text-slate-400'}>Upload media</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-200">
                      <Check className={`w-3.5 h-3.5 ${isConnected ? 'text-emerald-400' : 'text-slate-600'}`} />
                      <span className={isConnected ? 'text-white' : 'text-slate-400'}>Publish</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Configure Button */}
              <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
                <span className="text-[11px] font-mono text-slate-500">
                  {isConnected ? 'Sync: Real-time' : 'Inactive'}
                </span>

                <button
                  onClick={() => setConfiguringItem(item)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-medium transition-colors cursor-pointer border border-slate-700"
                >
                  <Settings className="w-3.5 h-3.5 text-purple-400" />
                  <span>[Configure]</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>
      )}

      {/* Configure Modal */}
      {configuringItem && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0e1422] border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Settings className="w-4 h-4 text-purple-400" />
                <h3 className="text-sm font-bold text-white">Configure {configuringItem.name} MCP</h3>
              </div>
              <button
                onClick={() => setConfiguringItem(null)}
                className="text-slate-400 hover:text-white text-xs"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="text-slate-300 block mb-1 font-semibold">Protocol Endpoint</label>
                <input
                  type="text"
                  readOnly
                  value={configuringItem.endpoint}
                  className="w-full rounded-lg bg-slate-900 border border-slate-800 p-2 text-xs font-mono text-purple-300"
                />
              </div>

              <div>
                <label className="text-slate-300 block mb-1 font-semibold">Connection Status</label>
                <div className="p-2 rounded bg-slate-900 border border-slate-800 text-slate-300 flex items-center gap-2">
                  <Radio className="w-3 h-3 text-emerald-400 animate-pulse" />
                  <span>Verified TLS 1.3 handshake with local daemon</span>
                </div>
              </div>

              <div>
                <label className="text-slate-300 block mb-1 font-semibold">Authentication Token</label>
                <input
                  type="password"
                  value="mcp_sec_984f89d71a6245ee8"
                  readOnly
                  className="w-full rounded-lg bg-slate-900 border border-slate-800 p-2 text-xs font-mono text-slate-400"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => {
                  setConfiguringItem(null);
                  onShowToast('Settings Saved', `${configuringItem.name} MCP parameters synced.`, 'success');
                }}
                className="px-4 py-2 rounded-lg bg-purple-600 text-white text-xs font-semibold"
              >
                Save Configuration
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
