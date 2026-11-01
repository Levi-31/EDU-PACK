import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { StructuredVideoNotes } from '../types';
import {
  Download,
  ExternalLink,
  BookOpen,
  Copy,
  ChevronLeft,
  ChevronRight,
  Clock,
  Play,
  Check,
  HelpCircle,
  FileText,
  RotateCcw
} from 'lucide-react';
import { getDownloadUrl, getJobNotes } from '../api/client';
import { MermaidDiagram } from './MermaidDiagram';

interface NotesViewerProps {
  jobId: string;
  notes: StructuredVideoNotes[];
  onBackToDashboard: () => void;
}

export const NotesViewer: React.FC<NotesViewerProps> = ({
  jobId,
  notes: initialNotes,
  onBackToDashboard,
}) => {
  const {
    data: fetchedNotes,
    isLoading: isFetchingNotes,
    refetch,
    isRefetching
  } = useQuery<StructuredVideoNotes[]>({
    queryKey: ['notes', jobId],
    queryFn: () => getJobNotes(jobId),
    initialData: initialNotes && initialNotes.length > 0 ? initialNotes : undefined,
    refetchOnMount: 'always',
    staleTime: 0,
  });

  const notes = (fetchedNotes && fetchedNotes.length > 0) ? fetchedNotes : (initialNotes || []);

  const [selectedVideoId, setSelectedVideoId] = useState<string>(
    notes.length > 0 ? notes[0].video_id : ''
  );
  const [copiedCodeId, setCopiedCodeId] = useState<string | null>(null);
  const [markdownCopied, setMarkdownCopied] = useState(false);

  useEffect(() => {
    if (notes.length > 0 && (!selectedVideoId || !notes.some((n) => n.video_id === selectedVideoId))) {
      setSelectedVideoId(notes[0].video_id);
    }
  }, [notes, selectedVideoId]);

  const currentIndex = notes.findIndex((n) => n.video_id === selectedVideoId);
  const currentNote = notes[currentIndex >= 0 ? currentIndex : 0];
  const chapterVisual = currentNote?.visual || currentNote?.sections?.find((s) => s.visual)?.visual;

  const handleCopyCode = (code: string, id: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCodeId(id);
    setTimeout(() => setCopiedCodeId(null), 2000);
  };

  const handleExportMarkdown = () => {
    if (!currentNote) return;
    let md = `# ${currentNote.video_title}\n\n`;
    md += `## Executive Summary\n${currentNote.executive_summary}\n\n`;
    if (currentNote.comprehensive_theory_background) {
      md += `## Foundational Theory\n${currentNote.comprehensive_theory_background}\n\n`;
    }
    currentNote.sections.forEach((sec) => {
      md += `### ${sec.title}\n`;
      if (sec.from_video) md += `**From the Video:**\n${sec.from_video}\n\n`;
      if (sec.additional_theory) md += `**Supplementary Explanation:**\n${sec.additional_theory}\n\n`;
      if (sec.markdown_content && !sec.from_video && !sec.additional_theory) {
        md += `${sec.markdown_content}\n\n`;
      }
      if (sec.code_snippets) {
        sec.code_snippets.forEach((code) => {
          md += `\`\`\`${code.language || ''}\n${code.code}\n\`\`\`\n\n`;
        });
      }
    });
    navigator.clipboard.writeText(md);
    setMarkdownCopied(true);
    setTimeout(() => setMarkdownCopied(false), 2000);
  };

  if ((!notes || notes.length === 0) && isFetchingNotes) {
    return (
      <div className="max-w-2xl mx-auto py-16 text-center space-y-4">
        <RotateCcw className="w-8 h-8 text-primary animate-spin mx-auto" />
        <h3 className="text-lg font-semibold text-on-surface">Loading Verified Monograph Notes...</h3>
        <p className="text-sm text-on-surface-variant font-mono">
          Fetching synthesized chapters from curriculum database.
        </p>
      </div>
    );
  }

  if (!notes || notes.length === 0) {
    return (
      <div className="max-w-2xl mx-auto py-16 text-center space-y-4">
        <h3 className="text-lg font-semibold text-on-surface">No Notes Available</h3>
        <p className="text-sm text-on-surface-variant">
          No generated notes could be found for this job.
        </p>
        <div className="flex items-center justify-center gap-3">
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-primary-container text-on-primary-container rounded-xl text-xs font-medium shadow-sm hover:opacity-90 flex items-center gap-1.5"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Retry Loading Notes</span>
          </button>
          <button
            onClick={onBackToDashboard}
            className="px-4 py-2 bg-surface-container hover:bg-surface-container-high text-on-surface rounded-xl text-xs font-medium border border-outline-variant/30"
          >
            Return to Generator
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto py-4 space-y-6 linear-animate-entrance">
      {/* Top Header Actions */}
      <div className="flex items-center justify-between pb-3 border-b border-outline-variant/30 text-xs">
        <div className="flex items-center gap-2 text-on-surface-variant font-mono">
          <span
            onClick={onBackToDashboard}
            className="hover:text-on-surface cursor-pointer smooth-transition"
          >
            Study Notes
          </span>
          <span className="text-outline">&bull;</span>
          <span className="text-on-surface font-medium">
            Chapter {String(currentIndex + 1).padStart(2, '0')} of {String(notes.length).padStart(2, '0')}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => refetch()}
            disabled={isRefetching}
            title="Refresh chapters"
            className="px-2.5 py-1.5 rounded-lg bg-surface-container hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface flex items-center gap-1 smooth-transition border border-outline-variant/30 text-xs"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${isRefetching ? 'animate-spin text-primary' : ''}`} />
          </button>

          {currentNote?.video_url && (
            <a
              href={currentNote.video_url}
              target="_blank"
              rel="noopener noreferrer"
              className="px-3 py-1.5 rounded-lg bg-surface-container hover:bg-surface-container-high text-on-surface flex items-center gap-1.5 smooth-transition border border-outline-variant/30 text-xs"
            >
              <Play className="w-3 h-3 text-red-500" />
              <span>Watch Video</span>
            </a>
          )}

          <button
            onClick={handleExportMarkdown}
            className="px-3 py-1.5 rounded-lg bg-surface-container hover:bg-surface-container-high text-on-surface flex items-center gap-1.5 smooth-transition border border-outline-variant/30 text-xs"
            type="button"
          >
            <Copy className="w-3 h-3 text-tertiary" />
            <span>{markdownCopied ? 'Copied Markdown!' : 'Copy Markdown'}</span>
          </button>

          <a
            href={getDownloadUrl(jobId)}
            target="_blank"
            rel="noreferrer"
            className="px-4 py-1.5 rounded-lg bg-primary-container hover:bg-primary-container/90 text-on-primary-container font-semibold flex items-center gap-1.5 shadow-sm text-xs smooth-transition"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download PDF</span>
          </a>
        </div>
      </div>

      {/* 2-Column Balanced Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Sidebar: Chapters Index (3 cols) */}
        <aside className="lg:col-span-4 xl:col-span-3 sticky top-20 space-y-2">
          <div className="text-xs font-mono text-outline uppercase tracking-wider px-2 flex items-center justify-between">
            <span>Syllabus Index</span>
            <span className="text-primary font-semibold">{notes.length} Ch</span>
          </div>

          <nav className="space-y-1 max-h-[70vh] overflow-y-auto pr-1">
            {notes.map((n, idx) => {
              const isActive = n.video_id === selectedVideoId;
              return (
                <button
                  key={n.video_id}
                  onClick={() => setSelectedVideoId(n.video_id)}
                  className={`w-full text-left p-2.5 rounded-xl flex items-start gap-2.5 text-xs smooth-transition ${
                    isActive
                      ? 'bg-surface-container-high text-on-surface font-medium border border-outline-variant/40 shadow-sm'
                      : 'hover:bg-surface-container text-on-surface-variant hover:text-on-surface'
                  }`}
                >
                  <span className={`font-mono text-[11px] w-5 text-right shrink-0 pt-0.5 ${isActive ? 'text-primary font-bold' : 'text-outline'}`}>
                    {String(idx + 1).padStart(2, '0')}
                  </span>
                  <span className="line-clamp-2 leading-snug">
                    {n.video_title}
                  </span>
                </button>
              );
            })}
          </nav>
        </aside>

        {/* Right Reader: Editorial Technical Monograph (9 cols) */}
        <main className="lg:col-span-8 xl:col-span-9 space-y-8 min-w-0">
          {currentNote && (
            <div className="space-y-8">
              {/* Chapter Header */}
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-primary font-semibold uppercase tracking-wider px-2 py-0.5 rounded bg-primary-container/10 border border-primary/20">
                    Chapter {String(currentIndex + 1).padStart(2, '0')}
                  </span>
                  <span className="text-xs text-outline font-mono">
                    Verified Monograph
                  </span>
                </div>
                <h1 className="font-geist text-2xl sm:text-3xl text-on-surface font-semibold tracking-tight leading-snug">
                  {currentNote.video_title}
                </h1>
                <p className="text-xs text-on-surface-variant">
                  {currentNote.channel_name ? `Recorded by ${currentNote.channel_name}` : ''}
                </p>
              </div>

              {/* Executive Summary */}
              {currentNote.executive_summary && (
                <div className="p-5 rounded-2xl bg-surface-container-low border border-outline-variant/30 shadow-sm relative overflow-hidden space-y-2">
                  <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary-container"></div>
                  <div className="text-xs font-mono font-semibold text-primary uppercase tracking-wider">
                    Executive Summary
                  </div>
                  <p className="text-sm text-on-surface leading-relaxed">
                    {currentNote.executive_summary}
                  </p>
                </div>
              )}

              {/* Foundational Theory & Context */}
              {currentNote.comprehensive_theory_background && (
                <div className="space-y-2">
                  <h3 className="font-geist text-base font-semibold text-on-surface">
                    Foundational Theory & Mechanics
                  </h3>
                  <div className="text-sm text-on-surface-variant leading-relaxed whitespace-pre-line font-sans">
                    {currentNote.comprehensive_theory_background}
                  </div>
                </div>
              )}

              {/* Learning Objectives */}
              {currentNote.learning_objectives && currentNote.learning_objectives.length > 0 && (
                <div className="p-4 rounded-xl bg-surface-container-low border border-outline-variant/20 space-y-2">
                  <h4 className="text-xs font-mono text-primary uppercase tracking-wider font-semibold">
                    Core Learning Objectives
                  </h4>
                  <ul className="space-y-1.5 text-xs sm:text-sm text-on-surface-variant">
                    {currentNote.learning_objectives.map((obj, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-primary font-bold">✓</span>
                        <span>{obj}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Architecture & Flowchart Visual Diagram */}
              {chapterVisual && (chapterVisual.mermaid_code || chapterVisual.image_url) && (
                <div className="pt-2">
                  <MermaidDiagram
                    mermaidCode={chapterVisual.mermaid_code}
                    imageUrl={chapterVisual.image_url}
                    title={chapterVisual.title}
                    description={chapterVisual.description}
                    assetType={chapterVisual.asset_type}
                  />
                </div>
              )}

              {/* Technical Sections */}
              <div className="space-y-6 pt-2">
                {currentNote.sections.map((section, idx) => (
                  <div key={idx} className="space-y-3 p-5 rounded-2xl bg-surface-container-low border border-outline-variant/30 shadow-sm">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-outline-variant/20 pb-3">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs text-primary font-bold">
                          § {idx + 1}.0
                        </span>
                        <h3 className="font-geist text-base font-semibold text-on-surface">
                          {section.title}
                        </h3>
                      </div>

                      {section.timestamped_watch_url && (
                        <a
                          href={section.timestamped_watch_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-xs text-primary hover:underline flex items-center gap-1 font-mono shrink-0"
                        >
                          <Clock className="w-3.5 h-3.5" />
                          <span>
                            {section.timestamp_seconds !== undefined
                              ? `${Math.floor(section.timestamp_seconds / 60)}:${Math.floor(section.timestamp_seconds % 60).toString().padStart(2, '0')}`
                              : 'Watch'}
                          </span>
                        </a>
                      )}
                    </div>

                    {/* From the Video */}
                    {section.from_video && (
                      <div className="text-sm text-on-surface leading-relaxed whitespace-pre-line font-sans">
                        {section.from_video}
                      </div>
                    )}

                    {/* Supplementary Explanation */}
                    {section.additional_theory && (
                      <div className="text-sm text-on-surface-variant leading-relaxed whitespace-pre-line font-sans pt-1">
                        {section.additional_theory}
                      </div>
                    )}

                    {!section.from_video && !section.additional_theory && section.markdown_content && (
                      <div className="text-sm text-on-surface-variant leading-relaxed whitespace-pre-line font-sans">
                        {section.markdown_content}
                      </div>
                    )}

                    {/* Comparison Table */}
                    {section.comparison_table_markdown && (
                      <div className="p-3 bg-surface-container-lowest rounded-xl border border-outline-variant/30 text-xs overflow-x-auto">
                        <pre className="font-mono text-on-surface text-xs whitespace-pre-wrap leading-relaxed">
                          {section.comparison_table_markdown}
                        </pre>
                      </div>
                    )}

                    {/* Code Snippets */}
                    {section.code_snippets && section.code_snippets.map((snip, sIdx) => {
                      const snippetId = `code-${idx}-${sIdx}`;
                      const isCopied = copiedCodeId === snippetId;
                      return (
                        <div key={sIdx} className="space-y-1">
                          <div className="flex items-center justify-between text-[11px] font-mono text-outline px-1">
                            <span>{snip.language || 'code'} payload</span>
                            <button
                              type="button"
                              onClick={() => handleCopyCode(snip.code, snippetId)}
                              className="hover:text-on-surface flex items-center gap-1 smooth-transition"
                            >
                              <Copy className="w-3 h-3" />
                              <span>{isCopied ? 'Copied' : 'Copy'}</span>
                            </button>
                          </div>
                          <div className="bg-surface-container-lowest p-3 rounded-xl border border-outline-variant/30 font-mono text-xs text-primary overflow-x-auto leading-relaxed">
                            <code>{snip.code}</code>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ))}
              </div>

              {/* Active Recall Flashcards */}
              {currentNote.flashcards && currentNote.flashcards.length > 0 && (
                <div className="space-y-3 pt-4 border-t border-outline-variant/30">
                  <div className="flex items-center gap-2">
                    <HelpCircle className="w-4 h-4 text-primary" />
                    <h3 className="font-geist text-base font-semibold text-on-surface">
                      Active Recall Questions & Knowledge Review
                    </h3>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {currentNote.flashcards.map((card, i) => (
                      <div
                        key={i}
                        className="p-4 rounded-xl bg-surface-container-low border border-outline-variant/30 space-y-2 text-xs"
                      >
                        <div className="font-semibold text-on-surface flex items-start gap-1.5">
                          <span className="text-primary font-mono">Q:</span>
                          <span>{card.question}</span>
                        </div>
                        <div className="text-on-surface-variant pl-3 border-l border-primary/30 leading-relaxed">
                          {card.answer}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Next / Previous Navigation */}
              <nav className="flex items-center justify-between pt-6 border-t border-outline-variant/30">
                {currentIndex > 0 ? (
                  <button
                    onClick={() => setSelectedVideoId(notes[currentIndex - 1].video_id)}
                    className="flex items-center gap-2 text-xs text-on-surface-variant hover:text-on-surface font-medium smooth-transition"
                  >
                    <ChevronLeft className="w-4 h-4" />
                    <span>Previous Chapter</span>
                  </button>
                ) : (
                  <div></div>
                )}

                {currentIndex < notes.length - 1 && (
                  <button
                    onClick={() => setSelectedVideoId(notes[currentIndex + 1].video_id)}
                    className="flex items-center gap-2 text-xs text-primary hover:text-primary/80 font-medium smooth-transition ml-auto"
                  >
                    <span>Next Chapter</span>
                    <ChevronRight className="w-4 h-4" />
                  </button>
                )}
              </nav>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};
