# Figures can't split across pages, so one that doesn't fit jumps to the next page and leaves a hole behind it.
# This runs in Chromium before printing. It lays the document out in page-sized columns, which paginate like print,
# then closes each hole by shrinking the figure slightly or letting the text after it flow up, as textbooks do.
CLOSE_FIGURE_GAPS_JS = r"""() => {
    const container = document.querySelector('.research-container');
    const content = document.querySelector('.research-content');
    if (!container || !content) return { skipped: true };

    const PAGE_WIDTH = 658;    // A4 width minus 18mm side margins
    const PAGE_HEIGHT = 971;   // A4 height minus 20mm top and bottom margins
    const MIN_GAP = 110;       // About 30mm; anything smaller reads as normal spacing
    const MILD_SHRINK = 0.8;   // Smallest size accepted without trying to move text first
    const MAX_SHRINK = 0.6;    // Smallest size accepted at all; below this labels get hard to read
    const original = container.style.cssText;
    container.style.cssText += `;width:${PAGE_WIDTH}px;height:${PAGE_HEIGHT}px;column-width:${PAGE_WIDTH}px;column-gap:0;column-fill:auto;`;

    const isFigure = el => el.matches('.diagram-box') || (el.matches('p') && el.querySelector(':scope > img'));
    const isHeading = el => /^H[1-6]$/.test(el.tagName);
    const isSectionEnd = el => /^(H1|H2|HR)$/.test(el.tagName);
    const isUnsplittable = el => /^(PRE|TABLE|BLOCKQUOTE)$/.test(el.tagName);
    const origin = () => container.getBoundingClientRect();
    const pageOf = rect => Math.floor((rect.left - origin().left + 1) / PAGE_WIDTH);
    const firstRect = el => el.getClientRects()[0];
    const lastRect = el => { const rects = el.getClientRects(); return rects[rects.length - 1]; };

    function gapBefore(figure) {
        let previous = figure.previousElementSibling;
        while (previous && isHeading(previous)) previous = previous.previousElementSibling;
        if (!previous) return 0;
        const end = lastRect(previous);
        if (!end || pageOf(end) >= pageOf(firstRect(figure))) return 0;
        return PAGE_HEIGHT - (end.bottom - origin().top);
    }

    function shrinkToFit(figure, gap, minScale) {
        const graphic = figure.querySelector('svg, img');
        if (!graphic) return false;
        const figureHeight = firstRect(figure).height;
        const graphicHeight = graphic.getBoundingClientRect().height;
        const scale = (graphicHeight - (figureHeight - gap) - 24) / graphicHeight;
        if (scale < minScale || scale >= 1) return false;
        if (graphic.tagName.toLowerCase() === 'img') {
            const width = graphic.getBoundingClientRect().width * scale;
            graphic.style.setProperty('width', `${width}px`, 'important');
            graphic.style.setProperty('max-width', `${width}px`, 'important');
        } else {
            graphic.style.setProperty('max-height', `${graphicHeight * scale}px`);
        }
        return true;
    }

    // Moves the next block of text above the figure; a heading travels with the block it introduces
    function pullTextAbove(figure, gap) {
        const next = figure.nextElementSibling;
        if (!next || isSectionEnd(next) || isFigure(next)) return false;
        const group = [next];
        if (isHeading(next)) {
            const body = next.nextElementSibling;
            if (!body || isSectionEnd(body) || isFigure(body)) return false;
            group.push(body);
        }
        const tail = group[group.length - 1];
        if (isUnsplittable(tail) && firstRect(tail).height > gap) return false;
        group.forEach(el => figure.parentNode.insertBefore(el, figure));
        return true;
    }

    const stats = { figures: 0, shrunk: 0, moved: 0, remaining: 0 };
    Array.from(content.children).filter(isFigure).forEach(figure => {
        stats.figures += 1;
        for (let attempt = 0; attempt < 12; attempt++) {
            const gap = gapBefore(figure);
            if (gap < MIN_GAP) return;
            if (attempt === 0 && shrinkToFit(figure, gap, MILD_SHRINK)) { stats.shrunk += 1; continue; }
            if (pullTextAbove(figure, gap)) { stats.moved += 1; continue; }
            if (shrinkToFit(figure, gap, MAX_SHRINK)) { stats.shrunk += 1; continue; }
            stats.remaining += 1;
            return;
        }
    });

    container.style.cssText = original;
    return stats;
}"""
