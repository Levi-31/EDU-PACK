import React, { useState } from 'react';
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
  Play
} from 'lucide-react';

interface PlaylistPreviewProps {
  preview: PlaylistPreviewResponse;
  onBack: () => void;
  onStartJob: (options: GenerationOptions) => void;
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

  const handleStart = () => {
    onStartJob({
      detail_level: detailLevel,
      transcript_language: language,
      enable_visuals: enableVisuals,
      pdf_theme: pdfTheme,
      max_revisions: 1,
    });
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 py-6 linear-animate-entrance">
      {/* Header bar */}
      <div className="flex items-center justify-between pb-4 border-b border-outline-variant/30">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-2 rounded-xl bg-surface-container hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface border border-outline-variant/30 smooth-transition"
            title="Go back"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h2 className="text-xl font-geist font-semibold text-on-surface tracking-tight truncate">
              {preview.title}
            </h2>
            <p className="text-xs text-on-surface-variant mt-0.5">
              {preview.channel_name || 'YouTube Channel'} &bull; {preview.total_videos} lectures detected
            </p>
          </div>
        </div>

        <button
          onClick={handleStart}
          disabled={isStarting}
          className="px-5 py-2.5 bg-primary-container hover:bg-primary-container/90 disabled:opacity-50 text-on-primary-container font-semibold text-xs sm:text-sm rounded-xl transition-all shadow-sm flex items-center gap-2 shrink-0 active:scale-[0.98]"
        >
          {isStarting ? (
            <>
              <div className="w-3.5 h-3.5 border-2 border-on-primary-container/30 border-t-on-primary-container rounded-full animate-spin" />
              <span>Starting...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              <span>Start Generation</span>
            </>
          )}
        </button>
      </div>

      {/* Settings Row: Clean & Compact */}
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
              className="rounded bg-surface-container border-outline-variant text-primary-container focus:ring-0"
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

      {/* Videos List */}
      <div className="space-y-2">
        <div className="text-xs text-outline px-1 font-mono uppercase tracking-wider">
          Curriculum Queue ({preview.videos.length} Videos)
        </div>

        <div className="space-y-1.5 max-h-[50vh] overflow-y-auto pr-1">
          {preview.videos.map((video, idx) => (
            <div
              key={video.video_id}
              className={`p-3 rounded-xl border flex items-center justify-between gap-3 smooth-transition ${
                video.is_available
                  ? 'bg-surface-container-low hover:bg-surface-container border-outline-variant/20'
                  : 'bg-surface-container-lowest/30 border-outline-variant/10 opacity-60'
              }`}
            >
              <div className="flex items-center gap-3 min-w-0">
                <span className="font-mono text-xs text-outline w-6 text-right shrink-0">
                  {idx + 1}
                </span>

                <div className="min-w-0">
                  <h4 className="text-xs sm:text-sm font-medium text-on-surface truncate">
                    {video.title}
                  </h4>
                  <p className="text-[11px] text-on-surface-variant/70 truncate">
                    {video.duration_formatted ? `${video.duration_formatted} • ` : ''}{video.channel_title || 'YouTube'}
                  </p>
                </div>
              </div>

              <div className="shrink-0 text-xs font-mono">
                {video.is_available ? (
                  <span className="text-tertiary flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Ready</span>
                  </span>
                ) : (
                  <span className="text-error flex items-center gap-1">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    <span>Unavailable</span>
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
