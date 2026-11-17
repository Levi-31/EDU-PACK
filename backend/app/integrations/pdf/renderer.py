import re
from abc import ABC, abstractmethod

_INFO_REF = re.compile(rb"/Info\s+(\d+)\s+0\s+R")
_INFO_ENTRY = re.compile(
    rb"/(?:Author|Creator|CreationDate|Keywords|ModDate|Producer|Subject|Trapped)\s*"
    rb"(?:\((?:[^()\\]|\\.)*\)|<[0-9A-Fa-f\s]*>|/\w+)",
    re.DOTALL,
)


def shorten_title(title: str) -> str:
    """Drops a subtitle ("Roadmap: A Clear Path to..." becomes "Roadmap") when what remains still names the document."""
    title = " ".join(title.split())
    head = re.split(r"\s*[:|\u2013\u2014]\s+|\s+-\s+", title, maxsplit=1)[0]
    return head if len(head.split()) >= 2 else title


def _estimated_width(text: str, font_pt: float) -> float:
    """Conservative width of bold sans-serif text; the heading must never run past the page edge."""
    units = sum(0.3 if c.isspace() else 0.74 if c.isupper() else 0.6 for c in text)
    return units * font_pt


def fit_heading(title: str, width_pt: float, max_pt: float, min_pt: float = 14) -> dict:
    """Returns heading text and a font size that keep it on one line, cutting whole words only if the minimum size can't fit."""
    text = shorten_title(title)
    words = text.split()
    while len(words) > 1 and _estimated_width(" ".join(words), min_pt) > width_pt:
        words.pop()
    text = " ".join(words)
    natural_width = _estimated_width(text, 1) or 1
    return {"text": text, "font_pt": round(max(min_pt, min(max_pt, width_pt / natural_width)), 1)}


def strip_pdf_metadata(pdf_bytes: bytes) -> bytes:
    """
    Blanks every entry except /Title in the PDF document info dictionary (renderer name, timestamps, etc).
    Entries are overwritten with same-length whitespace so xref offsets stay valid without rewriting the file.
    """
    refs = _INFO_REF.findall(pdf_bytes)
    if not refs:
        return pdf_bytes
    info_obj = re.search(rb"\b%s\s+0\s+obj\b.*?endobj" % refs[-1], pdf_bytes, re.DOTALL)
    if not info_obj:
        return pdf_bytes
    cleaned = _INFO_ENTRY.sub(lambda m: b" " * len(m.group()), info_obj.group())
    return pdf_bytes[:info_obj.start()] + cleaned + pdf_bytes[info_obj.end():]


class PDFRendererInterface(ABC):
    @abstractmethod
    async def render_html_to_pdf(self, html_content: str) -> bytes:
        """
        Renders an HTML document to PDF bytes preserving print CSS and clickable hyperlinks.
        """
        pass

