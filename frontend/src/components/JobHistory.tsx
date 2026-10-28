import React from 'react';
import { JobDetailResponse } from '../types';
import {
  Clock,
  CheckCircle2,
  AlertTriangle,
  Download,
  BookOpen,
  ArrowRight,
  RefreshCw
} from 'lucide-react';
import { getDownloadUrl } from '../api/client';

interface JobHistoryProps {
  jobs: JobDetailResponse[];
  isLoading: boolean;
  onSelectJob: (jobId: string) => void;
  onRefresh: () => void;
}

export const JobHistory: React.FC<JobHistoryProps> = ({
  jobs,
  isLoading,
  onSelectJob,
  onRefresh,
}) => {
  return (
    <div className="max-w-5xl mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            Generation Job History
          </h2>
          <p className="text-xs sm:text-sm text-slate-400">
            View previous playlist generation jobs, review generated notes, or download PDFs.
          </p>
        </div>

        <button
          onClick={onRefresh}
          className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 transition-colors flex items-center space-x-1.5 text-xs"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {jobs.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center space-y-3">
          <Clock className="w-8 h-8 text-slate-600 mx-auto" />
          <h3 className="text-base font-semibold text-white">No Jobs Yet</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            Submit your first YouTube playlist URL to generate high-quality technical notes and diagrams.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {jobs.map((job) => {
            const isCompleted = job.status === 'COMPLETED' || job.status === 'PARTIAL_SUCCESS';
            return (
              <div
                key={job.id}
                className="bg-slate-900 border border-slate-800 hover:border-slate-700/80 p-5 rounded-2xl transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm"
              >
                <div className="space-y-1.5 min-w-0">
                  <div className="flex items-center space-x-2">
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider ${
                        isCompleted
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : job.status === 'FAILED'
                          ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                          : 'bg-brand-500/10 text-brand-400 border border-brand-500/20'
                      }`}
                    >
                      {job.status}
                    </span>
                    <span className="text-xs text-slate-500 font-mono">
                      {new Date(job.created_at).toLocaleDateString()} &bull; {new Date(job.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>

                  <h3 className="text-base font-semibold text-white truncate">
                    {job.playlist_title}
                  </h3>

                  <div className="text-xs text-slate-400 flex items-center space-x-3">
                    <span>{job.total_videos} total lectures</span>
                    <span>&bull;</span>
                    <span className="text-emerald-400">{job.completed_videos} completed</span>
                    {job.skipped_videos > 0 && (
                      <>
                        <span>&bull;</span>
                        <span className="text-amber-400">{job.skipped_videos} unavailable</span>
                      </>
                    )}
                  </div>
                </div>

                <div className="flex items-center space-x-2 shrink-0">
                  <button
                    onClick={() => onSelectJob(job.id)}
                    className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-xl flex items-center space-x-1.5 transition-colors"
                  >
                    <BookOpen className="w-3.5 h-3.5 text-brand-400" />
                    <span>View Progress / Notes</span>
                  </button>

                  {isCompleted && (
                    <a
                      href={getDownloadUrl(job.id)}
                      target="_blank"
                      rel="noreferrer"
                      className="p-2 bg-brand-600/20 hover:bg-brand-600/30 text-brand-300 border border-brand-500/30 rounded-xl transition-colors"
                      title="Download PDF"
                    >
                      <Download className="w-4 h-4" />
                    </a>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

