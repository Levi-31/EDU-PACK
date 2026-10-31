import React, { useState } from 'react';
import { Youtube, ArrowRight, X, Sparkles, ShieldCheck, Workflow, FileText, CheckCircle2 } from 'lucide-react';

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

  const loadPreset = (presetUrl: string) => {
    setPlaylistInput(presetUrl);
    onFetchPreview(presetUrl);
  };

  return (
    <div className="relative w-full max-w-4xl mx-auto flex flex-col items-center pt-8 pb-16 px-4 linear-animate-entrance">
      {/* Subtle Radial Gradient Glow */}
      <div className="absolute top-12 left-1/2 -translate-x-1/2 w-[540px] h-[300px] bg-gradient-to-tr from-secondary-container/10 via-primary-container/15 to-tertiary-container/10 blur-[100px] pointer-events-none rounded-full opacity-60"></div>

      {/* Refined Badge Pill */}
      <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-surface-container-high/70 backdrop-blur-md shadow-sm mb-6 border border-outline-variant/30 text-xs font-mono">
        <span className="w-2 h-2 rounded-full bg-tertiary animate-pulse"></span>
        <span className="text-on-surface-variant tracking-wider uppercase font-semibold">
          Autonomous Curriculum Synthesis
        </span>
        <span className="text-outline">&bull;</span>
        <span className="text-primary font-normal">Multi-Agent</span>
      </div>

      {/* Main Headline & Subtitle */}
      <div className="text-center max-w-2xl mb-8 relative z-10 flex flex-col items-center">
        <h1 className="font-geist text-3xl sm:text-4xl lg:text-5xl text-on-surface font-semibold tracking-tight leading-tight mb-3">
          Turn Any YouTube Playlist Into A Structured Study Handbook
        </h1>
        <p className="text-sm sm:text-base text-on-surface-variant font-sans max-w-xl leading-relaxed">
          Extracts verified video transcripts, enriches concepts with foundational theory,
          generates visual diagrams, and compiles an editorial monograph PDF.
        </p>
      </div>

      {/* Input Box */}
      <div className="w-full max-w-2xl mb-8 relative z-10">
        <div className="relative bg-surface-container/90 backdrop-blur-xl rounded-2xl p-2 shadow-xl border border-outline-variant/40 focus-within:border-primary-container focus-within:shadow-[0_0_24px_rgba(94,106,210,0.25)] smooth-transition">
          <form onSubmit={handleSubmit} className="flex items-center gap-2 w-full">
            <div className="pl-3 text-red-500 shrink-0">
              <Youtube className="w-5 h-5 text-red-500" />
            </div>

            <input
              type="text"
              id="playlist-url-input"
              value={playlistInput}
              onChange={(e) => setPlaylistInput(e.target.value)}
              placeholder="https://www.youtube.com/playlist?list=..."
              className="w-full bg-transparent py-2.5 px-1 text-on-surface font-sans text-sm placeholder:text-outline/60 focus:outline-none tracking-tight"
              disabled={isLoading}
              autoFocus
            />

            {playlistInput && (
              <button
                type="button"
                onClick={() => setPlaylistInput('')}
                className="text-outline hover:text-on-surface p-1 smooth-transition"
                title="Clear input"
              >
                <X className="w-4 h-4" />
              </button>
            )}

            <button
              type="submit"
              disabled={isLoading || !playlistInput.trim()}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-primary-container hover:bg-primary-container/90 disabled:opacity-50 disabled:cursor-not-allowed text-on-primary-container rounded-xl font-sans text-xs sm:text-sm font-semibold tracking-tight shadow-sm smooth-transition shrink-0 active:scale-[0.98]"
            >
              {isLoading ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-on-primary-container/30 border-t-on-primary-container rounded-full animate-spin" />
                  <span>Inspecting...</span>
                </>
              ) : (
                <>
                  <span>Fetch Playlist</span>
                  <ArrowRight className="w-4 h-4" />
                  <kbd className="hidden sm:inline-block ml-0.5 px-1.5 py-0.5 rounded bg-surface-container-lowest/40 font-mono text-[10px] text-primary tracking-normal uppercase border border-outline-variant/20">
                    ↵
                  </kbd>
                </>
              )}
            </button>
          </form>
        </div>

        {errorMessage && (
          <div className="mt-3 p-3 rounded-xl bg-error-container/20 border border-error-container/40 text-error text-xs flex items-center gap-2">
            <span className="font-semibold uppercase tracking-wider font-mono">Error:</span>
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Quick Sample Presets */}
        <div className="flex flex-wrap items-center justify-center gap-2 mt-4 text-xs text-on-surface-variant font-mono">
          <span className="text-outline">Quick Samples:</span>
          <button
            type="button"
            onClick={() => loadPreset('https://www.youtube.com/playlist?list=PL_DISTRIBUTED_SYSTEMS_2026')}
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-surface-container-low hover:bg-surface-container text-on-surface-variant hover:text-on-surface smooth-transition border border-outline-variant/30 shadow-sm active:scale-[0.97]"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-tertiary"></span>
            <span>Distributed Systems (4 vids)</span>
          </button>

          <button
            type="button"
            onClick={() => loadPreset('https://www.youtube.com/playlist?list=PL_TRANSFORMER_ARCH_12VIDS')}
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-surface-container-low hover:bg-surface-container text-on-surface-variant hover:text-on-surface smooth-transition border border-outline-variant/30 shadow-sm active:scale-[0.97]"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-primary"></span>
            <span>Transformer Architecture (12 vids)</span>
          </button>
        </div>
      </div>

      {/* 3 Refined Capability Cards: Clean, High-Craft, Not Cluttered */}
      <div className="w-full grid grid-cols-1 md:grid-cols-3 gap-4 mt-4 relative z-10">
        {/* Pillar 1 */}
        <div className="p-5 rounded-2xl bg-surface-container-low/80 hover:bg-surface-container border border-outline-variant/30 hover:border-outline-variant/60 shadow-sm smooth-transition flex flex-col justify-between gap-4">
          <div className="space-y-2">
            <div className="w-9 h-9 rounded-xl bg-surface-container-high flex items-center justify-center text-primary border border-outline-variant/30">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <h3 className="font-geist text-base font-semibold text-on-surface">
              Transcript Grounding
            </h3>
            <p className="text-xs text-on-surface-variant leading-relaxed">
              Every technical explanation links directly to verified video timestamps with zero hallucinated claims.
            </p>
          </div>
          <div className="pt-2 border-t border-outline-variant/20 flex items-center justify-between text-[11px] font-mono text-outline">
            <span className="text-tertiary flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" />
              <span>Timestamp Anchors</span>
            </span>
            <span>Accurate</span>
          </div>
        </div>

        {/* Pillar 2 */}
        <div className="p-5 rounded-2xl bg-surface-container-low/80 hover:bg-surface-container border border-outline-variant/30 hover:border-outline-variant/60 shadow-sm smooth-transition flex flex-col justify-between gap-4">
          <div className="space-y-2">
            <div className="w-9 h-9 rounded-xl bg-surface-container-high flex items-center justify-center text-secondary border border-outline-variant/30">
              <Workflow className="w-4 h-4" />
            </div>
            <h3 className="font-geist text-base font-semibold text-on-surface">
              Architectural Diagrams
            </h3>
            <p className="text-xs text-on-surface-variant leading-relaxed">
              Converts complex multi-step workflows, relationships, and taxonomies into clean vector Mermaid diagrams.
            </p>
          </div>
          <div className="pt-2 border-t border-outline-variant/20 flex items-center justify-between text-[11px] font-mono text-outline">
            <span className="text-secondary flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" />
              <span>Flowcharts & Mindmaps</span>
            </span>
            <span>Mermaid.js</span>
          </div>
        </div>

        {/* Pillar 3 */}
        <div className="p-5 rounded-2xl bg-surface-container-low/80 hover:bg-surface-container border border-outline-variant/30 hover:border-outline-variant/60 shadow-sm smooth-transition flex flex-col justify-between gap-4">
          <div className="space-y-2">
            <div className="w-9 h-9 rounded-xl bg-surface-container-high flex items-center justify-center text-tertiary border border-outline-variant/30">
              <FileText className="w-4 h-4" />
            </div>
            <h3 className="font-geist text-base font-semibold text-on-surface">
              Publication-Grade PDF
            </h3>
            <p className="text-xs text-on-surface-variant leading-relaxed">
              Compiled with university press typography, structured table of contents, and active recall flashcards.
            </p>
          </div>
          <div className="pt-2 border-t border-outline-variant/20 flex items-center justify-between text-[11px] font-mono text-outline">
            <span className="text-primary flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" />
              <span>A4 Monograph</span>
            </span>
            <span>Print-Ready</span>
          </div>
        </div>
      </div>
    </div>
  );
};
