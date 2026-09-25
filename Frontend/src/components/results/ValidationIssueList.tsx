import React from 'react';
import { AlertCircle, AlertTriangle, Info, XOctagon } from 'lucide-react';

export interface ValidationIssueItem {
  issue_id: string;
  issue_type: string;
  severity: string;
  message: string;
  generated_text?: string;
  location?: string;
}

export interface ValidationIssueListProps {
  issues: ValidationIssueItem[];
  title?: string;
}

export const ValidationIssueList: React.FC<ValidationIssueListProps> = ({
  issues,
  title = 'Validation Audit Findings',
}) => {
  if (!issues || issues.length === 0) {
    return (
      <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm flex items-center gap-2">
        <Info className="w-4 h-4 shrink-0" />
        <span>No factual mismatches or validation errors detected. Content is 100% grounded.</span>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <h4 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
        <AlertTriangle className="w-4 h-4 text-amber-400" />
        {title} ({issues.length})
      </h4>
      <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
        {issues.map((issue) => {
          const sev = (issue.severity || 'WARNING').toUpperCase();
          let border = 'border-amber-500/30 bg-amber-500/5 text-amber-300';
          let Icon = AlertTriangle;

          if (sev === 'CRITICAL' || sev === 'ERROR') {
            border = 'border-rose-500/30 bg-rose-500/5 text-rose-300';
            Icon = XOctagon;
          } else if (sev === 'INFO') {
            border = 'border-blue-500/30 bg-blue-500/5 text-blue-300';
            Icon = Info;
          }

          return (
            <div
              key={issue.issue_id || Math.random().toString()}
              className={`p-3 rounded-lg border text-xs space-y-1 ${border}`}
            >
              <div className="flex items-center justify-between font-mono text-[11px] font-bold">
                <span className="flex items-center gap-1.5">
                  <Icon className="w-3.5 h-3.5 shrink-0" />
                  {issue.issue_type}
                </span>
                <span className="px-1.5 py-0.5 rounded bg-black/30 font-semibold">{sev}</span>
              </div>
              <p className="text-slate-300 text-xs leading-relaxed">{issue.message}</p>
              {issue.generated_text && (
                <div className="mt-1 p-1.5 rounded bg-black/40 text-[11px] font-mono text-slate-400">
                  <span className="text-slate-500">Flagged Text:</span> "{issue.generated_text}"
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
