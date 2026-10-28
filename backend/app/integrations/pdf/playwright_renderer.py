import logging
from playwright.async_api import async_playwright
from app.core.exceptions import PDFGenerationException
from app.integrations.pdf.renderer import PDFRendererInterface

logger = logging.getLogger(__name__)


class PlaywrightPDFRenderer(PDFRendererInterface):
    """
    Renders HTML + print CSS into a polished, publication-grade PDF using Playwright Chromium.
    Executes client-side Mermaid rendering to transform diagram DSL into crisp vector SVGs.
    Guarantees clickable external hyperlinks (YouTube timestamps) and internal TOC navigation.
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
                
                # Execute Mermaid.js to render diagrams as inline vector SVGs
                try:
                    await page.evaluate("""async () => {
                        if (window.mermaid) {
                            try {
                                await mermaid.run();
                            } catch (e) {
                                console.error('Mermaid rendering notice:', e);
                            }
                        }
                    }""")
                    # Allow layout and font rendering to settle
                    await page.wait_for_timeout(800)
                except Exception as ex:
                    logger.debug(f"Mermaid execution note: {ex}")

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
                    header_template='<div style="font-size:8px; color:#888; width:100%; text-align:right; padding-right:20mm;">Playlist Scholar Technical Study Guide</div>',
                    footer_template='<div style="font-size:8px; color:#888; width:100%; text-align:center;">Page <span class="pageNumber"></span> of <span class="totalPages"></span></div>'
                )
                await browser.close()
                return pdf_bytes
        except Exception as e:
            logger.error(f"Playwright PDF rendering failed: {e}")
            raise PDFGenerationException(f"Playwright PDF compilation failed: {str(e)}")
