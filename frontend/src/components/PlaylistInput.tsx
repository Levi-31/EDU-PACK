import React, { useState, useMemo } from 'react';
import {
  Youtube,
  ArrowRight,
  X,
  PlaySquare,
  ListVideo
} from 'lucide-react';

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

  // Dynamic detection for single video vs playlist
  const detectedType = useMemo<'video' | 'playlist' | null>(() => {
    const trimmed = playlistInput.trim();
    if (!trimmed) return null;
    if (trimmed.includes('list=')) return 'playlist';
    if (
      trimmed.includes('watch?v=') ||
      trimmed.includes('youtu.be/') ||
      trimmed.includes('/shorts/') ||
      trimmed.includes('/embed/') ||
      trimmed.includes('/v/') ||
      /^[a-zA-Z0-9_-]{11}$/.test(trimmed)
    ) {
      return 'video';
    }
    return null;
  }, [playlistInput]);

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
    <div className="w-full max-w-4xl mx-auto flex flex-col items-center pt-12 pb-20 px-4 linear-animate-entrance">
      {/* Editorial Headline & Subtitle */}
      <div className="text-center max-w-2xl mb-10">
        <h1 className="font-geist text-4xl sm:text-5xl text-on-surface font-semibold tracking-tight leading-tight mb-4">
          Turn videos into study guides.
        </h1>
        <p className="text-base sm:text-lg text-on-surface-variant max-w-xl mx-auto leading-relaxed">
          Convert a YouTube video or complete playlist into detailed, structured notes.
        </p>
      </div>

      {/* Primary Input Box */}
      <div className="w-full max-w-3xl mb-8">
        <div className="bg-surface-container/70 border border-outline-variant/40 rounded-2xl p-5 sm:p-6 shadow-xs focus-within:border-primary/60 focus-within:ring-2 focus-within:ring-primary/15 smooth-transition">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="playlist-url-input" className="block text-sm font-medium text-on-surface mb-2">
                Paste a YouTube video or playlist URL
              </label>

              <div className="relative flex items-center">
                <div className="pl-3.5 pr-2 text-red-500 shrink-0">
                  <Youtube className="w-5 h-5 text-red-500" />
                </div>

                <input
                  type="text"
                  id="playlist-url-input"
                  value={playlistInput}
                  onChange={(e) => setPlaylistInput(e.target.value)}
                  placeholder="https://www.youtube.com/watch?v=... or playlist?list=..."
                  className="w-full bg-surface border border-outline-variant/30 rounded-xl py-3.5 pl-2 pr-28 text-on-surface font-sans text-base placeholder:text-outline/60 focus:outline-none focus:border-primary/50 tracking-tight"
                  disabled={isLoading}
                  autoFocus
                />

                {/* Subtle Detection Badge */}
                {detectedType && (
                  <div className="absolute right-12 hidden sm:flex items-center gap-1 px-2.5 py-1 rounded-md bg-surface-container border border-outline-variant/30 text-[11px] font-medium">
                    {detectedType === 'video' ? (
                      <>
                        <PlaySquare className="w-3.5 h-3.5 text-primary" />
                        <span className="text-on-surface">Video</span>
                      </>
                    ) : (
                      <>
                        <ListVideo className="w-3.5 h-3.5 text-secondary" />
                        <span className="text-on-surface">Playlist</span>
                      </>
                    )}
                  </div>
                )}

                {playlistInput && (
                  <button
                    type="button"
                    onClick={() => setPlaylistInput('')}
                    className="absolute right-4 text-outline hover:text-on-surface p-1 smooth-transition"
                    title="Clear input"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>

            {/* Submit Action */}
            <div className="flex items-center justify-end pt-1">
              <button
                type="submit"
                disabled={isLoading || !playlistInput.trim()}
                className="inline-flex items-center justify-center gap-2 px-6 py-2.5 bg-primary hover:bg-primary/90 disabled:opacity-40 disabled:cursor-not-allowed text-on-primary rounded-xl font-sans text-sm font-semibold tracking-tight shadow-xs smooth-transition active:scale-[0.98]"
              >
                {isLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-on-primary/30 border-t-on-primary rounded-full animate-spin" />
                    <span>Loading...</span>
                  </>
                ) : (
                  <>
                    <span>Generate Notes</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {errorMessage && (
          <div className="mt-4 p-3.5 rounded-xl bg-error/10 border border-error/30 text-error text-xs flex items-center gap-2">
            <span className="font-semibold">Error:</span>
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Minimal Presets */}
        <div className="flex flex-wrap items-center justify-center gap-2 mt-4 text-xs text-on-surface-variant">
          <span className="text-outline">Try an example:</span>

          <button
            type="button"
            onClick={() => loadPreset('https://www.youtube.com/watch?v=fMHGSx8B9gs')}
            className="px-2.5 py-1 rounded-lg bg-surface-container hover:bg-surface-high text-on-surface-variant hover:text-on-surface border border-outline-variant/30 smooth-transition font-medium"
          >
            Video: LLM Fundamentals
          </button>

          <button
            type="button"
            onClick={() => loadPreset('https://www.youtube.com/playlist?list=PL_DISTRIBUTED_SYSTEMS_2026')}
            className="px-2.5 py-1 rounded-lg bg-surface-container hover:bg-surface-high text-on-surface-variant hover:text-on-surface border border-outline-variant/30 smooth-transition font-medium"
          >
            Playlist: Distributed Systems
          </button>
        </div>
      </div>
    </div>
  );
};
