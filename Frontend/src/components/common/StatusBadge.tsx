import React from 'react';
import { Check, AlertTriangle, AlertOctagon, Loader2 } from 'lucide-react';

export type CoreStatus = 
  | 'ready'          // 🟢 SUCCESS: ✓ Ready
  | 'verified'       // 🟢 SUCCESS: ✓ Verified
  | 'processing'     // 🟣 PROCESSING: ◌ Processing
  | 'active'         // 🔵 ACTIVE: ● Active
  | 'needs_review'   // 🟡 WARNING: ⚠ Needs Review
  | 'failed';        // 🔴 ERROR: ● Failed

export interface StatusBadgeProps {
  status: CoreStatus | string;
  label?: string;
  size?: 'xs' | 'sm' | 'md';
  variant?: 'badge' | 'text-only' | 'dot-only';
  className?: string;
}

export function normalizeStatus(raw: string): CoreStatus {
  const s = (raw || '').toLowerCase().trim();
  if (s === 'failed' || s.includes('fail') || s === 'error' || s === 'disconnected') return 'failed';
  if (s === 'needs_review' || s.includes('review') || s === 'warning' || s === 'tlp:amber') return 'needs_review';
  if (s === 'processing' || s.includes('process') || s === 'synthesizing' || s === 'generating') return 'processing';
  if (s === 'active' || s === 'online' || s === 'connected' || s === 'synced') return 'active';
  if (s === 'verified' || s.includes('verif') || s.includes('validated')) return 'verified';
  return 'ready';
}

interface StatusConfig {
  defaultLabel: string;
  containerClasses: string;
  icon: React.ReactNode;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  label,
  size = 'sm',
  variant = 'badge',
  className = ''
}) => {
  const core = normalizeStatus(status);

  const configs: Record<CoreStatus, StatusConfig> = {
    ready: {
      defaultLabel: 'Ready',
      containerClasses: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
      icon: <Check className="w-3 h-3 stroke-[2.5] text-emerald-400" />
    },
    verified: {
      defaultLabel: 'Verified',
      containerClasses: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
      icon: <Check className="w-3 h-3 stroke-[2.5] text-emerald-400" />
    },
    processing: {
      defaultLabel: 'Processing',
      containerClasses: 'bg-purple-500/15 border-purple-500/30 text-purple-300 animate-pulse',
      icon: <Loader2 className="w-3 h-3 animate-spin text-purple-300" />
    },
    active: {
      defaultLabel: 'Active',
      containerClasses: 'bg-sky-500/10 border-sky-500/30 text-sky-400',
      icon: <span className="w-1.5 h-1.5 rounded-full bg-sky-400 inline-block shrink-0" />
    },
    needs_review: {
      defaultLabel: 'Needs Review',
      containerClasses: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
      icon: <AlertTriangle className="w-3 h-3 text-amber-400" />
    },
    failed: {
      defaultLabel: 'Failed',
      containerClasses: 'bg-rose-500/10 border-rose-500/30 text-rose-400',
      icon: <span className="w-1.5 h-1.5 rounded-full bg-rose-400 inline-block shrink-0" />
    }
  };

  const current = configs[core];
  const displayLabel = label || current.defaultLabel;

  if (variant === 'dot-only') {
    return (
      <span className={`inline-flex items-center ${className}`} title={displayLabel}>
        {current.icon}
      </span>
    );
  }

  if (variant === 'text-only') {
    const textColors: Record<CoreStatus, string> = {
      ready: 'text-emerald-400',
      verified: 'text-emerald-400',
      processing: 'text-purple-300',
      active: 'text-sky-400',
      needs_review: 'text-amber-400',
      failed: 'text-rose-400'
    };

    return (
      <span className={`inline-flex items-center gap-1.5 font-mono text-[11px] font-medium ${textColors[core]} ${className}`}>
        {current.icon}
        <span>{core === 'ready' || core === 'verified' ? `✓ ${displayLabel}` : core === 'processing' ? `◌ ${displayLabel}` : core === 'needs_review' ? `⚠ ${displayLabel}` : `● ${displayLabel}`}</span>
      </span>
    );
  }

  const sizeClasses = {
    xs: 'px-1.5 py-0.5 text-[10px]',
    sm: 'px-2 py-0.5 text-[11px]',
    md: 'px-2.5 py-1 text-xs'
  }[size];

  // Standardized Wording format:
  // 🟢 SUCCESS: ✓ Ready or ✓ Verified
  // 🟣 PROCESSING: ◌ Processing
  // 🔵 ACTIVE: ● Active
  // 🟡 WARNING: ⚠ Needs Review
  // 🔴 ERROR: ● Failed
  const prefix = core === 'ready' || core === 'verified' 
    ? '✓ ' 
    : core === 'processing' 
      ? '◌ ' 
      : core === 'needs_review' 
        ? '⚠ ' 
        : '● ';

  return (
    <span 
      className={`inline-flex items-center gap-1 font-mono font-medium rounded border ${sizeClasses} ${current.containerClasses} ${className}`}
    >
      <span>{prefix}{displayLabel}</span>
    </span>
  );
};
