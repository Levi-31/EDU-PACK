import React from 'react';
import { JobDetailResponse, JobEvent } from '../types';
import {
  CheckCircle,
  Clock,
  AlertTriangle,
  RotateCcw,
  Download,
  BookOpen,
  Terminal,
  Layers,
  ArrowRight
} from 'lucide-react';
import { getDownloadUrl } from '../api/client';

interface JobProgressProps {
  job: JobDetailResponse;
  events: JobEvent[];
  latestProgress: number;
  currentStage: string;
  isFinished: boolean;
  onRetry: () => void;
  onViewNotes: () => void;
  isRetrying: boolean;
}

export const JobProgress: React.FC<JobProgressProps> = ({
  job,
  events,
  latestProgress,
  currentStage,
  isFinished,
  onRetry,
  onViewNotes,
  isRetrying,
}) => {
  const effectiveProgress = Math.max(job.progress_percentage, latestProgress);
  const isCompleted = job.status === 'COMPLETED' || job.status === 'PARTIAL_SUCCESS';
  const isFailed = job.status === 'FAILED';

  return (
    <div className="max-w-5xl mx-auto space-y-8 py-4">
      {/* Status Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-brand-500/10 text-brand-400 border border-brand-500/20">
                Agentic Pipeline Execution
              </span>
              <span className="text-xs font-mono text-slate-500">
                ID: {job.id.slice(0, 8)}...
              </span>
            </div>
            <h2 className="text-2xl font-bold text-white tracking-tight">
              {job.playlist_title}
            </h2>
          </div>

          {/* Action CTAs */}
          <div className="flex items-center space-x-3 shrink-0">
            {isFailed && (
              <button
                onClick={onRetry}
                disabled={isRetrying}
                className="px-4 py-2.5 bg-rose-600 hover:bg-rose-500 text-white font-medium text-xs rounded-xl flex items-center space-x-2 transition-colors shadow-lg shadow-rose-600/25"
              >
                <RotateCcw className={`w-3.5 h-3.5 ${isRetrying ? 'animate-spin' : ''}`} />
                <span>Retry Failed Videos</span>
              </button>
            )}

            {isCompleted && (
              <>
                <button
                  onClick={onViewNotes}
                  className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-white font-medium text-xs rounded-xl flex items-center space-x-2 transition-colors border border-slate-700"
                >
                  <BookOpen className="w-3.5 h-3.5 text-brand-400" />
                  <span>View Notes</span>
                </button>
                <a
                  href={getDownloadUrl(job.id)}
                  target="_blank"
                  rel="noreferrer"
                  className="px-5 py-2.5 bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs rounded-xl flex items-center space-x-2 transition-all shadow-lg shadow-brand-600/30"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download Study Guide PDF</span>
                </a>
              </>
            )}
          </div>
        </div>

        {/* Progress Bar & Stage Indicator */}
        <div className="space-y-2">
          <div className="flex justify-between items-center text-xs">
            <span className="font-semibold text-slate-300 flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-brand-400 animate-pulse" />
              <span>Current Stage: <span className="text-brand-300">{currentStage || job.current_stage}</span></span>
            </span>
            <span className="font-mono font-bold text-brand-400">
              {effectiveProgress.toFixed(0)}%
            </span>
          </div>

          <div className="w-full h-3 bg-slate-950 rounded-full overflow-hidden border border-slate-800 p-0.5">
            <div
              className="h-full bg-gradient-to-r from-brand-600 via-sky-500 to-teal-400 rounded-full transition-all duration-500 shadow-sm shadow-brand-500/50"
              style={{ width: `${effectiveProgress}%` }}
            />
          </div>
        </div>

        {/* Counters Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80">
            <div className="text-[11px] font-medium text-slate-500 uppercase">Total Videos</div>
            <div className="text-lg font-bold text-white mt-0.5">{job.total_videos}</div>
          </div>
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80">
            <div className="text-[11px] font-medium text-emerald-500 uppercase">Completed Notes</div>
            <div className="text-lg font-bold text-emerald-400 mt-0.5">{job.completed_videos}</div>
          </div>
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80">
            <div className="text-[11px] font-medium text-amber-500 uppercase">Skipped / Private</div>
            <div className="text-lg font-bold text-amber-400 mt-0.5">{job.skipped_videos}</div>
          </div>
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80">
            <div className="text-[11px] font-medium text-rose-500 uppercase">Failed</div>
            <div className="text-lg font-bold text-rose-400 mt-0.5">{job.failed_videos}</div>
          </div>
        </div>
      </div>

      {/* Main Grid: Per-Video Status & Live Terminal Events */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Ordered Videos Checklist */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
          <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
            <Layers className="w-4 h-4 text-brand-400" />
            <span>Per-Video Pipeline Status</span>
          </h3>

          <div className="space-y-2.5 max-h-[420px] overflow-y-auto pr-1">
            {job.videos.map((v, idx) => (
              <div
                key={v.video_id}
                className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 flex items-center justify-between text-xs"
              >
                <div className="flex items-center space-x-3 min-w-0 pr-2">
                  <span className="font-mono text-slate-500 font-bold w-5 shrink-0">
                    #{idx + 1}
                  </span>
                  <div className="min-w-0">
                    <div className="text-slate-200 font-medium truncate">{v.title}</div>
                    <div className="flex items-center space-x-2 text-[11px] text-slate-500">
                      <span>{v.duration_formatted}</span>
                      {v.error_message && (
                        <span className="text-rose-400 font-mono truncate max-w-xs">&bull; {v.error_message}</span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="shrink-0">
                  {v.status === 'COMPLETED' ? (
                    <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-emerald-500/10 text-emerald-400 font-medium text-[11px]">
                      <CheckCircle className="w-3 h-3" />
                      <span>Notes Done</span>
                    </span>
                  ) : v.status === 'SKIPPED' ? (
                    <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-amber-500/10 text-amber-400 font-medium text-[11px]">
                      <AlertTriangle className="w-3 h-3" />
                      <span>Inaccessible</span>
                    </span>
                  ) : v.status === 'FAILED' || v.status === 'TRANSCRIPT_FAILED' ? (
                    <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-rose-500/10 text-rose-400 font-medium text-[11px]">
                      <AlertTriangle className="w-3 h-3" />
                      <span>Failed</span>
                    </span>
                  ) : (
                    <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded bg-brand-500/10 text-brand-400 font-medium text-[11px]">
                      <div className="w-2.5 h-2.5 border-2 border-brand-400/30 border-t-brand-400 rounded-full animate-spin" />
                      <span>Processing</span>
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Live SSE Event Stream Terminal */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
              <Terminal className="w-4 h-4 text-teal-400" />
              <span>Live Agent Event Log</span>
            </h3>
            <span className="text-[11px] text-slate-500 font-mono">SSE Stream</span>
          </div>

          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800/80 font-mono text-xs text-slate-300 h-[420px] overflow-y-auto space-y-2">
            {events.length === 0 ? (
              <div className="text-slate-600 italic">Waiting for agent workflow stream...</div>
            ) : (
              events.map((ev, i) => (
                <div key={i} className="leading-relaxed">
                  <span className="text-teal-400 font-semibold">[{ev.stage}]</span>{' '}
                  <span className="text-slate-200">{ev.message}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

