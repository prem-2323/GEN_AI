import React, { useState } from 'react';
import { 
  Twitter, 
  Copy, 
  Check, 
  Download, 
  Send, 
  Edit3, 
  Sparkles, 
  CheckCircle2,
  MessageSquare
} from 'lucide-react';
import { TwitterDeliverable } from '../../../types';
import { StatusBadge } from '../../common/StatusBadge';

interface TwitterCardProps {
  deliverable: TwitterDeliverable;
  onUpdate: (updated: TwitterDeliverable) => void;
  onPublishToMcp?: () => void;
  onShowToast: (title: string, message: string, type?: 'success' | 'info' | 'error') => void;
}

export const TwitterCard: React.FC<TwitterCardProps> = ({
  deliverable,
  onUpdate,
  onPublishToMcp,
  onShowToast
}) => {
  const [tab, setTab] = useState<'thread' | 'single'>('thread');
  const [copied, setCopied] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [singleText, setSingleText] = useState(deliverable.singlePost);
  const [threadList, setThreadList] = useState(deliverable.thread);

  const handleCopy = () => {
    const textToCopy = tab === 'single' 
      ? singleText 
      : threadList.map(t => t.text).join('\n\n---\n\n');
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    onShowToast('Copied to Clipboard', tab === 'single' ? 'Single tweet copied.' : 'Entire thread copied.', 'success');
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCopySingleItem = (text: string, idx: number) => {
    navigator.clipboard.writeText(text);
    onShowToast('Tweet Copied', `Post ${idx + 1} copied to clipboard.`, 'success');
  };

  const handleSaveEdits = () => {
    onUpdate({
      singlePost: singleText,
      thread: threadList
    });
    setIsEditing(false);
    onShowToast('Saved', 'Twitter deliverables updated.', 'info');
  };

  const handleDownload = () => {
    const content = tab === 'single'
      ? singleText
      : threadList.map(t => `[Post ${t.index}/${threadList.length}]\n${t.text}`).join('\n\n');
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `X_Twitter_Thread_${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    onShowToast('Exported', 'Thread saved to text file.', 'success');
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-[#0d121f] p-6 space-y-5 shadow-xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-sky-500/15 border border-sky-500/30 flex items-center justify-center text-sky-400">
            {/* Clean X icon */}
            <span className="font-bold text-base">𝕏</span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-white">Twitter / X</h3>
              <StatusBadge status="ready" size="xs" />
            </div>
            <p className="text-xs text-slate-400">Platform-optimized single post or multi-part narrative thread</p>
          </div>
        </div>

        {/* Post vs Thread Tab Selector */}
        <div className="flex items-center gap-1 p-1 bg-slate-900 border border-slate-800 rounded-lg">
          <button
            onClick={() => setTab('thread')}
            className={`px-3 py-1 text-xs font-semibold rounded-md transition-colors ${
              tab === 'thread' ? 'bg-sky-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Thread ({threadList.length})
          </button>
          <button
            onClick={() => setTab('single')}
            className={`px-3 py-1 text-xs font-semibold rounded-md transition-colors ${
              tab === 'single' ? 'bg-sky-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Single Post
          </button>
        </div>
      </div>

      {/* Content View / Edit */}
      {isEditing ? (
        <div className="space-y-4">
          {tab === 'single' ? (
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Single Post Content</label>
              <textarea
                value={singleText}
                onChange={(e) => setSingleText(e.target.value)}
                rows={4}
                className="w-full rounded-xl bg-slate-900 border border-slate-800 p-3 text-xs text-white focus:outline-none focus:border-sky-500"
              />
              <span className="text-xs font-mono text-slate-400 mt-1 block">{singleText.length} / 280 characters</span>
            </div>
          ) : (
            <div className="space-y-3">
              {threadList.map((item, idx) => (
                <div key={item.index} className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1.5">
                  <span className="text-xs font-bold text-sky-400">Post {item.index} / {threadList.length}</span>
                  <textarea
                    value={item.text}
                    onChange={(e) => {
                      const updated = [...threadList];
                      updated[idx] = { ...updated[idx], text: e.target.value, charCount: e.target.value.length };
                      setThreadList(updated);
                    }}
                    rows={3}
                    className="w-full rounded-lg bg-slate-950 border border-slate-800 p-2 text-xs text-white focus:outline-none focus:border-sky-500"
                  />
                  <span className="text-[11px] font-mono text-slate-400">{item.text.length} / 280 characters</span>
                </div>
              ))}
            </div>
          )}

          <div className="flex justify-end gap-2">
            <button
              onClick={() => setIsEditing(false)}
              className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 text-xs"
            >
              Cancel
            </button>
            <button
              onClick={handleSaveEdits}
              className="px-4 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold"
            >
              Save Edits
            </button>
          </div>
        </div>
      ) : tab === 'single' ? (
        <div className="rounded-xl bg-slate-950/80 border border-slate-800/80 p-5 space-y-3">
          <p className="text-sm text-slate-100 leading-relaxed font-sans">{singleText}</p>
          <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800/60 font-mono">
            <span>{singleText.length} characters</span>
            <span className="text-emerald-400">Within standard 280 limit</span>
          </div>
        </div>
      ) : (
        /* Thread List View */
        <div className="space-y-3">
          {threadList.map((post, idx) => (
            <div
              key={post.index}
              className="relative p-4 rounded-xl bg-slate-950/70 border border-slate-800 hover:border-slate-700 transition-colors flex gap-3.5 items-start group"
            >
              {/* Thread connector line */}
              {idx < threadList.length - 1 && (
                <div className="absolute left-7 top-10 bottom-0 w-0.5 -mb-3 bg-slate-800" />
              )}

              <div className="w-6 h-6 rounded-full bg-sky-500/20 text-sky-400 text-xs font-bold font-mono flex items-center justify-center shrink-0 border border-sky-500/30">
                {post.index}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                  <span className="font-semibold text-slate-300">Post {post.index} / {threadList.length}</span>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[11px]">{post.text.length} chars</span>
                    <button
                      onClick={() => handleCopySingleItem(post.text, idx)}
                      className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-white rounded transition-opacity"
                      title="Copy this post"
                    >
                      <Copy className="w-3 h-3" />
                    </button>
                  </div>
                </div>
                <p className="text-xs sm:text-sm text-slate-200 leading-relaxed whitespace-pre-line font-sans">
                  {post.text}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsEditing(!isEditing)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors"
          >
            <Edit3 className="w-3.5 h-3.5" />
            <span>{isEditing ? 'Editing' : 'Edit'}</span>
          </button>

          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Copied' : tab === 'single' ? 'Copy Post' : 'Copy Thread'}</span>
          </button>

          <button
            onClick={handleDownload}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export .txt</span>
          </button>
        </div>

        <button
          onClick={onPublishToMcp}
          className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold shadow-md shadow-sky-600/20 transition-all cursor-pointer"
          title="Publish to X"
        >
          <Send className="w-3.5 h-3.5" />
          <span>Publish to X</span>
        </button>
      </div>
    </div>
  );
};
