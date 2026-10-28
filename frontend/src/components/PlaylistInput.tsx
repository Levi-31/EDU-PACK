import React, { useState } from 'react';
import { Search, Youtube, Play, ArrowRight, ShieldCheck, FileText, Cpu, CheckCircle } from 'lucide-react';

interface PlaylistInputProps {
  onFetchPreview: (input: string) => void;
  isLoading: boolean;
  errorMessage?: string | null;
}

export const PlaylistInput: React.FC<PlaylistInputProps> = ({
  onFetchPreview,
  isLoading,
  errorMessage,
}) => {
  const [playlistInput, setPlaylistInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (playlistInput.trim()) {
      onFetchPreview(playlistInput.trim());
    }
  };

  const loadSample = (sampleId: string) => {
    setPlaylistInput(sampleId);
    onFetchPreview(sampleId);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-12 py-6">
      {/* Hero Header */}
      <div className="text-center space-y-4">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-400 text-xs font-semibold uppercase tracking-wider">
          <Cpu className="w-3.5 h-3.5" />
          <span>Agentic Technical Education Platform</span>
        </div>
        <h1 className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight leading-tight">
          Turn Any YouTube Playlist Into A <br />
          <span className="bg-gradient-to-r from-brand-400 via-sky-300 to-teal-300 bg-clip-text text-transparent">
            Production-Grade Technical Study Guide
          </span>
        </h1>
        <p className="text-base sm:text-lg text-slate-400 max-w-2xl mx-auto">
          Autonomous multi-agent synthesis with LangGraph. Extracts verified transcripts,
          generates architectural diagrams, preserves precise video timestamps, and compiles a publication-ready PDF.
        </p>
      </div>

      {/* Input Form Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 -mt-8 -mr-8 w-48 h-48 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />

        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block text-sm font-medium text-slate-300">
            YouTube Playlist URL or Playlist ID
          </label>
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                <Youtube className="w-5 h-5 text-red-500" />
              </div>
              <input
                type="text"
                value={playlistInput}
                onChange={(e) => setPlaylistInput(e.target.value)}
                placeholder="https://www.youtube.com/playlist?list=PL_DISTRIBUTED_SYSTEMS_2026"
                className="w-full pl-11 pr-4 py-3.5 bg-slate-950 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent text-sm transition-all"
                disabled={isLoading}
              />
            </div>
            <button
              type="submit"
              disabled={isLoading || !playlistInput.trim()}
              className="px-6 py-3.5 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold text-sm rounded-xl transition-all shadow-lg shadow-brand-600/25 flex items-center justify-center space-x-2 shrink-0"
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Inspecting Playlist...</span>
                </>
              ) : (
                <>
                  <span>Fetch Playlist</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>

          {errorMessage && (
            <div className="p-3.5 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center space-x-2">
              <span className="font-semibold">Error:</span>
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Quick Demo Buttons */}
          <div className="pt-2 flex flex-wrap items-center gap-2 text-xs text-slate-400">
            <span className="font-medium text-slate-500">Quick Test Samples:</span>
            <button
              type="button"
              onClick={() => loadSample('https://www.youtube.com/playlist?list=PL_DISTRIBUTED_SYSTEMS_2026')}
              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700/60 transition-colors flex items-center space-x-1"
            >
              <Play className="w-3 h-3 text-brand-400" />
              <span>Distributed Systems (4 Videos)</span>
            </button>
            <button
              type="button"
              onClick={() => loadSample('PL_PAGINATED_MULTI_PAGE_SERIES')}
              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700/60 transition-colors flex items-center space-x-1"
            >
              <Play className="w-3 h-3 text-teal-400" />
              <span>55-Video Paginated Boundary Test</span>
            </button>
          </div>
        </form>
      </div>

      {/* Feature Pillars */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4">
        <div className="bg-slate-900/60 border border-slate-800/80 p-5 rounded-xl space-y-2.5">
          <div className="w-9 h-9 rounded-lg bg-sky-500/10 text-sky-400 flex items-center justify-center">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <h3 className="font-semibold text-white text-sm">Grounded Transcripts & Timestamps</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Every section links directly back to the exact video timestamp. Zero hallucinated timestamps or fabricated claims.
          </p>
        </div>

        <div className="bg-slate-900/60 border border-slate-800/80 p-5 rounded-xl space-y-2.5">
          <div className="w-9 h-9 rounded-lg bg-teal-500/10 text-teal-400 flex items-center justify-center">
            <Cpu className="w-5 h-5" />
          </div>
          <h3 className="font-semibold text-white text-sm">LangGraph Agentic Review</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Multi-stage workflow: Planning coordinator, transcript chunking, notes extraction, conditional Mermaid visuals, and critic agent.
          </p>
        </div>

        <div className="bg-slate-900/60 border border-slate-800/80 p-5 rounded-xl space-y-2.5">
          <div className="w-9 h-9 rounded-lg bg-purple-500/10 text-purple-400 flex items-center justify-center">
            <FileText className="w-5 h-5" />
          </div>
          <h3 className="font-semibold text-white text-sm">Publication-Grade PDF</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Rendered with headless Chromium. Features editorial cover, clickable table of contents, code blocks, diagrams, and recap flashcards.
          </p>
        </div>
      </div>
    </div>
  );
};
