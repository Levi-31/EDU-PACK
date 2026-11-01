import React, { useEffect, useState, useId } from 'react';
import mermaid from 'mermaid';
import { Copy, Check, ZoomIn, Image as ImageIcon, GitFork } from 'lucide-react';

interface MermaidDiagramProps {
  mermaidCode?: string;
  imageUrl?: string;
  title?: string;
  description?: string;
  assetType?: string;
}

export const MermaidDiagram: React.FC<MermaidDiagramProps> = ({
  mermaidCode,
  imageUrl,
  title,
  description,
  assetType
}) => {
  const [svgHtml, setSvgHtml] = useState<string>('');
  const [hasError, setHasError] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);
  const [isZoomed, setIsZoomed] = useState<boolean>(false);
  const rawId = useId();
  const diagramId = `mermaid_${rawId.replace(/[^a-zA-Z0-9_-]/g, '_')}`;

  useEffect(() => {
    let isMounted = true;
    if (!mermaidCode || !mermaidCode.trim()) {
      return;
    }

    const renderDiagram = async () => {
      try {
        const isDark = document.documentElement.classList.contains('dark');
        mermaid.initialize({
          startOnLoad: false,
          securityLevel: 'loose',
          theme: isDark ? 'dark' : 'default',
          themeVariables: isDark
            ? {
                primaryColor: '#1e293b',
                primaryTextColor: '#f1f5f9',
                primaryBorderColor: '#475569',
                lineColor: '#94a3b8',
                secondaryColor: '#0f172a',
                tertiaryColor: '#1e293b',
                fontFamily: 'Inter, sans-serif',
                fontSize: '11px',
              }
            : {
                primaryColor: '#f8fafc',
                primaryTextColor: '#1e293b',
                primaryBorderColor: '#cbd5e1',
                lineColor: '#64748b',
                secondaryColor: '#f1f5f9',
                tertiaryColor: '#ffffff',
                fontFamily: 'Inter, sans-serif',
                fontSize: '11px',
              },
        });

        // Clean and sanitize DSL
        let code = mermaidCode.trim();
        code = code.replace(/^```[a-z]*\s*/i, '').replace(/\s*```$/i, '').trim();
        code = code.replace(/-->>/g, '-->');
        code = code.replace(/(?<![-=.])->(?!>)/g, '-->');
        code = code.replace(/;\s*$/gm, '');

        const { svg } = await mermaid.render(diagramId, code);
        if (isMounted) {
          setSvgHtml(svg);
          setHasError(false);
        }
      } catch (err) {
        console.warn('Failed to render Mermaid diagram in UI:', err);
        if (isMounted) {
          setHasError(true);
        }
      }
    };

    renderDiagram();
    return () => {
      isMounted = false;
    };
  }, [mermaidCode, diagramId]);

  const handleCopyCode = () => {
    if (!mermaidCode) return;
    navigator.clipboard.writeText(mermaidCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!mermaidCode && !imageUrl) {
    return null;
  }

  return (
    <div className="rounded-2xl border border-outline-variant/40 bg-surface-container-low p-5 space-y-4 shadow-sm overflow-hidden transition-all duration-200 hover:border-outline-variant/70">
      {/* Header bar */}
      <div className="flex items-center justify-between gap-3 border-b border-outline-variant/20 pb-3">
        <div className="flex items-center gap-2">
          {imageUrl && !mermaidCode ? (
            <span className="p-1.5 rounded-lg bg-secondary-container/20 text-secondary">
              <ImageIcon className="w-4 h-4 text-primary" />
            </span>
          ) : (
            <span className="p-1.5 rounded-lg bg-primary-container/20 text-primary">
              <GitFork className="w-4 h-4 text-primary" />
            </span>
          )}
          <div>
            <div className="text-[10px] font-mono uppercase tracking-wider text-primary font-semibold">
              {imageUrl && !mermaidCode
                ? 'Technical Visual Illustration'
                : 'Architecture & Workflow Flowchart'}
            </div>
            {title && (
              <h4 className="font-geist text-sm sm:text-base font-semibold text-on-surface">
                {title}
              </h4>
            )}
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          {mermaidCode && (
            <button
              type="button"
              onClick={handleCopyCode}
              title="Copy Mermaid DSL"
              className="px-2 py-1 rounded-lg border border-outline-variant/30 text-[11px] font-mono text-on-surface-variant hover:text-on-surface hover:bg-surface-container flex items-center gap-1 transition-colors"
            >
              {copied ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
              <span>{copied ? 'Copied' : 'Mermaid'}</span>
            </button>
          )}
          <button
            type="button"
            onClick={() => setIsZoomed(!isZoomed)}
            title={isZoomed ? 'Reset zoom' : 'Expand diagram'}
            className="p-1.5 rounded-lg border border-outline-variant/30 text-on-surface-variant hover:text-on-surface hover:bg-surface-container transition-colors"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Render Canvas */}
      {imageUrl && !mermaidCode ? (
        <div className={`overflow-hidden rounded-xl bg-surface-container-lowest border border-outline-variant/20 flex items-center justify-center p-2 ${isZoomed ? 'max-h-none' : 'max-h-[460px]'}`}>
          <img
            src={imageUrl}
            alt={title || 'Technical Concept'}
            className="w-full h-auto object-contain max-h-[500px] rounded-lg"
            loading="lazy"
          />
        </div>
      ) : svgHtml && !hasError ? (
        <div
          className={`overflow-x-auto rounded-xl bg-surface-container-lowest/80 border border-outline-variant/20 p-4 flex justify-center items-center transition-all duration-300 ${
            isZoomed ? 'scale-110 p-8 my-4' : ''
          }`}
          dangerouslySetInnerHTML={{ __html: svgHtml }}
        />
      ) : hasError && mermaidCode ? (
        <div className="p-3 bg-surface-container-lowest rounded-xl border border-outline-variant/30 font-mono text-xs overflow-x-auto">
          <pre className="text-on-surface-variant">{mermaidCode}</pre>
        </div>
      ) : null}

      {/* Caption description */}
      {description && (
        <div className="text-xs text-on-surface-variant leading-relaxed font-sans pt-1 border-t border-outline-variant/20 flex items-start gap-2">
          <span className="font-mono text-[10px] uppercase font-bold text-outline shrink-0 pt-0.5">
            Caption:
          </span>
          <span>{description}</span>
        </div>
      )}
    </div>
  );
};

