import React, { useState } from 'react';
import { 
  Bot, 
  Cpu, 
  CheckCircle2, 
  Activity, 
  Sparkles, 
  Sliders, 
  ShieldCheck, 
  FileText, 
  Layers, 
  RefreshCw,
  Search,
  ExternalLink
} from 'lucide-react';
import { AgentInfo } from '../../types';
import { StatusBadge } from '../common/StatusBadge';

export const AgentsView: React.FC = () => {
  const [agents] = useState<AgentInfo[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<AgentInfo | null>(null);

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-purple-400 uppercase tracking-wider mb-1">
            <Bot className="w-4 h-4" />
            <span>Autonomous Intelligence Fabric</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            AI Multi-Agent System
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Specialized neural agents coordinating across extraction, semantic synthesis, format adaptation, and factual verification.
          </p>
        </div>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 text-xs font-medium self-start sm:self-auto">
          <span className="w-2 h-2 rounded-full bg-slate-500" />
          <span>No agents connected</span>
        </div>
      </div>

      {agents.length === 0 ? (
        <div className="p-12 rounded-2xl border border-dashed border-slate-800 text-center space-y-3 bg-slate-900/30">
          <Bot className="w-8 h-8 text-slate-600 mx-auto" />
          <h3 className="text-base font-bold text-white">No AI agents configured</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">Connect your agent backend to see live extraction, synthesis, and verification agents here. Generation uses the Gemini API directly.</p>
        </div>
      ) : (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {agents.map((agent) => (
          <div
            key={agent.id}
            className="rounded-2xl border border-slate-800 bg-[#0d121f] p-6 hover:border-purple-500/50 transition-all flex flex-col justify-between shadow-xl relative overflow-hidden"
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="w-10 h-10 rounded-xl bg-purple-500/15 border border-purple-500/30 flex items-center justify-center text-purple-400">
                  <Bot className="w-5 h-5" />
                </div>
                <StatusBadge status={agent.status} size="xs" />
              </div>

              <h3 className="text-base font-bold text-white">
                {agent.name}
              </h3>
              <span className="text-xs font-semibold text-purple-400 block mb-2">
                {agent.role}
              </span>

              <p className="text-xs text-slate-400 leading-relaxed">
                {agent.description}
              </p>

              {/* Agent Specs */}
              <div className="mt-4 pt-3 border-t border-slate-800/80 space-y-2 text-xs">
                <div className="flex items-center justify-between text-slate-400">
                  <span>Model Foundation:</span>
                  <span className="font-mono text-slate-200 font-semibold">{agent.model || 'Gemini 2.5 Flash'}</span>
                </div>
                <div className="flex items-center justify-between text-slate-400">
                  <span>Tasks Executed:</span>
                  <span className="font-mono text-purple-300 font-semibold">{agent.tasksCompleted.toLocaleString()}</span>
                </div>
                <div className="flex items-center justify-between text-slate-400">
                  <span>Accuracy Score:</span>
                  <span className="font-mono text-emerald-400 font-semibold">{agent.accuracy}</span>
                </div>
              </div>
            </div>

            <div className="mt-5 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
              <span className="text-[11px] text-slate-400 font-mono">
                Latency: ~420ms
              </span>
              <button
                onClick={() => setSelectedAgent(agent)}
                className="text-xs font-semibold text-purple-400 hover:text-purple-300 transition-colors"
              >
                Inspect Agent
              </button>
            </div>
          </div>
        ))}
      </div>
      )}

      {/* Agent Deep Dive Modal */}
      {selectedAgent && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0e1422] border border-slate-800 rounded-2xl max-w-xl w-full p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2.5">
                <Bot className="w-5 h-5 text-purple-400" />
                <h3 className="text-base font-bold text-white">{selectedAgent.name} Inspector</h3>
              </div>
              <button
                onClick={() => setSelectedAgent(null)}
                className="text-slate-400 hover:text-white text-xs"
              >
                ✕ Close
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <span className="text-slate-400 font-semibold block mb-1">Architecture & Role</span>
                <p className="text-slate-200 leading-relaxed bg-slate-900 p-3 rounded-lg border border-slate-800">
                  {selectedAgent.description}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                  <span className="text-slate-400 font-semibold block mb-0.5">Underlying Engine</span>
                  <span className="text-purple-300 font-mono font-bold">{selectedAgent.model || 'Gemini 2.5 Flash'}</span>
                </div>
                <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                  <span className="text-slate-400 font-semibold block mb-0.5">Factual Verification</span>
                  <span className="text-emerald-400 font-mono font-bold">{selectedAgent.accuracy} Grounded</span>
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedAgent(null)}
                className="px-4 py-2 rounded-lg bg-purple-600 text-white text-xs font-semibold"
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
