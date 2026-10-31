import logging
from playwright.async_api import async_playwright
from app.core.exceptions import PDFGenerationException
from app.integrations.pdf.renderer import PDFRendererInterface

logger = logging.getLogger(__name__)


class PlaywrightPDFRenderer(PDFRendererInterface):
    """
    Renders HTML + print CSS into a polished, publication-grade PDF using Playwright Chromium.
    Executes client-side Mermaid rendering with restrained editorial styling.
    Ensures font shaping, Devanagari Unicode support, and internal TOC navigation.
    """

    async def render_html_to_pdf(self, html_content: str) -> bytes:
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
                )
                page = await browser.new_page()
                
                # Load HTML into Chromium
                await page.set_content(html_content, wait_until="load")

                # Wait for web fonts (including Devanagari and Inter) to load and shape
                try:
                    await page.evaluate("document.fonts.ready")
                except Exception as font_err:
                    logger.debug("Font ready check: %s", font_err)
                
                # Execute Mermaid.js to render diagrams as inline vector SVGs in restrained theme
                try:
                    result = await page.evaluate(r"""async () => {
                        if (!window.mermaid) {
                            return { error: 'window.mermaid is undefined' };
                        }
                        try {
                            window.mermaid.parseError = function(err, hash) {
                                // Suppress browser DOM error injection
                            };
                            window.mermaid.initialize({
                                startOnLoad: false,
                                suppressErrorRendering: true,
                                theme: 'base',
                                securityLevel: 'loose',
                                themeVariables: {
                                    primaryColor: '#F5F7F9',
                                    primaryTextColor: '#202B36',
                                    primaryBorderColor: '#D9E0E6',
                                    lineColor: '#5F6B76',
                                    secondaryColor: '#EBF1F5',
                                    tertiaryColor: '#FFFFFF',
                                    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                                    fontSize: '11px',
                                    edgeLabelBackground: '#FFFFFF',
                                    clusterBkg: '#FAFBFD',
                                    clusterBorder: '#D9E0E6'
                                }
                            });

                            function sanitizeDsl(raw) {
                                if (!raw) return '';
                                let text = raw.trim();
                                // Strip fences if present
                                text = text.replace(/^```[a-z]*\s*/i, '').replace(/\s*```$/i, '').trim();
                                // Newline after declaration
                                text = text.replace(/^(flowchart\s+[a-z]{2}|graph\s+[a-z]{2})\s*;?\s+([^\n]+)$/im, '$1\\n    $2');
                                // Split joined statements
                                text = text.replace(/(\]|\)|\})\s+([A-Za-z0-9_]+\s*(?:-->|---|-.->|==>|->>|\[|\())/g, '$1\\n    $2');
                                text = text.replace(/(\]|\)|\})\s+(subgraph\b)/gi, '$1\\n$2');
                                text = text.replace(/\bend\s+([A-Za-z0-9_]+\b)/gi, 'end\\n    $1');
                                text = text.replace(/\bend\s+(subgraph\b)/gi, 'end\\n$1');
                                // Fix isolated single dash arrows -> to -->
                                text = text.replace(/(?<![-=.])->(?!>)/g, '-->');
                                // Clean trailing semicolons
                                text = text.replace(/;\s*$/gm, '');
                                text = text.replace(/\bend\s*;/gi, 'end');
                                return text.trim();
                            }

                            const nodes = document.querySelectorAll('.mermaid-canvas, .mermaid');
                            let successCount = 0;
                            for (let i = 0; i < nodes.length; i++) {
                                const node = nodes[i];
                                const box = node.closest('.diagram-box');
                                try {
                                    const raw = node.textContent.trim();
                                    const code = sanitizeDsl(raw);
                                    if (!code || code.length < 10) {
                                        if (box) box.remove();
                                        else node.remove();
                                        continue;
                                    }
                                    const { svg } = await window.mermaid.render('diagram_svg_' + i, code);
                                    node.innerHTML = svg;
                                    successCount++;
                                } catch (err) {
                                    console.warn('Mermaid node render error at index ' + i + ':', err);
                                    if (box) box.remove();
                                    else node.remove();
                                }
                            }

                            // Comprehensive safety sweep: remove any residual Mermaid error elements or syntax error blocks
                            document.querySelectorAll('svg[aria-roledescription="error"], .error-text, svg.error, [id^="dmermaid"]').forEach(el => {
                                const box = el.closest('.diagram-box');
                                if (box) box.remove();
                                else el.remove();
                            });
                            document.querySelectorAll('.diagram-box').forEach(box => {
                                const svg = box.querySelector('svg');
                                const hasError = box.textContent.includes('Syntax error in text') || 
                                                 box.textContent.includes('mermaid version') ||
                                                 (svg && svg.getAttribute('aria-roledescription') === 'error') ||
                                                 !svg;
                                if (hasError) {
                                    box.remove();
                                }
                            });
                            document.querySelectorAll('body > div[id^="d"], body > svg').forEach(el => {
                                if (el.textContent.includes('Syntax error') || el.querySelector('.error-text') || el.getAttribute('aria-roledescription') === 'error') {
                                    el.remove();
                                }
                            });

                            return {
                                totalNodes: nodes.length,
                                successCount: successCount,
                                svgCount: document.querySelectorAll('svg').length,
                                remainingDiagrams: document.querySelectorAll('.diagram-box').length
                            };
                        } catch (e) {
                            return { error: e.toString() };
                        }
                    }""")
                    logger.info(f"Mermaid rendering in Chromium result: {result}")
                    # Allow layout, SVGs, and font rendering to settle
                    await page.wait_for_timeout(800)
                except Exception as ex:
                    logger.warning(f"Mermaid execution note: {ex}")

                pdf_bytes = await page.pdf(
                    format="A4",
                    print_background=True,
                    margin={
                        "top": "20mm",
                        "bottom": "20mm",
                        "left": "18mm",
                        "right": "18mm"
                    },
                    display_header_footer=True,
                    header_template='<span></span>',
                    footer_template='<div style="font-size:7.5pt; font-family:\'Inter\',sans-serif; color:#5F6B76; width:100%; text-align:center;">Page <span class="pageNumber"></span> of <span class="totalPages"></span></div>'
                )
                await browser.close()
                return pdf_bytes
        except Exception as e:
            logger.error(f"Playwright PDF rendering failed: {e}")
            raise PDFGenerationException(f"Playwright PDF compilation failed: {str(e)}")
