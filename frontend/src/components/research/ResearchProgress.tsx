import React, { useEffect, useRef } from 'react';
import {
  Compass,
  CheckCircle2,
  AlertCircle,
  Terminal,
  ArrowRight,
  ExternalLink,
  Layers,
  Sparkles,
  Search,
  Cpu,
  Image,
  RefreshCw
} from 'lucide-react';
import { ResearchJobDetailResponse } from '../../types';

interface ResearchProgressProps {
  job: ResearchJobDetailResponse;
  onViewResults: () => void;
  onBackToInput: () => void;
}

export const ResearchProgress: React.FC<ResearchProgressProps> = ({
  job,
  onViewResults,
  onBackToInput,
}) => {
  const logContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [job.logs]);

  const stages = [
    { id: 'router', label: 'Topic Routing', icon: Compass, threshold: 15 },
    { id: 'research', label: 'Web Research', icon: Search, threshold: 30 },
    { id: 'orchestrator', label: 'Content Planning', icon: Layers, threshold: 45 },
    { id: 'workers', label: 'Section Synthesis', icon: Cpu, threshold: 70 },
    { id: 'images', label: 'Image Planning & Gen', icon: Image, threshold: 85 },
    { id: 'reducer', label: 'Markdown Bundling', icon: Sparkles, threshold: 100 },
  ];

  const isCompleted = job.status === 'COMPLETED';
  const isFailed = job.status === 'FAILED';
  const isRunning = job.status === 'RUNNING' || job.status === 'QUEUED';

  return (
    <div className="max-w-4xl mx-auto py-8 space-y-6 linear-animate-entrance">
      {/* Top Header Card */}
      <div className="p-6 rounded-2xl bg-surface-container/70 border border-outline-variant/30 shadow-xs space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <span className="text-xs text-on-surface-variant font-medium">Research Topic</span>
            <h2 className="text-xl sm:text-2xl font-geist font-semibold text-on-surface tracking-tight">
              {job.topic}
            </h2>
          </div>

          <div className="flex items-center gap-2">
            {isCompleted && (
              <button
                onClick={onViewResults}
                className="px-5 py-2.5 bg-primary hover:bg-primary/90 text-on-primary rounded-xl text-sm font-semibold shadow-xs flex items-center gap-1.5 smooth-transition"
              >
                <span>Read Article</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            )}
            <button
              onClick={onBackToInput}
              className="px-3.5 py-2 bg-surface-container hover:bg-surface-high text-on-surface-variant hover:text-on-surface rounded-xl text-xs font-medium border border-outline-variant/30 smooth-transition"
            >
              New Query
            </button>
          </div>
        </div>

        {/* Progress Bar & Status Text */}
        <div className="space-y-2 pt-2 border-t border-outline-variant/20">
          <div className="flex items-center justify-between text-xs">
            <span className="text-on-surface-variant flex items-center gap-2">
              {isRunning && <span className="w-2 h-2 rounded-full bg-primary animate-ping" />}
              <span className="font-medium">{job.current_stage || 'Synthesizing research...'}</span>
            </span>
            <span className="text-primary font-semibold">
              {Math.round(job.progress_percentage || 0)}%
            </span>
          </div>

          <div className="w-full h-2 bg-surface rounded-full overflow-hidden border border-outline-variant/20">
            <div
              className={`h-full transition-all duration-500 rounded-full ${
                isCompleted ? 'bg-tertiary' : isFailed ? 'bg-error' : 'bg-primary'
              }`}
              style={{ width: `${Math.max(5, Math.min(100, job.progress_percentage || 5))}%` }}
            />
          </div>
        </div>

        {/* 6 Stage Milestones */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 pt-1">
          {stages.map((st, idx) => {
            const Icon = st.icon;
            const isDone = (job.progress_percentage || 0) >= st.threshold || isCompleted;
            const isCurrent = (job.progress_percentage || 0) < st.threshold && (idx === 0 || (job.progress_percentage || 0) >= stages[idx - 1].threshold);

            return (
              <div
                key={st.id}
                className={`p-2.5 rounded-xl border flex flex-col gap-1 smooth-transition text-xs ${
                  isDone
                    ? 'bg-surface border-tertiary/40 text-on-surface'
                    : isCurrent
                    ? 'bg-surface border-primary/50 text-primary shadow-xs'
                    : 'bg-surface/40 border-outline-variant/20 text-outline'
                }`}
              >
                <div className="flex items-center justify-between">
                  <Icon className="w-3.5 h-3.5" />
                  {isDone ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-tertiary" />
                  ) : isCurrent ? (
                    <RefreshCw className="w-3.5 h-3.5 text-primary animate-spin" />
                  ) : null}
                </div>
                <span className="font-medium text-[11px] leading-tight truncate">
                  {st.label}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Router Decision Pill / Summary (if determined) */}
      {job.router_decision && (
        <div className="p-4 rounded-xl bg-surface-container-low border border-outline-variant/30 space-y-2 text-xs">
          <div className="flex items-center justify-between">
            <span className="font-mono text-outline uppercase tracking-wider text-[11px]">
              Router Analysis & Strategy
            </span>
            <span className="font-mono text-primary font-semibold capitalize">
              Mode: {job.router_decision.mode}
            </span>
          </div>
          <p className="text-on-surface-variant leading-relaxed">
            {job.router_decision.reasoning}
          </p>
          {job.router_decision.queries && job.router_decision.queries.length > 0 && (
            <div className="pt-2 border-t border-outline-variant/20">
              <span className="text-[11px] text-outline font-mono block mb-1">Generated Search Queries:</span>
              <div className="flex flex-wrap gap-1.5">
                {job.router_decision.queries.map((q, i) => (
                  <span
                    key={i}
                    className="px-2 py-0.5 rounded bg-surface-container border border-outline-variant/30 text-[11px] font-mono text-on-surface"
                  >
                    "{q}"
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Execution Logs Terminal */}
      <div className="rounded-2xl bg-surface-container-lowest border border-outline-variant/30 overflow-hidden shadow-inner">
        <div className="px-4 py-2.5 bg-surface-container-high/60 border-b border-outline-variant/20 flex items-center justify-between text-xs font-mono text-outline">
          <div className="flex items-center gap-2">
            <Terminal className="w-3.5 h-3.5 text-primary" />
            <span>Agent Graph Execution Trace</span>
          </div>
          <span>{(job.logs || []).length} Events</span>
        </div>

        <div
          ref={logContainerRef}
          className="p-4 max-h-80 overflow-y-auto space-y-1 font-mono text-xs leading-relaxed text-on-surface-variant"
        >
          {job.logs && job.logs.length > 0 ? (
            job.logs.map((logMsg, i) => (
              <div key={i} className="flex items-start gap-2">
                <span className="text-outline select-none text-[11px] shrink-0">›</span>
                <span className="break-all">{logMsg}</span>
              </div>
            ))
          ) : (
            <div className="text-outline italic">Awaiting initial agent activity...</div>
          )}
        </div>
      </div>

      {/* Failure Box */}
      {isFailed && (
        <div className="p-4 rounded-xl bg-error-container/20 border border-error-container/40 text-error text-xs flex items-center gap-3">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <div>
            <div className="font-semibold uppercase tracking-wider font-mono">Research Job Terminated</div>
            <div>{job.error_summary || 'An error occurred during workflow execution.'}</div>
          </div>
        </div>
      )}
    </div>
  );
};

