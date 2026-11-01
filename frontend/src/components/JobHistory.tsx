import React, { useState, useMemo } from 'react';
import { JobDetailResponse } from '../types';
import {
  Clock,
  Download,
  ArrowRight,
  RefreshCw,
  Search,
  BookOpen,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Database
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
  const [searchTerm, setSearchTerm] = useState('');

  const filteredJobs = useMemo(() => {
    if (!searchTerm.trim()) return jobs;
    const term = searchTerm.toLowerCase();
    return jobs.filter(
      (j) =>
        (j.playlist_title && j.playlist_title.toLowerCase().includes(term)) ||
        (j.id && j.id.toLowerCase().includes(term))
    );
  }, [jobs, searchTerm]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
      case 'PARTIAL_SUCCESS':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3 h-3" />
            <span>{status === 'PARTIAL_SUCCESS' ? 'Partial' : 'Completed'}</span>
          </span>
        );
      case 'FAILED':
      case 'CANCELLED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20">
            <AlertCircle className="w-3 h-3" />
            <span>{status}</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-primary/10 text-primary border border-primary/20 animate-pulse">
            <Loader2 className="w-3 h-3 animate-spin" />
            <span>{status}</span>
          </span>
        );
    }
  };

  return (
    <div className="max-w-6xl mx-auto py-8 space-y-6 linear-animate-entrance">
      {/* Header and Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-outline-variant/30">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-geist font-semibold text-on-surface tracking-tight">
              YouTube Notes History
            </h2>
            <span className="px-2 py-0.5 rounded-full text-[11px] font-mono bg-primary/10 text-primary border border-primary/20 flex items-center gap-1">
              <Database className="w-3 h-3" />
              <span>MinIO Storage</span>
            </span>
          </div>
          <p className="text-sm text-on-surface-variant mt-1">
            Previous playlist synthesis runs, video handbooks, and direct MinIO PDF downloads.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-outline absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search playlists..."
              className="bg-surface-container border border-outline-variant/30 rounded-xl pl-9 pr-3.5 py-1.5 text-xs text-on-surface placeholder:text-outline/60 focus:outline-none focus:border-primary/50 w-48 sm:w-60"
            />
          </div>

          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="p-2 rounded-xl bg-surface-container hover:bg-surface-container-high border border-outline-variant/30 text-on-surface-variant hover:text-on-surface smooth-transition flex items-center gap-1.5 text-xs"
            title="Refresh Table"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {jobs.length === 0 ? (
        <div className="bg-surface-container-low border border-outline-variant/20 rounded-2xl p-16 text-center space-y-2">
          <BookOpen className="w-8 h-8 text-outline mx-auto" />
          <h3 className="text-sm font-semibold text-on-surface">No Generated Handbooks Yet</h3>
          <p className="text-xs text-on-surface-variant max-w-xs mx-auto">
            Submit a playlist in the Generate tab to create your first comprehensive technical handbook.
          </p>
        </div>
      ) : filteredJobs.length === 0 ? (
        <div className="p-12 text-center text-sm text-on-surface-variant bg-surface-container/30 rounded-2xl border border-outline-variant/20">
          No handbooks matching "{searchTerm}".
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-outline-variant/30 bg-surface shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-outline-variant/30 bg-surface-container-low text-[11px] font-mono uppercase text-on-surface-variant tracking-wider">
                  <th className="py-3.5 px-4 font-semibold">Playlist / Video</th>
                  <th className="py-3.5 px-4 font-semibold">Status</th>
                  <th className="py-3.5 px-4 font-semibold">Lectures</th>
                  <th className="py-3.5 px-4 font-semibold">Handbook PDF</th>
                  <th className="py-3.5 px-4 font-semibold">Created</th>
                  <th className="py-3.5 px-4 text-right font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant/20 text-xs">
                {filteredJobs.map((job) => {
                  const isCompleted = job.status === 'COMPLETED' || job.status === 'PARTIAL_SUCCESS';
                  const pdfDownloadUrl = job.pdf_url || (isCompleted ? getDownloadUrl(job.id) : null);

                  return (
                    <tr
                      key={job.id}
                      className="hover:bg-surface-container-low/60 smooth-transition group"
                    >
                      {/* 1. Title */}
                      <td className="py-4 px-4 max-w-xs sm:max-w-md">
                        <div className="space-y-1">
                          <div
                            onClick={() => onSelectJob(job.id)}
                            className="font-geist font-semibold text-on-surface hover:text-primary cursor-pointer line-clamp-2 smooth-transition text-sm"
                            title={job.playlist_title}
                          >
                            {job.playlist_title}
                          </div>
                          <div className="text-[10px] font-mono text-outline">
                            ID: {job.id.slice(0, 8)}... {job.source_type ? `• ${job.source_type}` : ''}
                          </div>
                        </div>
                      </td>

                      {/* 2. Status */}
                      <td className="py-4 px-4 whitespace-nowrap">
                        {getStatusBadge(job.status)}
                      </td>

                      {/* 3. Lectures */}
                      <td className="py-4 px-4 whitespace-nowrap font-mono text-[11px] text-on-surface-variant">
                        <span>{job.completed_videos}</span> / <span>{job.total_videos}</span> completed
                      </td>

                      {/* 4. PDF File */}
                      <td className="py-4 px-4 whitespace-nowrap">
                        {isCompleted && pdfDownloadUrl ? (
                          <a
                            href={pdfDownloadUrl}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 font-medium text-xs smooth-transition shadow-xs"
                            title={job.pdf_url ? `Open MinIO PDF: ${job.pdf_url}` : 'Download PDF'}
                          >
                            <Download className="w-3.5 h-3.5" />
                            <span>Download PDF</span>
                          </a>
                        ) : (
                          <span className="text-outline text-xs font-mono">—</span>
                        )}
                      </td>

                      {/* 5. Created */}
                      <td className="py-4 px-4 whitespace-nowrap text-on-surface-variant font-mono text-[11px]">
                        <div className="flex items-center gap-1">
                          <Clock className="w-3 h-3 text-outline" />
                          <span>{new Date(job.created_at).toLocaleDateString()}</span>
                        </div>
                      </td>

                      {/* 6. Action */}
                      <td className="py-4 px-4 text-right whitespace-nowrap">
                        <button
                          onClick={() => onSelectJob(job.id)}
                          className="px-3.5 py-1.5 rounded-xl bg-primary text-on-primary hover:bg-primary/90 font-medium text-xs shadow-xs inline-flex items-center gap-1.5 smooth-transition active:scale-[0.98]"
                        >
                          <span>View Notes</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
