import React, { useState, useMemo } from 'react';
import {
  Download,
  FileDown,
  Layers,
  Search,
  BookOpen,
  Image as ImageIcon,
  Terminal,
  Copy,
  Check,
  ExternalLink,
  ArrowLeft,
  Calendar,
  Sparkles,
  Eye
} from 'lucide-react';
import { marked } from 'marked';
import {
  ResearchJobDetailResponse,
  ResearchPlan,
  ResearchEvidenceItem,
  ResearchImageSpec
} from '../../types';
import {
  getResearchPdfUrl,
  getResearchImageUrl
} from '../../api/client';

interface ResearchResultsProps {
  job: ResearchJobDetailResponse;
  onBack: () => void;
}

export type ResultsTabType = 'preview' | 'plan' | 'evidence' | 'images' | 'logs';

const ImageCard: React.FC<{
  spec: ResearchImageSpec;
  idx: number;
  jobId: string;
}> = ({ spec, idx, jobId }) => {
  const [loadError, setLoadError] = useState(false);
  const cleanName = spec.filename || (spec.path || '').split('/').pop() || `image_${idx + 1}.png`;
  const imageUrl = getResearchImageUrl(jobId, cleanName);

  return (
    <div className="rounded-2xl bg-surface-container-low border border-outline-variant/30 overflow-hidden shadow-sm flex flex-col justify-between smooth-transition hover:border-outline-variant/60">
      <div className="relative aspect-video bg-white dark:bg-surface-container-lowest flex items-center justify-center overflow-hidden group">
        {!loadError ? (
          <img
            src={imageUrl}
            alt={spec.alt || spec.placeholder || 'Generated research visual'}
            className="w-full h-full object-contain p-3 group-hover:scale-[1.02] smooth-transition"
            onError={() => setLoadError(true)}
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center p-6 text-center bg-surface-container space-y-2">
            <ImageIcon className="w-8 h-8 text-primary/60" />
            <div className="text-xs font-semibold text-on-surface">Technical Visual</div>
            <div className="text-[11px] text-outline font-mono line-clamp-2">{spec.prompt}</div>
          </div>
        )}

        <div className="absolute inset-0 bg-surface-container/60 opacity-0 group-hover:opacity-100 flex items-center justify-center gap-2 smooth-transition backdrop-blur-xs">
          <a
            href={imageUrl}
            target="_blank"
            rel="noreferrer"
            className="p-2 px-3 rounded-xl bg-surface text-on-surface shadow-md flex items-center gap-1.5 text-xs font-medium hover:bg-surface-container-high smooth-transition"
          >
            <Eye className="w-3.5 h-3.5" />
            <span>Full Resolution (1200×675)</span>
          </a>
          <a
            href={imageUrl}
            download={cleanName}
            className="p-2 px-3 rounded-xl bg-primary text-on-primary shadow-md flex items-center gap-1.5 text-xs font-medium hover:bg-primary/90 smooth-transition"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Save Image</span>
          </a>
        </div>
      </div>

      <div className="p-4 space-y-2">
        <div className="flex items-center justify-between">
          <span className="px-2 py-0.5 rounded bg-primary/10 text-primary text-[10px] font-mono font-semibold uppercase">
            {spec.kind || 'Figure'} {idx + 1}
          </span>
          <span className="text-[10px] font-mono text-outline">
            1200 × 675 (16:9)
          </span>
        </div>

        {spec.caption && (
          <div className="text-xs font-medium text-on-surface">
            {spec.caption}
          </div>
        )}

        <p className="text-xs text-on-surface-variant leading-relaxed line-clamp-3">
          <span className="font-semibold text-on-surface">Prompt: </span>
          {spec.prompt}
        </p>

        {cleanName && (
          <div className="text-[10px] font-mono text-outline truncate">
            File: images/{cleanName}
          </div>
        )}
      </div>
    </div>
  );
};

export const ResearchResults: React.FC<ResearchResultsProps> = ({ job, onBack }) => {
  const [activeTab, setActiveTab] = useState<ResultsTabType>('preview');
  const [copiedMd, setCopiedMd] = useState(false);

  const handleCopyMarkdown = () => {
    if (job.markdown_content) {
      navigator.clipboard.writeText(job.markdown_content);
      setCopiedMd(true);
      setTimeout(() => setCopiedMd(false), 2000);
    }
  };

  // Filter image specs to only those that were ACTUALLY generated on the backend
  const availableSpecs = useMemo(() => {
    if (!job.image_specs || !job.images) return [];
    return job.image_specs.filter((spec, idx) => {
      const cleanName = spec.filename || (spec.path || '').split('/').pop() || `image_${idx + 1}.png`;
      return job.images && job.images.includes(cleanName);
    });
  }, [job.image_specs, job.images]);

  // Convert relative image URLs and placeholders in markdown to full API URLs
  const renderedHtml = useMemo(() => {
    if (!job.markdown_content) return '<p class="text-outline italic">No content generated.</p>';

    let processedMd = job.markdown_content;

    // Resolve any remaining placeholders [[IMAGE_1]] only if the image was actually generated
    if (job.image_specs && job.image_specs.length > 0) {
      job.image_specs.forEach((spec, idx) => {
        const cleanName = spec.filename || (spec.path || '').split('/').pop() || `image_${idx + 1}.png`;
        const fullUrl = getResearchImageUrl(job.id, cleanName);
        if (spec.placeholder && processedMd.includes(spec.placeholder)) {
          if (job.images && job.images.includes(cleanName)) {
            processedMd = processedMd.split(spec.placeholder).join(
              `\n\n![${spec.alt || spec.caption || 'Research Visual'}](${fullUrl})\n*${spec.caption || ''}*\n\n`
            );
          } else {
            // No image was generated: skip and remove placeholder cleanly!
            processedMd = processedMd.split(spec.placeholder).join('');
          }
        }
      });
    }

    // Replace markdown image syntax ![alt](images/filename.png) or ![alt](./images/filename.png)
    // If the image was not generated on disk, skip it entirely!
    processedMd = processedMd.replace(
      /!\[([^\]]*)\]\((?:(?:images|\.\/images)\/)?([^)]+)\)/g,
      (match, alt, filename) => {
        if (filename.startsWith('http://') || filename.startsWith('https://') || filename.startsWith('data:')) {
          return match;
        }
        const cleanName = filename.split('/').pop() || filename;
        if (job.images && !job.images.includes(cleanName)) {
          return ''; // Skip non-existent image!
        }
        const fullUrl = getResearchImageUrl(job.id, cleanName);
        return `![${alt}](${fullUrl})`;
      }
    );

    // Replace HTML image tags <img src="images/filename.png" ... />
    processedMd = processedMd.replace(
      /<img\s+([^>]*?)src=["'](?:(?:images|\.\/images)\/)?([^"']+)["']([^>]*?)>/gi,
      (match, pre, filename, post) => {
        if (filename.startsWith('http://') || filename.startsWith('https://') || filename.startsWith('data:')) {
          return match;
        }
        const cleanName = filename.split('/').pop() || filename;
        if (job.images && !job.images.includes(cleanName)) {
          return ''; // Skip non-existent image!
        }
        const fullUrl = getResearchImageUrl(job.id, cleanName);
        return `<img ${pre}src="${fullUrl}"${post}>`;
      }
    );

    try {
      return marked.parse(processedMd) as string;
    } catch (e) {
      return `<pre class="text-xs p-4 overflow-auto">${job.markdown_content}</pre>`;
    }
  }, [job.markdown_content, job.id, job.image_specs, job.images]);

  return (
    <div className="max-w-6xl mx-auto py-6 space-y-6 linear-animate-entrance">
      {/* Top Bar Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-outline-variant/30">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-2 rounded-xl bg-surface-container hover:bg-surface-high text-on-surface-variant hover:text-on-surface border border-outline-variant/30 smooth-transition shrink-0"
            title="Return to Research"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div className="min-w-0">
            <h1 className="text-xl sm:text-2xl font-geist font-semibold text-on-surface tracking-tight truncate">
              {job.article_title || job.topic}
            </h1>
          </div>
        </div>

        {/* Action Buttons: Only Copy & Download PDF */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={handleCopyMarkdown}
            className="px-3.5 py-1.5 bg-surface-container hover:bg-surface-high text-on-surface rounded-xl text-xs font-medium border border-outline-variant/30 flex items-center gap-1.5 smooth-transition"
            title="Copy Raw Markdown"
          >
            {copiedMd ? <Check className="w-3.5 h-3.5 text-tertiary" /> : <Copy className="w-3.5 h-3.5 text-outline" />}
            <span>{copiedMd ? 'Copied' : 'Copy'}</span>
          </button>

          <a
            href={getResearchPdfUrl(job.id)}
            download
            className="px-4 py-1.5 bg-primary hover:bg-primary/90 text-on-primary rounded-xl text-xs font-semibold shadow-xs flex items-center gap-1.5 smooth-transition"
            title="Download Publication-Grade PDF"
          >
            <FileDown className="w-3.5 h-3.5" />
            <span>Download PDF</span>
          </a>
        </div>
      </div>

      {/* Clean Minimalist Tabs: [ Article ]  [ Sources ]  [ Images ]  [ Plan ]  [ Activity ] */}
      <div className="flex items-center gap-1 p-1 bg-surface-container rounded-xl border border-outline-variant/30 overflow-x-auto text-xs w-fit">
        <button
          onClick={() => setActiveTab('preview')}
          className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg font-medium smooth-transition whitespace-nowrap ${
            activeTab === 'preview'
              ? 'bg-surface text-on-surface font-semibold shadow-xs'
              : 'text-on-surface-variant hover:text-on-surface'
          }`}
        >
          <BookOpen className="w-3.5 h-3.5 text-primary" />
          <span>Article</span>
        </button>

        <button
          onClick={() => setActiveTab('evidence')}
          className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg font-medium smooth-transition whitespace-nowrap ${
            activeTab === 'evidence'
              ? 'bg-surface text-on-surface font-semibold shadow-xs'
              : 'text-on-surface-variant hover:text-on-surface'
          }`}
        >
          <Search className="w-3.5 h-3.5 text-outline" />
          <span>Sources</span>
        </button>

        <button
          onClick={() => setActiveTab('images')}
          className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg font-medium smooth-transition whitespace-nowrap ${
            activeTab === 'images'
              ? 'bg-surface text-on-surface font-semibold shadow-xs'
              : 'text-on-surface-variant hover:text-on-surface'
          }`}
        >
          <ImageIcon className="w-3.5 h-3.5 text-outline" />
          <span>Images</span>
        </button>

        <button
          onClick={() => setActiveTab('plan')}
          className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg font-medium smooth-transition whitespace-nowrap ${
            activeTab === 'plan'
              ? 'bg-surface text-on-surface font-semibold shadow-xs'
              : 'text-on-surface-variant hover:text-on-surface'
          }`}
        >
          <Layers className="w-3.5 h-3.5 text-outline" />
          <span>Plan</span>
        </button>

        <button
          onClick={() => setActiveTab('logs')}
          className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg font-medium smooth-transition whitespace-nowrap ${
            activeTab === 'logs'
              ? 'bg-surface text-on-surface font-semibold shadow-xs'
              : 'text-on-surface-variant hover:text-on-surface'
          }`}
        >
          <Terminal className="w-3.5 h-3.5 text-outline" />
          <span>Activity</span>
        </button>
      </div>

      {/* Tab 1: Markdown Preview */}
      {activeTab === 'preview' && (
        <div className="bg-surface-container-low/70 border border-outline-variant/30 rounded-2xl p-6 sm:p-10 shadow-sm">
          <div
            className="markdown-article max-w-none"
            dangerouslySetInnerHTML={{ __html: renderedHtml }}
          />
        </div>
      )}

      {/* Tab 2: Content Plan */}
      {activeTab === 'plan' && (
        <div className="space-y-4">
          <div className="p-5 rounded-2xl bg-surface-container-low border border-outline-variant/30 space-y-3">
            <h3 className="font-geist text-lg font-semibold text-on-surface">
              {job.plan?.title || 'Planned Content Structure'}
            </h3>
            {job.plan?.description && (
              <p className="text-xs sm:text-sm text-on-surface-variant leading-relaxed">
                {job.plan.description}
              </p>
            )}
          </div>

          <div className="space-y-3">
            {job.plan?.tasks && job.plan.tasks.length > 0 ? (
              job.plan.tasks.map((task, idx) => (
                <div
                  key={task.id || idx}
                  className="p-4 rounded-xl bg-surface-container-low/70 border border-outline-variant/20 space-y-1.5"
                >
                  <div className="flex items-center gap-2">
                    <span className="w-5 h-5 rounded-md bg-secondary/10 text-secondary text-[10px] font-mono font-semibold flex items-center justify-center">
                      {idx + 1}
                    </span>
                    <h4 className="font-geist text-sm font-semibold text-on-surface">
                      {task.title}
                    </h4>
                  </div>
                  <p className="text-xs text-on-surface-variant leading-relaxed pl-7">
                    {task.description}
                  </p>
                </div>
              ))
            ) : (
              <div className="p-8 text-center text-xs text-outline italic bg-surface-container-low/40 rounded-xl">
                No structured content plan available for this run.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 3: Evidence Sources */}
      {activeTab === 'evidence' && (
        <div className="space-y-4">
          <div className="text-xs font-mono text-outline uppercase tracking-wider px-1">
            Retrieved Research Evidence ({job.evidence_items?.length || 0} Citations)
          </div>

          {job.evidence_items && job.evidence_items.length > 0 ? (
            <div className="space-y-3">
              {job.evidence_items.map((item, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-xl bg-surface-container-low/80 border border-outline-variant/20 hover:border-outline-variant/50 space-y-2 smooth-transition"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <a
                        href={item.url}
                        target="_blank"
                        rel="noreferrer"
                        className="font-geist text-sm font-semibold text-primary hover:underline flex items-center gap-1.5"
                      >
                        <span className="truncate">{item.title || item.url}</span>
                        <ExternalLink className="w-3.5 h-3.5 shrink-0" />
                      </a>
                      <span className="text-[11px] font-mono text-outline block mt-0.5 truncate">
                        {item.url}
                      </span>
                    </div>

                    {item.score !== undefined && (
                      <span className="px-2 py-0.5 rounded bg-surface-container text-[10px] font-mono text-outline shrink-0">
                        Score: {typeof item.score === 'number' ? item.score.toFixed(2) : item.score}
                      </span>
                    )}
                  </div>

                  <p className="text-xs text-on-surface-variant leading-relaxed bg-surface-container-lowest/50 p-2.5 rounded-lg border border-outline-variant/10">
                    {item.snippet}
                  </p>

                  <div className="flex items-center gap-4 text-[11px] font-mono text-outline">
                    {item.query && <span>Query: "{item.query}"</span>}
                    {item.published_date && <span>Published: {item.published_date}</span>}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 text-center text-xs text-outline italic bg-surface-container-low/40 rounded-xl">
              {job.mode === 'closed_book'
                ? 'Closed-book topic — no external search queries were required.'
                : 'No external evidence items recorded.'}
            </div>
          )}
        </div>
      )}

      {/* Tab 4: Generated Images */}
      {activeTab === 'images' && (
        <div className="space-y-4">
          <div className="text-xs font-mono text-outline uppercase tracking-wider px-1">
            Visual Asset Gallery ({availableSpecs.length} Assets)
          </div>

          {availableSpecs.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {availableSpecs.map((spec, idx) => (
                <ImageCard
                  key={spec.placeholder || idx}
                  spec={spec}
                  idx={idx}
                  jobId={job.id}
                />
              ))}
            </div>
          ) : (
            <div className="p-8 text-center text-xs text-outline italic bg-surface-container-low/40 rounded-xl">
              No visual assets generated for this run.
            </div>
          )}
        </div>
      )}

      {/* Tab 5: Execution Logs */}
      {activeTab === 'logs' && (
        <div className="rounded-2xl bg-surface-container-lowest border border-outline-variant/30 overflow-hidden shadow-inner">
          <div className="px-4 py-2.5 bg-surface-container-high/60 border-b border-outline-variant/20 flex items-center justify-between text-xs font-mono text-outline">
            <div className="flex items-center gap-2">
              <Terminal className="w-3.5 h-3.5 text-primary" />
              <span>Agent Graph Execution Trace</span>
            </div>
            <span>{(job.logs || []).length} Events</span>
          </div>

          <div className="p-4 max-h-[600px] overflow-y-auto space-y-1 font-mono text-xs leading-relaxed text-on-surface-variant">
            {job.logs && job.logs.length > 0 ? (
              job.logs.map((logMsg, i) => (
                <div key={i} className="flex items-start gap-2">
                  <span className="text-outline select-none text-[11px] shrink-0">›</span>
                  <span className="break-all">{logMsg}</span>
                </div>
              ))
            ) : (
              <div className="text-outline italic">No execution logs recorded.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
