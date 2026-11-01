import React, { useState } from 'react';
import {
  ArrowRight,
  Calendar,
  ChevronDown,
  ChevronUp,
  Clock,
  Sparkles
} from 'lucide-react';
import { CreateResearchJobRequest, ResearchJobDetailResponse } from '../../types';

interface ResearchLandingProps {
  onStartResearch: (req: CreateResearchJobRequest) => void;
  isLoading: boolean;
  recentJobs: ResearchJobDetailResponse[];
  onSelectJob: (jobId: string) => void;
}

export const ResearchLanding: React.FC<ResearchLandingProps> = ({
  onStartResearch,
  isLoading,
  recentJobs,
  onSelectJob,
}) => {
  const [topic, setTopic] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [asOfDate, setAsOfDate] = useState(() => {
    return new Date().toISOString().split('T')[0];
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (topic.trim()) {
      onStartResearch({
        topic: topic.trim(),
        as_of: asOfDate.trim() || undefined,
      });
    }
  };

  const handleSelectPreset = (presetTopic: string) => {
    setTopic(presetTopic);
  };

  const examples = [
    'Modern Vector Databases Architecture',
    'PostgreSQL 17 Query Optimizer Improvements',
    'SQLite Virtual Machine Internals',
  ];

  return (
    <div className="w-full max-w-4xl mx-auto flex flex-col items-center pt-12 pb-20 px-4 linear-animate-entrance">
      {/* Editorial Headline & Subtitle */}
      <div className="text-center max-w-2xl mb-10">
        <h1 className="font-geist text-4xl sm:text-5xl text-on-surface font-semibold tracking-tight leading-tight mb-4">
          Research a topic. Go deeper.
        </h1>
        <p className="text-base sm:text-lg text-on-surface-variant max-w-xl mx-auto leading-relaxed">
          Generate detailed, source-backed research reports from any technical or general topic.
        </p>
      </div>

      {/* Primary Research Form */}
      <div className="w-full max-w-3xl mb-10">
        <div className="bg-surface-container/70 border border-outline-variant/40 rounded-2xl p-5 sm:p-6 shadow-xs focus-within:border-primary/60 focus-within:ring-2 focus-within:ring-primary/15 smooth-transition">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="research-topic" className="block text-sm font-medium text-on-surface mb-2">
                What would you like to research?
              </label>
              <textarea
                id="research-topic"
                rows={3}
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="Enter a topic or research question (e.g. Next.js 15 Server Actions, Distributed Consensus in Raft...)"
                className="w-full bg-surface border border-outline-variant/30 rounded-xl p-3.5 text-on-surface font-sans text-base placeholder:text-outline/60 focus:outline-none focus:border-primary/50 tracking-tight resize-none leading-relaxed"
                disabled={isLoading}
                autoFocus
              />
            </div>

            {/* Advanced Options Accordion */}
            <div className="border-t border-outline-variant/20 pt-3">
              <button
                type="button"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="flex items-center gap-1.5 text-xs text-on-surface-variant hover:text-on-surface font-medium smooth-transition select-none"
              >
                <span>Advanced options</span>
                {showAdvanced ? (
                  <ChevronUp className="w-3.5 h-3.5" />
                ) : (
                  <ChevronDown className="w-3.5 h-3.5" />
                )}
              </button>

              {showAdvanced && (
                <div className="mt-3 pt-2 flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-outline shrink-0" />
                    <span className="text-xs text-on-surface-variant font-medium shrink-0">As-Of Date:</span>
                    <input
                      type="date"
                      value={asOfDate}
                      onChange={(e) => setAsOfDate(e.target.value)}
                      disabled={isLoading}
                      className="bg-surface border border-outline-variant/30 rounded-lg px-2.5 py-1 text-xs text-on-surface focus:outline-none focus:border-primary/50"
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Submit Action */}
            <div className="flex items-center justify-end pt-1">
              <button
                type="submit"
                disabled={isLoading || !topic.trim()}
                className="inline-flex items-center justify-center gap-2 px-6 py-2.5 bg-primary hover:bg-primary/90 disabled:opacity-40 disabled:cursor-not-allowed text-on-primary rounded-xl font-sans text-sm font-semibold tracking-tight shadow-xs smooth-transition active:scale-[0.98]"
              >
                {isLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-on-primary/30 border-t-on-primary rounded-full animate-spin" />
                    <span>Researching...</span>
                  </>
                ) : (
                  <>
                    <span>Run Research</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Minimal Examples */}
        <div className="flex flex-wrap items-center justify-center gap-2 mt-4 text-xs text-on-surface-variant">
          <span className="text-outline">Explore examples:</span>
          {examples.map((ex) => (
            <button
              key={ex}
              type="button"
              onClick={() => handleSelectPreset(ex)}
              className="px-2.5 py-1 rounded-lg bg-surface-container hover:bg-surface-high text-on-surface-variant hover:text-on-surface border border-outline-variant/30 smooth-transition font-medium"
            >
              {ex}
            </button>
          ))}
        </div>
      </div>

      {/* Clean Recent Research Runs */}
      {recentJobs && recentJobs.length > 0 && (
        <div className="w-full max-w-3xl mt-8 space-y-3">
          <div className="flex items-center justify-between text-xs text-on-surface-variant px-1 font-medium">
            <span>Recent Research</span>
            <span className="text-outline">{recentJobs.length} reports</span>
          </div>

          <div className="space-y-2">
            {recentJobs.slice(0, 4).map((job) => (
              <div
                key={job.id}
                onClick={() => onSelectJob(job.id)}
                className="p-3.5 rounded-xl bg-surface-container/60 hover:bg-surface-container border border-outline-variant/30 hover:border-outline-variant/60 cursor-pointer smooth-transition flex items-center justify-between gap-3"
              >
                <div className="min-w-0">
                  <h4 className="text-sm font-medium text-on-surface truncate">
                    {job.article_title || job.topic}
                  </h4>
                  <div className="flex items-center gap-2 mt-0.5 text-xs text-outline">
                    <Clock className="w-3 h-3" />
                    <span>{new Date(job.created_at).toLocaleDateString()}</span>
                  </div>
                </div>

                <div className="shrink-0 flex items-center gap-2 text-xs">
                  <span className={`px-2 py-0.5 rounded-md font-medium text-[11px] ${
                    job.status === 'COMPLETED' ? 'bg-tertiary/10 text-tertiary' :
                    job.status === 'RUNNING' ? 'bg-primary/10 text-primary animate-pulse' :
                    job.status === 'FAILED' ? 'bg-error/10 text-error' : 'bg-surface-container text-outline'
                  }`}>
                    {job.status === 'COMPLETED' ? 'Ready' : job.status}
                  </span>
                  <ArrowRight className="w-3.5 h-3.5 text-outline" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

