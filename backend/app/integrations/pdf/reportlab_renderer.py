import io
from app.integrations.pdf.renderer import PDFRendererInterface
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


class ReportLabFallbackRenderer(PDFRendererInterface):
    """
    Lightweight fallback PDF renderer if headless Chromium cannot launch.
    """

    async def render_html_to_pdf(self, html_content: str) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=54,
            leftMargin=54,
            topMargin=54,
            bottomMargin=54
        )
        styles = getSampleStyleSheet()
        normal_style = styles["Normal"]
        title_style = styles["Title"]

        story = [
            Paragraph("Playlist Scholar — Technical Study Guide", title_style),
            Spacer(1, 14),
            Paragraph("Rendered via Fallback Engine", styles["Heading3"]),
            Spacer(1, 14),
            Paragraph("This document was generated using the fallback PDF pipeline. See HTML version for full styling.", normal_style)
        ]
        doc.build(story)
        return buffer.getvalue()

