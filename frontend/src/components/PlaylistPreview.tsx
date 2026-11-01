import React, { useState, useEffect } from 'react';
import {
  PlaylistPreviewResponse,
  GenerationOptions,
  NoteDetailLevel,
  PDFTheme
} from '../types';
import {
  Sparkles,
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  PlaySquare,
  ListVideo,
  Check,
  CheckSquare,
  Square,
  MinusCircle
} from 'lucide-react';

interface PlaylistPreviewProps {
  preview: PlaylistPreviewResponse;
  onBack: () => void;
  onStartJob: (options: GenerationOptions, selectedVideoIds?: string[]) => void;
  isStarting: boolean;
}

export const PlaylistPreview: React.FC<PlaylistPreviewProps> = ({
  preview,
  onBack,
  onStartJob,
  isStarting,
}) => {
  const [detailLevel, setDetailLevel] = useState<NoteDetailLevel>('standard');
  const [language, setLanguage] = useState<string>('en');
  const [enableVisuals, setEnableVisuals] = useState<boolean>(true);
  const [pdfTheme, setPdfTheme] = useState<PDFTheme>('editorial_navy');

  // Multi-video selection state: defaults to all available videos
  const [selectedIds, setSelectedIds] = useState<Set<string>>(() => {
    return new Set(
      preview.videos
        .filter((v) => v.is_available)
        .map((v) => v.video_id)
    );
  });

  // Keep selected IDs in sync if the preview data changes
  useEffect(() => {
    setSelectedIds(
      new Set(
        preview.videos
          .filter((v) => v.is_available)
          .map((v) => v.video_id)
      )
    );
  }, [preview.playlist_id, preview.videos]);

  const isSingleVideo = preview.source_type === 'video' || preview.videos.length === 1;
  const availableCount = preview.videos.filter((v) => v.is_available).length;
  const selectedCount = selectedIds.size;
  const allAvailableSelected = availableCount > 0 && selectedCount === availableCount;

  const toggleVideo = (videoId: string, isAvailable: boolean) => {
    if (!isAvailable) return;
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(videoId)) {
        next.delete(videoId);
      } else {
        next.add(videoId);
      }
      return next;
    });
  };

  const handleSelectAll = () => {
    setSelectedIds(
      new Set(
        preview.videos
          .filter((v) => v.is_available)
          .map((v) => v.video_id)
      )
    );
  };

  const handleDeselectAll = () => {
    setSelectedIds(new Set());
  };

  const handleStart = () => {
    if (selectedCount === 0) return;
    onStartJob(
      {
        detail_level: detailLevel,
        transcript_language: language,
        enable_visuals: enableVisuals,
        pdf_theme: pdfTheme,
        max_revisions: 1,
      },
      Array.from(selectedIds)
    );
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 py-6 linear-animate-entrance">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-outline-variant/30">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-2 rounded-xl bg-surface-container hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface border border-outline-variant/30 smooth-transition"
            title="Go back"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase font-semibold flex items-center gap-1 ${
                isSingleVideo ? 'bg-primary/10 text-primary' : 'bg-tertiary/10 text-tertiary'
              }`}>
                {isSingleVideo ? (
                  <>
                    <PlaySquare className="w-3 h-3" />
                    <span>Single Video</span>
                  </>
                ) : (
                  <>
                    <ListVideo className="w-3 h-3" />
                    <span>Playlist ({preview.total_videos} Videos)</span>
                  </>
                )}
              </span>
            </div>
            <h2 className="text-xl font-geist font-semibold text-on-surface tracking-tight truncate max-w-xl">
              {preview.title}
            </h2>
            <p className="text-xs text-on-surface-variant mt-0.5">
              {preview.channel_name || 'YouTube Channel'} &bull;{' '}
              {isSingleVideo
                ? 'Standalone Video Masterclass'
                : `${selectedCount} of ${preview.total_videos} lectures selected for synthesis`}
            </p>
          </div>
        </div>

        <button
          onClick={handleStart}
          disabled={isStarting || selectedCount === 0}
          className="px-5 py-2.5 bg-primary-container hover:bg-primary-container/90 disabled:opacity-40 disabled:cursor-not-allowed text-on-primary-container font-semibold text-xs sm:text-sm rounded-xl transition-all shadow-sm flex items-center gap-2 shrink-0 active:scale-[0.98]"
        >
          {isStarting ? (
            <>
              <div className="w-3.5 h-3.5 border-2 border-on-primary-container/30 border-t-on-primary-container rounded-full animate-spin" />
              <span>Starting...</span>
            </>
          ) : selectedCount === 0 ? (
            <span>Select At Least 1 Video</span>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              <span>
                {isSingleVideo
                  ? 'Generate Study Guide'
                  : `Start Generation (${selectedCount} ${selectedCount === 1 ? 'Lecture' : 'Lectures'})`}
              </span>
            </>
          )}
        </button>
      </div>

      {/* Settings Row */}
      <div className="bg-surface-container-low p-4 rounded-xl border border-outline-variant/30 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs">
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <span className="text-on-surface-variant font-medium shrink-0">Detail:</span>
          <div className="flex items-center p-0.5 bg-surface-container rounded-lg border border-outline-variant/30 w-full sm:w-auto">
            {(['concise', 'standard', 'comprehensive'] as NoteDetailLevel[]).map((lvl) => (
              <button
                key={lvl}
                type="button"
                onClick={() => setDetailLevel(lvl)}
                className={`py-1.5 px-3 rounded-md capitalize smooth-transition text-xs ${
                  detailLevel === lvl
                    ? 'bg-primary-container text-on-primary-container font-semibold shadow-sm'
                    : 'text-on-surface-variant hover:text-on-surface'
                }`}
              >
                {lvl}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-4 w-full sm:w-auto justify-between sm:justify-end">
          <label className="flex items-center gap-2 cursor-pointer select-none text-on-surface-variant hover:text-on-surface">
            <input
              type="checkbox"
              checked={enableVisuals}
              onChange={(e) => setEnableVisuals(e.target.checked)}
              className="rounded bg-surface-container border-outline-variant text-primary focus:ring-0"
            />
            <span>Include Diagrams</span>
          </label>

          <div className="flex items-center gap-1.5">
            <span className="text-on-surface-variant">Theme:</span>
            <select
              value={pdfTheme}
              onChange={(e) => setPdfTheme(e.target.value as PDFTheme)}
              className="py-1 px-2 bg-surface-container border border-outline-variant/30 rounded-lg text-xs text-on-surface focus:outline-none"
            >
              <option value="editorial_navy">Editorial Navy</option>
              <option value="technical_slate">Technical Slate</option>
            </select>
          </div>
        </div>
      </div>

      {/* Videos List with Selection Controls */}
      <div className="space-y-3">
        <div className="flex items-center justify-between px-1">
          <div className="text-xs text-outline font-mono uppercase tracking-wider flex items-center gap-2">
            <span>
              {isSingleVideo
                ? 'Lecture Source'
                : `Curriculum Queue (${selectedCount} of ${preview.videos.length} Selected)`}
            </span>
          </div>

          {!isSingleVideo && (
            <div className="flex items-center gap-2 text-xs font-mono">
              <button
                type="button"
                onClick={allAvailableSelected ? handleDeselectAll : handleSelectAll}
                className="px-2.5 py-1 rounded-lg bg-surface-container hover:bg-surface-container-high border border-outline-variant/30 text-on-surface-variant hover:text-on-surface smooth-transition flex items-center gap-1.5 text-[11px]"
              >
                {allAvailableSelected ? (
                  <>
                    <Square className="w-3 h-3 text-outline" />
                    <span>Deselect All</span>
                  </>
                ) : (
                  <>
                    <CheckSquare className="w-3 h-3 text-primary" />
                    <span>Select All ({availableCount})</span>
                  </>
                )}
              </button>
            </div>
          )}
        </div>

        <div className="space-y-1.5 max-h-[52vh] overflow-y-auto pr-1">
          {preview.videos.map((video, idx) => {
            const isSelected = selectedIds.has(video.video_id);

            return (
              <div
                key={video.video_id}
                onClick={() => toggleVideo(video.video_id, video.is_available)}
                className={`p-3 rounded-xl border flex items-center justify-between gap-3 smooth-transition ${
                  !video.is_available
                    ? 'bg-surface-container-lowest/30 border-outline-variant/10 opacity-50 cursor-not-allowed select-none'
                    : isSelected
                    ? 'bg-surface-container-low hover:bg-surface-container border-outline-variant/30 cursor-pointer shadow-2xs'
                    : 'bg-surface-container-lowest/40 hover:bg-surface-container-lowest/80 border-outline-variant/15 opacity-65 cursor-pointer'
                }`}
              >
                <div className="flex items-center gap-3 min-w-0">
                  {/* Selection Checkbox */}
                  <div className="shrink-0">
                    {!video.is_available ? (
                      <div className="w-4 h-4 rounded border border-outline-variant/30 flex items-center justify-center bg-surface-container-lowest opacity-40">
                        <MinusCircle className="w-3 h-3 text-outline" />
                      </div>
                    ) : (
                      <div
                        className={`w-4 h-4 rounded border flex items-center justify-center smooth-transition ${
                          isSelected
                            ? 'bg-primary border-primary text-on-primary'
                            : 'bg-surface-container border-outline-variant/50 hover:border-outline'
                        }`}
                      >
                        {isSelected && <Check className="w-3 h-3 stroke-[3]" />}
                      </div>
                    )}
                  </div>

                  {/* Video Number */}
                  <span className={`font-mono text-xs w-6 text-right shrink-0 ${isSelected ? 'text-outline' : 'text-outline/50'}`}>
                    {idx + 1}
                  </span>

                  {/* Video Title and Metadata */}
                  <div className="min-w-0">
                    <h4
                      className={`text-xs sm:text-sm font-medium truncate ${
                        isSelected ? 'text-on-surface' : 'text-on-surface-variant/70 line-through decoration-outline/40'
                      }`}
                    >
                      {video.title}
                    </h4>
                    <p className="text-[11px] text-on-surface-variant/70 truncate">
                      {video.duration_formatted ? `${video.duration_formatted} • ` : ''}
                      {video.channel_title || 'YouTube'}
                    </p>
                  </div>
                </div>

                {/* Status Badges */}
                <div className="shrink-0 text-xs font-mono">
                  {!video.is_available ? (
                    <span className="text-error flex items-center gap-1">
                      <AlertTriangle className="w-3.5 h-3.5" />
                      <span>Unavailable</span>
                    </span>
                  ) : isSelected ? (
                    <span className="text-tertiary flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Ready</span>
                    </span>
                  ) : (
                    <span className="text-outline text-[11px] px-2 py-0.5 rounded bg-surface-container border border-outline-variant/20">
                      Excluded
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
