import React from 'react';
import { JobDetailResponse } from '../types';
import {
  Clock,
  Download,
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
    <div className="max-w-4xl mx-auto py-8 space-y-6 linear-animate-entrance">
      <div className="flex items-center justify-between pb-4 border-b border-outline-variant/30">
        <div>
          <h2 className="text-xl font-geist font-semibold text-on-surface tracking-tight">
            Job History
          </h2>
          <p className="text-xs text-on-surface-variant mt-0.5">
            Previous playlist synthesis runs and generated handbooks.
          </p>
        </div>

        <button
          onClick={onRefresh}
          className="p-2 rounded-xl bg-surface-container hover:bg-surface-container-high border border-outline-variant/30 text-on-surface-variant hover:text-on-surface smooth-transition flex items-center gap-1.5 text-xs"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {jobs.length === 0 ? (
        <div className="bg-surface-container-low border border-outline-variant/20 rounded-2xl p-12 text-center space-y-2">
          <Clock className="w-6 h-6 text-outline mx-auto" />
          <h3 className="text-sm font-semibold text-on-surface">No Generated Handbooks</h3>
          <p className="text-xs text-on-surface-variant max-w-xs mx-auto">
            Submit a playlist in the Generate tab to create your first set of notes.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {jobs.map((job) => {
            const isCompleted = job.status === 'COMPLETED' || job.status === 'PARTIAL_SUCCESS';

            return (
              <div
                key={job.id}
                className="bg-surface-container-low border border-outline-variant/20 hover:border-outline-variant/40 p-4 rounded-xl smooth-transition flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                <div className="space-y-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-mono px-2 py-0.2 rounded-full uppercase ${
                      isCompleted ? 'text-primary bg-primary-container/10' : 'text-on-surface-variant bg-surface-container'
                    }`}>
                      {job.status}
                    </span>
                    <span className="text-[11px] text-outline">
                      {new Date(job.created_at).toLocaleDateString()}
                    </span>
                  </div>

                  <h3 className="font-geist text-sm sm:text-base font-semibold text-on-surface truncate">
                    {job.playlist_title}
                  </h3>

                  <div className="text-xs text-on-surface-variant">
                    {job.completed_videos} of {job.total_videos} lectures completed
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  {isCompleted && (
                    <a
                      href={getDownloadUrl(job.id)}
                      target="_blank"
                      rel="noreferrer"
                      className="p-2 rounded-xl bg-surface-container hover:bg-surface-container-high text-on-surface text-xs border border-outline-variant/30 smooth-transition"
                      title="Download PDF"
                    >
                      <Download className="w-4 h-4 text-primary" />
                    </a>
                  )}

                  <button
                    onClick={() => onSelectJob(job.id)}
                    className="px-3.5 py-1.5 rounded-xl bg-primary-container hover:bg-primary-container/90 text-on-primary-container text-xs font-medium flex items-center gap-1.5 shadow-sm smooth-transition active:scale-[0.98]"
                  >
                    <span>View Notes</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
