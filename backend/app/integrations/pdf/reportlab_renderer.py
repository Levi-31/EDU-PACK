import io
from app.integrations.pdf.renderer import PDFRendererInterface, strip_pdf_metadata
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def _draw_watermark(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#202B36"), alpha=0.05)
    canvas.setFont("Helvetica-Bold", 44)
    canvas.translate(doc.pagesize[0] / 2, doc.pagesize[1] / 2)
    canvas.rotate(35)
    canvas.drawCentredString(0, 0, "tokens.to.systems")
    canvas.restoreState()


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
            bottomMargin=54,
            title="tokens.to.systems"
        )
        styles = getSampleStyleSheet()
        normal_style = styles["Normal"]
        title_style = styles["Title"]

        story = [
            Paragraph("tokens.to.systems — Technical Study Guide", title_style),
            Spacer(1, 14),
            Paragraph("Rendered via Fallback Engine", styles["Heading3"]),
            Spacer(1, 14),
            Paragraph("This document was generated using the fallback PDF pipeline. See HTML version for full styling.", normal_style)
        ]
        doc.build(story, onFirstPage=_draw_watermark, onLaterPages=_draw_watermark)
        return strip_pdf_metadata(buffer.getvalue())

