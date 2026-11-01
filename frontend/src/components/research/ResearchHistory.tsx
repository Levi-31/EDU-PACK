import React, { useState, useMemo } from 'react';
import {
  FileText,
  ArrowRight,
  RefreshCw,
  Clock,
  Search,
  BookOpen,
  Image as ImageIcon,
  CheckCircle2,
  AlertCircle,
  Loader2,
  ExternalLink,
  Download,
  Eye,
  X,
  Database
} from 'lucide-react';
import { ResearchJobDetailResponse } from '../../types';
import { getResearchPdfUrl } from '../../api/client';

interface ResearchHistoryProps {
  jobs: ResearchJobDetailResponse[];
  isLoading: boolean;
  onSelectJob: (jobId: string) => void;
  onRefresh: () => void;
}

export const ResearchHistory: React.FC<ResearchHistoryProps> = ({
  jobs,
  isLoading,
  onSelectJob,
  onRefresh,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'COMPLETED' | 'RUNNING' | 'FAILED'>('ALL');
  const [selectedPreviewImage, setSelectedPreviewImage] = useState<string | null>(null);

  const filteredJobs = useMemo(() => {
    return jobs.filter((j) => {
      // Status filter
      if (statusFilter !== 'ALL' && j.status !== statusFilter) {
        return false;
      }
      // Search term
      if (!searchTerm.trim()) return true;
      const term = searchTerm.toLowerCase();
      return (
        (j.article_title && j.article_title.toLowerCase().includes(term)) ||
        (j.topic && j.topic.toLowerCase().includes(term)) ||
        (j.id && j.id.toLowerCase().includes(term))
      );
    });
  }, [jobs, searchTerm, statusFilter]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3 h-3" />
            <span>Completed</span>
          </span>
        );
      case 'RUNNING':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-primary/10 text-primary border border-primary/20 animate-pulse">
            <Loader2 className="w-3 h-3 animate-spin" />
            <span>Running</span>
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20">
            <AlertCircle className="w-3 h-3" />
            <span>Failed</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-surface-container text-on-surface-variant border border-outline-variant/30">
            <Clock className="w-3 h-3" />
            <span>{status}</span>
          </span>
        );
    }
  };

  const getModeBadge = (mode: string) => {
    const modeLabel = mode === 'open_book' ? 'Open Book' : mode === 'hybrid' ? 'Hybrid Search' : 'Closed Book';
    const modeColor =
      mode === 'open_book'
        ? 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20'
        : mode === 'hybrid'
        ? 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20'
        : 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20';

    return (
      <span className={`text-[10px] px-2 py-0.5 rounded-md font-mono font-medium border ${modeColor}`}>
        {modeLabel}
      </span>
    );
  };

  return (
    <div className="max-w-7xl mx-auto py-8 space-y-6 linear-animate-entrance">
      {/* Header and Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-outline-variant/30">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-geist font-semibold text-on-surface tracking-tight">
              Research & Visuals History
            </h2>
            <span className="px-2 py-0.5 rounded-full text-[11px] font-mono bg-primary/10 text-primary border border-primary/20 flex items-center gap-1">
              <Database className="w-3 h-3" />
              <span>MinIO Object Storage</span>
            </span>
          </div>
          <p className="text-sm text-on-surface-variant mt-1">
            Browse all research reports, generated diagrams, and direct publication PDFs persisted in MinIO.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Status Filter */}
          <div className="flex items-center bg-surface-container rounded-xl border border-outline-variant/30 p-1 text-xs">
            {(['ALL', 'COMPLETED', 'RUNNING', 'FAILED'] as const).map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1 rounded-lg font-medium smooth-transition capitalize ${
                  statusFilter === st
                    ? 'bg-surface text-on-surface font-semibold shadow-xs'
                    : 'text-on-surface-variant hover:text-on-surface'
                }`}
              >
                {st.toLowerCase()}
              </button>
            ))}
          </div>

          {/* Search Box */}
          <div className="relative">
            <Search className="w-4 h-4 text-outline absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Filter by title or topic..."
              className="bg-surface-container border border-outline-variant/30 rounded-xl pl-9 pr-3.5 py-1.5 text-xs text-on-surface placeholder:text-outline/60 focus:outline-none focus:border-primary/50 w-48 sm:w-60"
            />
          </div>

          {/* Refresh Button */}
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="p-2 rounded-xl bg-surface-container hover:bg-surface-high text-on-surface-variant hover:text-on-surface border border-outline-variant/30 smooth-transition"
            title="Refresh Table"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      {jobs.length === 0 ? (
        <div className="p-16 text-center space-y-3 bg-surface-container/40 rounded-2xl border border-outline-variant/20">
          <BookOpen className="w-10 h-10 text-outline mx-auto" />
          <h3 className="text-base font-semibold text-on-surface">No Research Reports Yet</h3>
          <p className="text-sm text-on-surface-variant max-w-sm mx-auto">
            Submit your first technical research prompt in the Research tab to synthesize technical reports and visual diagrams.
          </p>
        </div>
      ) : filteredJobs.length === 0 ? (
        <div className="p-12 text-center text-sm text-on-surface-variant bg-surface-container/30 rounded-2xl border border-outline-variant/20">
          No reports matching filter criteria.
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-outline-variant/30 bg-surface shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-outline-variant/30 bg-surface-container-low text-[11px] font-mono uppercase text-on-surface-variant tracking-wider">
                  <th className="py-3.5 px-4 font-semibold">Report & Topic</th>
                  <th className="py-3.5 px-4 font-semibold">Status</th>
                  <th className="py-3.5 px-4 font-semibold">Mode</th>
                  <th className="py-3.5 px-4 font-semibold">Generated Images (MinIO)</th>
                  <th className="py-3.5 px-4 font-semibold">PDF File</th>
                  <th className="py-3.5 px-4 font-semibold">Created</th>
                  <th className="py-3.5 px-4 text-right font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant/20 text-xs">
                {filteredJobs.map((job) => {
                  const isCompleted = job.status === 'COMPLETED';
                  const title = job.article_title || job.topic;
                  const minioPdfUrl = job.pdf_url || (isCompleted ? getResearchPdfUrl(job.id) : null);
                  const images = job.image_urls && job.image_urls.length > 0
                    ? job.image_urls
                    : (job.images || []).map((img) => `/api/v1/research/${job.id}/images/${img}`);

                  return (
                    <tr
                      key={job.id}
                      className="hover:bg-surface-container-low/60 smooth-transition group"
                    >
                      {/* 1. Report & Topic */}
                      <td className="py-4 px-4 max-w-xs sm:max-w-sm">
                        <div className="space-y-1">
                          <div
                            onClick={() => onSelectJob(job.id)}
                            className="font-geist font-semibold text-on-surface hover:text-primary cursor-pointer line-clamp-2 smooth-transition text-sm"
                            title={title}
                          >
                            {title}
                          </div>
                          <div className="text-[11px] text-on-surface-variant line-clamp-1 italic font-serif">
                            "{job.topic}"
                          </div>
                          <div className="text-[10px] font-mono text-outline">
                            ID: {job.id.slice(0, 8)}...
                          </div>
                        </div>
                      </td>

                      {/* 2. Status */}
                      <td className="py-4 px-4 whitespace-nowrap">
                        <div className="space-y-1">
                          {getStatusBadge(job.status)}
                          {job.current_stage && job.status === 'RUNNING' && (
                            <div className="text-[10px] text-outline font-mono max-w-[130px] truncate" title={job.current_stage}>
                              {job.current_stage}
                            </div>
                          )}
                        </div>
                      </td>

                      {/* 3. Mode */}
                      <td className="py-4 px-4 whitespace-nowrap">
                        {getModeBadge(job.mode)}
                      </td>

                      {/* 4. Generated Images (MinIO) */}
                      <td className="py-4 px-4">
                        {images.length > 0 ? (
                          <div className="space-y-1.5">
                            <div className="flex items-center gap-1.5">
                              {images.slice(0, 3).map((imgUrl, imgIdx) => (
                                <div
                                  key={imgIdx}
                                  onClick={() => setSelectedPreviewImage(imgUrl)}
                                  className="relative group/thumb w-14 h-9 rounded-lg overflow-hidden border border-outline-variant/40 bg-surface-container cursor-pointer shrink-0 shadow-xs hover:border-primary/60 smooth-transition"
                                  title="Click to view full image from MinIO"
                                >
                                  <img
                                    src={imgUrl}
                                    alt={`Generated visual ${imgIdx + 1}`}
                                    className="w-full h-full object-cover group-hover/thumb:scale-105 smooth-transition"
                                    loading="lazy"
                                  />
                                  <div className="absolute inset-0 bg-black/40 opacity-0 group-hover/thumb:opacity-100 flex items-center justify-center smooth-transition">
                                    <Eye className="w-3 h-3 text-white" />
                                  </div>
                                </div>
                              ))}
                              {images.length > 3 && (
                                <span className="text-[10px] font-mono text-outline px-1.5 py-0.5 bg-surface-container rounded-md">
                                  +{images.length - 3}
                                </span>
                              )}
                            </div>
                            <div className="text-[10px] text-emerald-600 dark:text-emerald-400 font-mono flex items-center gap-1">
                              <span>{images.length} in MinIO</span>
                            </div>
                          </div>
                        ) : (
                          <span className="text-outline text-xs font-mono">—</span>
                        )}
                      </td>

                      {/* 5. PDF File */}
                      <td className="py-4 px-4 whitespace-nowrap">
                        {isCompleted && minioPdfUrl ? (
                          <a
                            href={minioPdfUrl}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 font-medium text-xs smooth-transition shadow-xs"
                            title={job.pdf_url ? `Open MinIO PDF: ${job.pdf_url}` : 'Download PDF'}
                          >
                            <Download className="w-3.5 h-3.5" />
                            <span>Download PDF</span>
                          </a>
                        ) : job.status === 'RUNNING' ? (
                          <span className="text-[11px] text-outline font-mono flex items-center gap-1">
                            <Loader2 className="w-3 h-3 animate-spin text-primary" />
                            <span>Generating...</span>
                          </span>
                        ) : (
                          <span className="text-outline text-xs font-mono">—</span>
                        )}
                      </td>

                      {/* 6. Created */}
                      <td className="py-4 px-4 whitespace-nowrap text-on-surface-variant font-mono text-[11px]">
                        <div className="flex items-center gap-1">
                          <Clock className="w-3 h-3 text-outline" />
                          <span>{new Date(job.created_at).toLocaleDateString()}</span>
                        </div>
                        <div className="text-[10px] text-outline pl-4">
                          {new Date(job.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </div>
                      </td>

                      {/* 7. Action */}
                      <td className="py-4 px-4 text-right whitespace-nowrap">
                        <button
                          onClick={() => onSelectJob(job.id)}
                          className="px-3.5 py-1.5 rounded-xl bg-primary text-on-primary hover:bg-primary/90 font-medium text-xs shadow-xs inline-flex items-center gap-1.5 smooth-transition active:scale-[0.98]"
                        >
                          <span>{isCompleted ? 'Read' : 'View'}</span>
                          <ArrowRight className="w-3 h-3" />
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

      {/* Image Preview Lightbox Modal */}
      {selectedPreviewImage && (
        <div
          className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 sm:p-6"
          onClick={() => setSelectedPreviewImage(null)}
        >
          <div
            className="relative max-w-4xl w-full bg-surface-container rounded-2xl border border-outline-variant/30 overflow-hidden shadow-2xl flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between p-4 border-b border-outline-variant/30">
              <div className="flex items-center gap-2">
                <ImageIcon className="w-4 h-4 text-primary" />
                <span className="text-sm font-semibold text-on-surface">MinIO Persisted Visual</span>
              </div>
              <div className="flex items-center gap-2">
                <a
                  href={selectedPreviewImage}
                  target="_blank"
                  rel="noreferrer"
                  className="px-3 py-1 rounded-lg bg-surface hover:bg-surface-high border border-outline-variant/30 text-xs font-medium text-on-surface flex items-center gap-1.5 smooth-transition"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  <span>Open MinIO URL</span>
                </a>
                <button
                  onClick={() => setSelectedPreviewImage(null)}
                  className="p-1.5 rounded-lg bg-surface hover:bg-surface-high text-on-surface-variant hover:text-on-surface border border-outline-variant/30 smooth-transition"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Modal Body */}
            <div className="p-4 bg-surface-container-lowest flex items-center justify-center min-h-[300px] max-h-[70vh] overflow-hidden">
              <img
                src={selectedPreviewImage}
                alt="Enlarged visual"
                className="max-h-[65vh] w-auto object-contain rounded-lg shadow-sm"
              />
            </div>

            {/* Modal Footer with URL */}
            <div className="p-3 bg-surface-container-low border-t border-outline-variant/30 flex items-center justify-between text-xs font-mono text-outline">
              <div className="truncate max-w-xl">
                Source: <span className="text-on-surface select-all">{selectedPreviewImage}</span>
              </div>
              <span className="text-[11px] text-emerald-500 font-medium">Verified in MinIO S3</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
