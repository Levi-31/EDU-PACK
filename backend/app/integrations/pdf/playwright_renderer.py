import logging
from playwright.async_api import async_playwright
from app.core.exceptions import PDFGenerationException
from app.integrations.pdf.renderer import PDFRendererInterface

logger = logging.getLogger(__name__)


class PlaywrightPDFRenderer(PDFRendererInterface):
    """
    Renders HTML + print CSS into a polished, high-fidelity PDF using Playwright Chromium.
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
                
                # Allow Mermaid or any client-side scripts to settle if included
                try:
                    await page.wait_for_timeout(500)
                except Exception:
                    pass

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

