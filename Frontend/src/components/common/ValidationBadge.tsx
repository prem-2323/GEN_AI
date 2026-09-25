import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, ShieldCheck } from 'lucide-react';

export interface ValidationBadgeProps {
  status: 'PASS' | 'PASS_WITH_WARNINGS' | 'FAIL' | string;
  coverage?: number;
  consistency?: number;
  onClick?: () => void;
}

export const ValidationBadge: React.FC<ValidationBadgeProps> = ({
  status,
  coverage,
  consistency,
  onClick,
}) => {
  const normStatus = (status || 'PASS').toUpperCase();

  let colorClasses = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
  let Icon = CheckCircle2;
  let label = 'PASS';

  if (normStatus === 'PASS_WITH_WARNINGS' || normStatus === 'WARNING') {
    colorClasses = 'bg-amber-500/10 text-amber-400 border-amber-500/30';
    Icon = AlertTriangle;
    label = 'PASS WITH WARNINGS';
  } else if (normStatus === 'FAIL' || normStatus === 'FAILED' || normStatus === 'CRITICAL') {
    colorClasses = 'bg-rose-500/10 text-rose-400 border-rose-500/30';
    Icon = XCircle;
    label = 'VALIDATION FAILED';
  }

  return (
    <div
      onClick={onClick}
      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-semibold cursor-pointer transition-all hover:scale-[1.02] ${colorClasses}`}
      title="Click to view detailed Phase 13 Validation Audit"
    >
      <Icon className="w-4 h-4 shrink-0" />
      <span>{label}</span>
      {typeof coverage === 'number' && (
        <span className="opacity-80 border-l border-current/20 pl-2">
          Coverage: {(coverage * 100).toFixed(0)}%
        </span>
      )}
      {typeof consistency === 'number' && (
        <span className="opacity-80 border-l border-current/20 pl-2">
          Consistency: {(consistency * 100).toFixed(0)}%
        </span>
      )}
    </div>
  );
};
