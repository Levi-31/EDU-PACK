import React, { useRef, useEffect } from 'react';
import { JobDetailResponse, JobEvent } from '../types';
import {
  RotateCcw,
  BookOpen,
  FileText,
  CheckCircle2,
  AlertTriangle,
  PlayCircle,
  Terminal,
  Clock,
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
  const logTerminalRef = useRef<HTMLDivElement>(null);
  const effectiveProgress = Math.max(job.progress_percentage, latestProgress);
  const isCompleted = job.status === 'COMPLETED' || job.status === 'PARTIAL_SUCCESS';
  const isFailed = job.status === 'FAILED';

  useEffect(() => {
    if (logTerminalRef.current) {
      logTerminalRef.current.scrollTop = logTerminalRef.current.scrollHeight;
    }
  }, [events]);

  // 4 clear, professional milestones
  const milestones = [
    { id: 'transcripts', label: '1. Ingest Transcripts', active: true },
    { id: 'planning', label: '2. Decompose Topics', active: effectiveProgress >= 25 },
    { id: 'synthesis', label: '3. Synthesize Notes', active: effectiveProgress >= 50 },
    { id: 'export', label: '4. Compile PDF', active: isFinished || effectiveProgress >= 90 },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6 py-6 linear-animate-entrance">
      {/* Main Status & Header Card */}
      <div className="bg-surface-container-low p-6 rounded-2xl border border-outline-variant/30 shadow-md space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full font-mono text-[11px] font-medium ${
                isCompleted
                  ? 'bg-primary-container/20 text-primary border border-primary/30'
                  : isFailed
                  ? 'bg-error-container/20 text-error border border-error-container/30'
                  : 'bg-surface-container-high text-tertiary border border-outline-variant/30'
              }`}>
                <span className={`w-1.5 h-1.5 rounded-full bg-current ${!isFinished ? 'animate-pulse' : ''}`}></span>
                {job.status}
              </span>
              <span className="text-xs text-on-surface-variant font-mono">
                {job.total_videos} videos in queue
              </span>
            </div>

            <h1 className="font-geist text-xl sm:text-2xl font-semibold text-on-surface tracking-tight truncate">
              {job.playlist_title}
            </h1>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2.5 shrink-0 flex-wrap">
            {isFailed && (
              <button
                onClick={onRetry}
                disabled={isRetrying}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-error hover:bg-error/90 text-on-error font-sans text-xs font-semibold shadow-sm transition-all"
              >
                <RotateCcw className={`w-3.5 h-3.5 ${isRetrying ? 'animate-spin' : ''}`} />
                <span>Retry Pipeline</span>
              </button>
            )}

            {isCompleted && (
              <>
                <button
                  onClick={onViewNotes}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-surface-container hover:bg-surface-container-high text-on-surface font-sans text-xs font-medium border border-outline-variant/40 shadow-sm smooth-transition active:scale-[0.98]"
                >
                  <BookOpen className="w-4 h-4 text-primary" />
                  <span>View Notes</span>
                </button>

                <a
                  href={getDownloadUrl(job.id)}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-2 px-5 py-2 rounded-xl bg-primary-container hover:bg-primary-container/90 text-on-primary-container font-sans text-xs font-semibold shadow-sm smooth-transition active:scale-[0.98]"
                >
                  <FileText className="w-4 h-4" />
                  <span>Download PDF</span>
                </a>
              </>
            )}
          </div>
        </div>

        {/* 4 Milestones Stepper */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 font-mono text-[11px]">
          {milestones.map((m) => (
            <div
              key={m.id}
              className={`p-2 rounded-lg border text-center transition-colors ${
                m.active
                  ? 'bg-surface-container-high text-primary border-primary/30 font-semibold'
                  : 'bg-surface-container-lowest text-outline border-outline-variant/20'
              }`}
            >
              {m.label}
            </div>
          ))}
        </div>

        {/* Progress Bar & Stage Indicator */}
        <div className="space-y-2 pt-1">
          <div className="flex justify-between items-center text-xs">
            <span className="text-on-surface-variant font-medium">
              {isFinished ? 'Completed successfully' : (currentStage || job.current_stage || 'Processing curriculum...')}
            </span>
            <span className="font-mono text-primary font-semibold">
              {effectiveProgress.toFixed(0)}%
            </span>
          </div>

          <div className="w-full h-2 rounded-full bg-surface-container-highest overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-primary via-primary-container to-tertiary rounded-full transition-all duration-500 shadow-sm"
              style={{ width: `${effectiveProgress}%` }}
            />
          </div>
        </div>
      </div>

      {/* 2-Column Balanced Layout: Syllabus Progress List (Left) + Clean Event Stream (Right) */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
        {/* Videos Progress List (7 cols) */}
        <div className="md:col-span-7 space-y-2">
          <div className="flex items-center justify-between px-1 text-xs text-outline font-mono">
            <span>
              CURRICULUM QUEUE ({
                (isCompleted && job.completed_videos === 0 && job.videos?.length > 0)
                  ? (job.videos.filter((v) => v.has_notes || v.status === 'COMPLETED').length || job.total_videos)
                  : job.completed_videos
              } / {job.total_videos} DONE)
            </span>
          </div>

          <div className="space-y-2 max-h-[460px] overflow-y-auto pr-1">
            {job.videos && job.videos.length > 0 ? (
              job.videos.map((vid, idx) => {
                const isVidDone = vid.status === 'COMPLETED' || vid.has_notes || (isCompleted && vid.status !== 'FAILED' && vid.status !== 'SKIPPED');
                const isVidFail = vid.status === 'FAILED' || vid.status === 'TRANSCRIPT_FAILED';
                const isVidProc = !isVidDone && !isVidFail && vid.status !== 'SKIPPED' && vid.status !== 'PENDING';

                return (
                  <div
                    key={vid.video_id || idx}
                    className="p-3.5 rounded-xl bg-surface-container-low border border-outline-variant/30 hover:border-outline-variant/60 flex items-center justify-between gap-3 text-xs smooth-transition shadow-sm"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <span className="font-mono text-outline text-[11px] w-5 text-right shrink-0">
                        {String(idx + 1).padStart(2, '0')}
                      </span>
                      <div className="min-w-0">
                        <span className="text-on-surface font-medium truncate block">
                          {vid.title}
                        </span>
                        <span className="text-on-surface-variant/60 font-mono text-[10px]">
                          {vid.duration_formatted ? `${vid.duration_formatted} • ` : ''}Timestamp Verified
                        </span>
                      </div>
                    </div>

                    <div className="shrink-0 font-mono text-[11px]">
                      {isVidDone && (
                        <span className="text-tertiary flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Done</span>
                        </span>
                      )}
                      {isVidProc && (
                        <span className="text-primary flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-primary animate-ping"></span>
                          <span>Synthesizing...</span>
                        </span>
                      )}
                      {isVidFail && (
                        <span className="text-error flex items-center gap-1">
                          <AlertTriangle className="w-3.5 h-3.5" />
                          <span>Failed</span>
                        </span>
                      )}
                      {!isVidDone && !isVidProc && !isVidFail && (
                        <span className="text-outline">Waiting</span>
                      )}
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="p-6 text-center text-on-surface-variant font-mono text-xs bg-surface-container-low rounded-xl border border-outline-variant/20">
                Awaiting queue initialization...
              </div>
            )}
          </div>
        </div>

        {/* Live Execution Stream Box (5 cols) */}
        <div className="md:col-span-5 space-y-2">
          <div className="flex items-center justify-between px-1 text-xs text-outline font-mono">
            <span className="flex items-center gap-1.5">
              <Terminal className="w-3.5 h-3.5 text-primary" />
              <span>EXECUTION EVENT LOG</span>
            </span>
            <span className="text-[10px] text-tertiary">
              {isFinished ? 'Synced' : 'Listening'}
            </span>
          </div>

          <div
            ref={logTerminalRef}
            className="p-3.5 rounded-xl bg-surface-container-lowest border border-outline-variant/30 font-mono text-xs text-on-surface-variant max-h-[460px] h-[340px] overflow-y-auto space-y-2 selection:bg-primary-container shadow-inner"
          >
            {events.length === 0 ? (
              <div className="text-outline text-xs italic py-4">
                Connecting to agent workflow stream...
              </div>
            ) : (
              events.map((evt, idx) => (
                <div key={idx} className="flex items-start gap-2 text-[11px] leading-relaxed">
                  <span className="text-primary font-semibold shrink-0">
                    [{evt.stage || 'STAGE'}]
                  </span>
                  <span className="text-on-surface break-words">
                    {evt.message}
                  </span>
                </div>
              ))
            )}

            {isFinished && (
              <div className="pt-2 text-tertiary font-mono text-[11px] flex items-center gap-1.5 border-t border-outline-variant/20">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Monograph ready for download.</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
