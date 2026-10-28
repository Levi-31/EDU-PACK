from abc import ABC, abstractmethod


class PDFRendererInterface(ABC):
    @abstractmethod
    async def render_html_to_pdf(self, html_content: str) -> bytes:
        """
        Renders an HTML document to PDF bytes preserving print CSS and clickable hyperlinks.
        """
        pass
