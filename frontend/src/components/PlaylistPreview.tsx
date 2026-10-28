import React, { useState } from 'react';
import {
  PlaylistPreviewResponse,
  GenerationOptions,
  NoteDetailLevel,
  PDFTheme
} from '../types';
import {
  Clock,
  Video,
  Settings,
  Sparkles,
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  FileText
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
    <div className="max-w-5xl mx-auto space-y-8 py-4">
      {/* Back button & Playlist Overview Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div className="flex items-center space-x-3">
          <button
            onClick={onBack}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            title="Go back"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-brand-500/10 text-brand-400 border border-brand-500/20">
                Playlist Preview
              </span>
              {preview.is_mock && (
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                  Demo Mode
                </span>
              )}
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight mt-1">
              {{ preview: preview.title }.preview}
            </h2>
            <p className="text-xs sm:text-sm text-slate-400">
              {preview.channel_name || 'YouTube Creator'} &bull; {preview.total_videos} videos detected
            </p>
          </div>
        </div>

        <button
          onClick={handleStart}
          disabled={isStarting}
          className="px-6 py-3 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white font-semibold text-sm rounded-xl transition-all shadow-lg shadow-brand-600/30 flex items-center justify-center space-x-2 shrink-0"
        >
          {isStarting ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              <span>Launching Agents...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4 text-brand-200" />
              <span>Start Notes Generation</span>
            </>
          )}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Ordered Video Queue */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center space-x-2">
              <Video className="w-4 h-4 text-brand-400" />
              <span>Video Sequence ({preview.videos.length} Lectures)</span>
            </h3>
            <span className="text-xs text-slate-500">
              Preserved in exact original order
            </span>
          </div>

          <div className="space-y-3">
            {preview.videos.map((video, idx) => (
              <div
                key={video.video_id}
                className={`p-3.5 rounded-xl border flex items-start space-x-3.5 transition-all ${
                  video.is_available
                    ? 'bg-slate-900/80 border-slate-800 hover:border-slate-700'
                    : 'bg-red-950/20 border-red-900/40'
                }`}
              >
                <div className="text-xs font-mono font-bold text-slate-500 w-6 pt-1">
                  #{idx + 1}
                </div>

                <div className="w-24 h-14 rounded-lg bg-slate-800 overflow-hidden relative shrink-0">
                  {video.thumbnail_url ? (
                    <img
                      src={video.thumbnail_url}
                      alt={video.title}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-slate-600">
                      <Video className="w-6 h-6" />
                    </div>
                  )}
                  {video.duration_formatted && (
                    <span className="absolute bottom-1 right-1 px-1 py-0.2 bg-black/80 text-[10px] text-white rounded font-mono">
                      {video.duration_formatted}
                    </span>
                  )}
                </div>

                <div className="flex-1 min-w-0 space-y-1">
                  <h4 className="text-sm font-medium text-white truncate">
                    {video.title}
                  </h4>
                  <div className="flex items-center space-x-3 text-xs text-slate-400">
                    <span>{video.channel_title || 'Channel'}</span>
                    {video.is_available ? (
                      <span className="text-emerald-400 flex items-center space-x-1">
                        <CheckCircle2 className="w-3 h-3" />
                        <span>Ready</span>
                      </span>
                    ) : (
                      <span className="text-rose-400 flex items-center space-x-1">
                        <AlertTriangle className="w-3 h-3" />
                        <span>{video.status_note || 'Inaccessible'}</span>
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Generation Settings */}
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-6">
            <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
              <Settings className="w-4 h-4 text-brand-400" />
              <span>Generation Settings</span>
            </h3>

            {/* Note Detail Level */}
            <div className="space-y-2">
              <label className="text-xs font-medium text-slate-400">
                Technical Note Detail Level
              </label>
              <div className="grid grid-cols-3 gap-2">
                {(['concise', 'standard', 'comprehensive'] as NoteDetailLevel[]).map((lvl) => (
                  <button
                    key={lvl}
                    type="button"
                    onClick={() => setDetailLevel(lvl)}
                    className={`py-2 px-3 text-xs font-medium rounded-lg border capitalize transition-colors ${
                      detailLevel === lvl
                        ? 'bg-brand-600 text-white border-brand-500'
                        : 'bg-slate-950 text-slate-400 border-slate-800 hover:text-white'
                    }`}
                  >
                    {lvl}
                  </button>
                ))}
              </div>
            </div>

            {/* Language Preference */}
            <div className="space-y-2">
              <label className="text-xs font-medium text-slate-400">
                Transcript Language
              </label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full py-2.5 px-3 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-brand-500"
              >
                <option value="en">English (Default)</option>
                <option value="es">Spanish</option>
                <option value="de">German</option>
                <option value="fr">French</option>
                <option value="ja">Japanese</option>
              </select>
            </div>

            {/* Visuals Toggle */}
            <div className="space-y-2">
              <label className="text-xs font-medium text-slate-400">
                Visual Diagrams
              </label>
              <div
                onClick={() => setEnableVisuals(!enableVisuals)}
                className="flex items-center justify-between p-3 rounded-lg bg-slate-950 border border-slate-800 cursor-pointer hover:border-slate-700 transition-colors"
              >
                <div>
                  <div className="text-xs font-medium text-slate-200">
                    Generate Mermaid Diagrams
                  </div>
                  <div className="text-[11px] text-slate-500">
                    Architectural & sequence workflows
                  </div>
                </div>
                <div
                  className={`w-10 h-6 rounded-full transition-colors flex items-center p-0.5 ${
                    enableVisuals ? 'bg-brand-600 justify-end' : 'bg-slate-800 justify-start'
                  }`}
                >
                  <div className="w-5 h-5 rounded-full bg-white shadow" />
                </div>
              </div>
            </div>

            {/* PDF Theme */}
            <div className="space-y-2">
              <label className="text-xs font-medium text-slate-400">
                PDF Layout Palette
              </label>
              <div className="space-y-2">
                {[
                  { id: 'editorial_navy', name: 'Editorial Navy', desc: 'Deep navy & sky accent' },
                  { id: 'technical_slate', name: 'Technical Slate', desc: 'Minimal charcoal monochrome' },
                ].map((th) => (
                  <div
                    key={th.id}
                    onClick={() => setPdfTheme(th.id as PDFTheme)}
                    className={`p-2.5 rounded-lg border cursor-pointer text-xs transition-colors flex items-center justify-between ${
                      pdfTheme === th.id
                        ? 'border-brand-500 bg-brand-500/10 text-white'
                        : 'border-slate-800 bg-slate-950 text-slate-400 hover:text-white'
                    }`}
                  >
                    <div>
                      <div className="font-semibold text-slate-200">{th.name}</div>
                      <div className="text-[10px] text-slate-500">{th.desc}</div>
                    </div>
                    {pdfTheme === th.id && (
                      <CheckCircle2 className="w-4 h-4 text-brand-400 shrink-0" />
                    )}
                  </div>
                ))}
              </div>
            </div>

            <button
              onClick={handleStart}
              disabled={isStarting}
              className="w-full py-3.5 bg-brand-600 hover:bg-brand-500 text-white font-semibold text-sm rounded-xl transition-all shadow-lg shadow-brand-600/30 flex items-center justify-center space-x-2"
            >
              <Sparkles className="w-4 h-4 text-brand-200" />
              <span>Launch Pipeline</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
