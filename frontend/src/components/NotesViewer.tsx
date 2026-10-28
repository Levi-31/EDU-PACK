import React, { useState } from 'react';
import { StructuredVideoNotes } from '../types';
import {
  Download,
  ExternalLink,
  Clock,
  BookOpen,
  Code2,
  CheckCircle,
  HelpCircle,
  Layers,
  Sparkles,
  Info,
  AlertTriangle,
  GraduationCap,
  BookmarkCheck,
  Compass
} from 'lucide-react';
import { getDownloadUrl } from '../api/client';

interface NotesViewerProps {
  jobId: string;
  notes: StructuredVideoNotes[];
  onBackToDashboard: () => void;
}

export const NotesViewer: React.FC<NotesViewerProps> = ({
  jobId,
  notes,
  onBackToDashboard,
}) => {
  const [selectedVideoId, setSelectedVideoId] = useState<string>(
    notes.length > 0 ? notes[0].video_id : ''
  );

  const currentNote = notes.find((n) => n.video_id === selectedVideoId) || notes[0];

  if (!notes || notes.length === 0) {
    return (
      <div className="max-w-4xl mx-auto py-16 text-center space-y-4">
        <h3 className="text-xl font-bold text-white">No Notes Available</h3>
        <p className="text-sm text-slate-400">
          The processing pipeline has not completed or no video notes could be retrieved.
        </p>
        <button
          onClick={onBackToDashboard}
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-sm"
        >
          Return to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto py-4 space-y-6">
      {/* Top Action Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 sm:p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-xl">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-brand-500/10 text-brand-400 border border-brand-500/20">
              Technical Syllabus & Notes
            </span>
            {currentNote?.is_mock && (
              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                Demo Generated
              </span>
            )}
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            Generated Technical Notes & Diagrams
          </h2>
          <p className="text-xs sm:text-sm text-slate-400">
            {notes.length} chapters synthesized in original playlist sequence
          </p>
        </div>

        <div className="flex items-center space-x-3 shrink-0">
          <button
            onClick={onBackToDashboard}
            className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors"
          >
            Dashboard
          </button>
          <a
            href={getDownloadUrl(jobId)}
            target="_blank"
            rel="noreferrer"
            className="px-5 py-2.5 bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs rounded-xl flex items-center space-x-2 transition-all shadow-lg shadow-brand-600/30"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download High-Fidelity PDF</span>
          </a>
        </div>
      </div>

      {/* Main Reader View */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start">
        {/* Navigation Sidebar */}
        <div className="lg:col-span-1 bg-slate-900 border border-slate-800 rounded-2xl p-4 space-y-2 sticky top-24 max-h-[80vh] overflow-y-auto">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider px-2 mb-3">
            Video Chapters ({notes.length})
          </h3>
          <div className="space-y-1.5">
            {notes.map((n, idx) => (
              <button
                key={n.video_id}
                onClick={() => setSelectedVideoId(n.video_id)}
                className={`w-full text-left p-2.5 rounded-xl text-xs font-medium transition-all flex items-start space-x-2.5 ${
                  selectedVideoId === n.video_id
                    ? 'bg-brand-600/15 text-brand-300 border border-brand-500/30 font-semibold'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60 border border-transparent'
                }`}
              >
                <span className="font-mono text-slate-500 pt-0.5">#{idx + 1}</span>
                <span className="line-clamp-2 leading-relaxed">{n.video_title}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Note Reader Body */}
        <div className="lg:col-span-3 space-y-6">
          {currentNote && (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-8 shadow-xl">
              {/* Chapter Header */}
              <div className="border-b border-slate-800 pb-6 space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="text-xs font-bold text-brand-400 uppercase tracking-wider">
                    Chapter {currentNote.original_position + 1}
                  </span>
                  <a
                    href={currentNote.video_url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-red-600/15 hover:bg-red-600/25 border border-red-500/30 text-red-400 text-xs font-medium transition-colors"
                  >
                    <span>Watch Original on YouTube</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>

                <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight leading-snug">
                  {currentNote.video_title}
                </h1>

                <div className="flex items-center space-x-4 text-xs text-slate-400 pt-1">
                  <span>Instructor: {currentNote.channel_name || 'YouTube Creator'}</span>
                  {currentNote.duration_seconds && (
                    <span className="flex items-center space-x-1">
                      <Clock className="w-3.5 h-3.5 text-slate-500" />
                      <span>{Math.floor(currentNote.duration_seconds / 60)}m</span>
                    </span>
                  )}
                </div>
              </div>

              {/* Executive Summary */}
              <div className="p-4 rounded-xl bg-slate-950 border-l-4 border-brand-500 border-y border-r border-slate-800/80 space-y-1">
                <div className="text-[11px] font-bold uppercase tracking-wider text-brand-400">
                  Executive Summary
                </div>
                <p className="text-sm text-slate-200 leading-relaxed">
                  {currentNote.executive_summary}
                </p>
              </div>

              {/* Foundational Theory & Architectural Context */}
              {currentNote.comprehensive_theory_background && (
                <div className="p-4 rounded-xl bg-purple-950/20 border-l-4 border-purple-500 border-y border-r border-purple-900/40 space-y-2">
                  <div className="text-xs font-bold uppercase tracking-wider text-purple-400 flex items-center space-x-1.5">
                    <GraduationCap className="w-4 h-4" />
                    <span>Foundational Theory & Architectural Context</span>
                  </div>
                  <p className="text-xs sm:text-sm text-purple-200/90 leading-relaxed whitespace-pre-line">
                    {currentNote.comprehensive_theory_background}
                  </p>
                </div>
              )}

              {/* Key Takeaways */}
              {currentNote.key_takeaways && currentNote.key_takeaways.length > 0 && (
                <div className="space-y-3">
                  <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-emerald-400" />
                    <span>Key Takeaways</span>
                  </h3>
                  <ul className="space-y-2">
                    {currentNote.key_takeaways.map((takeaway, i) => (
                      <li key={i} className="text-xs sm:text-sm text-slate-300 flex items-start space-x-2">
                        <span className="text-brand-400 mt-1">&bull;</span>
                        <span>{takeaway}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Learning Objectives & Prerequisites */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {currentNote.learning_objectives && currentNote.learning_objectives.length > 0 && (
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                    <div className="text-xs font-semibold text-sky-400 uppercase tracking-wider">
                      Learning Objectives
                    </div>
                    <ul className="space-y-1.5 text-xs text-slate-300">
                      {currentNote.learning_objectives.map((obj, i) => (
                        <li key={i} className="flex items-start space-x-1.5">
                          <span className="text-sky-400">&check;</span>
                          <span>{obj}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {currentNote.prerequisites && currentNote.prerequisites.length > 0 && (
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                    <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Prerequisites
                    </div>
                    <ul className="space-y-1.5 text-xs text-slate-400">
                      {currentNote.prerequisites.map((p, i) => (
                        <li key={i} className="flex items-start space-x-1.5">
                          <span>&bull;</span>
                          <span>{p}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Detailed Sections with Timestamped Watch Links & Demarcation */}
              <div className="space-y-6 pt-2">
                <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
                  <BookOpen className="w-4 h-4 text-brand-400" />
                  <span>Technical Explanations & Modules</span>
                </h3>

                <div className="space-y-6">
                  {currentNote.sections.map((section, idx) => (
                    <div
                      key={idx}
                      className="bg-slate-950/70 border border-slate-800 rounded-xl p-5 space-y-4"
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/60 pb-3">
                        <h4 className="text-base font-bold text-white">
                          {section.title}
                        </h4>
                        {section.timestamped_watch_url && (
                          <a
                            href={section.timestamped_watch_url}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded bg-brand-500/10 hover:bg-brand-500/20 text-brand-400 text-xs font-medium transition-colors shrink-0"
                          >
                            <Clock className="w-3.5 h-3.5" />
                            <span>
                              Watch @ {section.timestamp_seconds !== undefined
                                ? `${Math.floor(section.timestamp_seconds / 60)}:${Math.floor(section.timestamp_seconds % 60).toString().padStart(2, '0')}`
                                : 'Video'}
                            </span>
                          </a>
                        )}
                      </div>

                      {/* Grounded From-the-Video Section */}
                      {section.from_video && (
                        <div className="p-3.5 rounded-lg bg-sky-950/20 border border-sky-800/40 text-xs space-y-1.5">
                          <span className="inline-block px-2 py-0.5 rounded bg-sky-600/30 text-sky-300 font-bold text-[10px] uppercase tracking-wider">
                            From the Video (Transcript Grounded)
                          </span>
                          <p className="text-slate-300 leading-relaxed whitespace-pre-line">
                            {section.from_video}
                          </p>
                        </div>
                      )}

                      {/* Additional Foundational Theory */}
                      {section.additional_theory && (
                        <div className="p-3.5 rounded-lg bg-purple-950/20 border border-purple-800/40 text-xs space-y-1.5">
                          <span className="inline-block px-2 py-0.5 rounded bg-purple-600/30 text-purple-300 font-bold text-[10px] uppercase tracking-wider">
                            Additional Theory & Mechanics
                          </span>
                          <p className="text-purple-200/90 leading-relaxed whitespace-pre-line">
                            {section.additional_theory}
                          </p>
                        </div>
                      )}

                      {/* General Content Fallback */}
                      {!section.from_video && !section.additional_theory && (
                        <div className="text-xs sm:text-sm text-slate-300 leading-relaxed whitespace-pre-line">
                          {section.markdown_content}
                        </div>
                      )}

                      {/* Comparison Table */}
                      {section.comparison_table_markdown && (
                        <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 text-xs overflow-x-auto">
                          <span className="font-semibold text-slate-300 block mb-1 text-[11px] uppercase tracking-wider">
                            Technical Comparison
                          </span>
                          <pre className="font-mono text-slate-300 text-[11px] whitespace-pre-wrap">
                            {section.comparison_table_markdown}
                          </pre>
                        </div>
                      )}

                      {/* Code Snippets */}
                      {section.code_snippets && section.code_snippets.map((snip, sIdx) => (
                        <div key={sIdx} className="space-y-1">
                          <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden">
                            <div className="bg-slate-900 px-4 py-1.5 border-b border-slate-800 flex justify-between items-center text-xs text-slate-400 font-mono">
                              <span>{snip.language || 'code'}</span>
                            </div>
                            <pre className="p-4 text-xs font-mono text-emerald-300 overflow-x-auto leading-relaxed">
                              <code>{snip.code}</code>
                            </pre>
                          </div>
                          {snip.caption && (
                            <p className="text-[11px] text-slate-500 italic px-1">
                              Snippet: {snip.caption}
                            </p>
                          )}
                        </div>
                      ))}

                      {/* Callouts */}
                      {section.callouts && section.callouts.map((c, cIdx) => (
                        <div
                          key={cIdx}
                          className={`p-3.5 rounded-lg border text-xs space-y-1 ${
                            c.kind === 'important' || c.kind === 'warning'
                              ? 'bg-amber-950/20 border-amber-800/40 text-amber-300'
                              : 'bg-sky-950/20 border-sky-800/40 text-sky-300'
                          }`}
                        >
                          <div className="font-bold flex items-center space-x-1.5">
                            <Info className="w-3.5 h-3.5" />
                            <span>{c.title}</span>
                          </div>
                          <p className="text-slate-300 leading-relaxed">{c.content}</p>
                        </div>
                      ))}

                      {/* Section References / Citations */}
                      {section.cited_sources && section.cited_sources.length > 0 && (
                        <div className="pt-2 flex flex-wrap gap-1.5 items-center">
                          <span className="text-[10px] text-slate-500 font-semibold uppercase">References:</span>
                          {section.cited_sources.map((src, rIdx) => (
                            <a
                              key={rIdx}
                              href={src.url}
                              target="_blank"
                              rel="noreferrer"
                              className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px] transition-colors border border-slate-700"
                            >
                              <span>{src.title}</span>
                              <ExternalLink className="w-2.5 h-2.5 text-slate-400" />
                            </a>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Architecture & Trade-offs */}
              {(currentNote.architecture_and_workflows || (currentNote.trade_offs_and_decisions && currentNote.trade_offs_and_decisions.length > 0)) && (
                <div className="space-y-4 pt-2">
                  <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
                    <Layers className="w-4 h-4 text-brand-400" />
                    <span>Architecture & Design Decisions</span>
                  </h3>

                  {currentNote.architecture_and_workflows && (
                    <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-xs sm:text-sm text-slate-300 leading-relaxed">
                      <div className="font-semibold text-slate-200 mb-1">Architecture Overview:</div>
                      {currentNote.architecture_and_workflows}
                    </div>
                  )}

                  {currentNote.trade_offs_and_decisions && (
                    <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                      <div className="text-xs font-semibold text-amber-400 uppercase tracking-wider">
                        Key Trade-offs
                      </div>
                      <ul className="space-y-1.5 text-xs text-slate-300">
                        {currentNote.trade_offs_and_decisions.map((to, i) => (
                          <li key={i} className="flex items-start space-x-1.5">
                            <span className="text-amber-400">&bull;</span>
                            <span>{to}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Common Misconceptions */}
              {currentNote.common_misconceptions && currentNote.common_misconceptions.length > 0 && (
                <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-800/40 space-y-2">
                  <div className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center space-x-1.5">
                    <AlertTriangle className="w-4 h-4" />
                    <span>Common Misconceptions & Clarifications</span>
                  </div>
                  <ul className="space-y-1.5 text-xs text-amber-200/90">
                    {currentNote.common_misconceptions.map((misc, i) => (
                      <li key={i} className="flex items-start space-x-1.5">
                        <span className="text-amber-400 font-bold">&bull;</span>
                        <span>{misc}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Flashcards & Active Recall */}
              {currentNote.flashcards && currentNote.flashcards.length > 0 && (
                <div className="space-y-3 pt-2">
                  <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
                    <HelpCircle className="w-4 h-4 text-teal-400" />
                    <span>Active Recall & Flashcards</span>
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {currentNote.flashcards.map((card, i) => (
                      <div key={i} className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                        <div className="text-xs font-bold text-white flex items-start space-x-1.5">
                          <span className="text-teal-400 font-mono">Q:</span>
                          <span>{card.question}</span>
                        </div>
                        <div className="text-xs text-slate-400 pl-4 border-l border-teal-500/30">
                          {card.answer}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Chapter-Wide Reference Sources */}
              {currentNote.all_sources && currentNote.all_sources.length > 0 && (
                <div className="pt-4 border-t border-slate-800 space-y-2">
                  <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
                    <BookmarkCheck className="w-3.5 h-3.5 text-sky-400" />
                    <span>Authoritative External Sources & RFCs</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {currentNote.all_sources.map((src, i) => (
                      <a
                        key={i}
                        href={src.url}
                        target="_blank"
                        rel="noreferrer"
                        className="p-2.5 rounded-lg bg-slate-950 hover:bg-slate-800/80 border border-slate-800 text-xs transition-colors flex items-start justify-between gap-2"
                      >
                        <div>
                          <div className="font-semibold text-slate-200 line-clamp-1">{src.title}</div>
                          <div className="text-[10px] text-slate-500 line-clamp-1">{src.domain || src.url}</div>
                        </div>
                        <ExternalLink className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
