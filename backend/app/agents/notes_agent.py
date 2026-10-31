import re
import logging
from typing import Dict, List, Optional
from app.domain.schemas.notes import StructuredVideoNotes, ReviewReport
from app.domain.schemas.transcript import TranscriptData, TranscriptSegment
from app.domain.schemas.topic_plan import VideoTopicPlan
from app.domain.schemas.research import VideoResearchBundle
from app.integrations.openai.client import OpenAIClientInterface
from app.integrations.youtube.parser import construct_video_url

logger = logging.getLogger(__name__)


class TechnicalNotesAgent:
    """
    Synthesizes dense, structured technical notes grounded in transcript evidence,
    enriched with topic plans, foundational theory, and authoritative external research.
    Resolves evidence segment IDs to verified start timestamps, constructs video watch links,
    and programmatically eliminates diagram placeholders and empty blocks.
    """

    def __init__(self, llm_client: OpenAIClientInterface):
        self.llm = llm_client

    @staticmethod
    def _scrub_salutations(text: Optional[str]) -> Optional[str]:
        if not text:
            return text
        hindi_patterns = [
            r'(?i)(?:हाय|हैलो|हेलो|नमस्ते|नमस्कार)\s*(?:गाइस|दोस्तों|साथियों|फ्रेंड्स|मित्रों|everyone|guys)?[,!.\s]*',
            r'(?i)(?:माय\s+नेम\s+इज|मेरा\s+नाम\s+है)[^.!?।\n…]+?(?:एंड|और|and)?[^.!?।\n…]*?[.!?।…]+',
            r'(?i)(?:यू\s+)?(?:वेलकम|वेलकम्)\s+टू\s+(?:माय|my)\s*(?:यूट्यूब|youtube)?\s*चैनल[^.!?।\n…]*?[.!?।…]+',
            r'(?i)(?:मेरे\s+चैनल\s+(?:में|पर)\s+स्वागत\s+है)[^.!?।\n…]*?[.!?।…]+',
            r'(?i)(?:इस\s+वीडियो\s+में\s+(?:भी\s+)?हम\s+लोग\s+अपना|आज\s+के\s+इस\s+वीडियो\s+में|आज\s+हम\s+बात\s+करेंगे)[^.!?।\n…]*?प्लेलिस्ट\s+कंटिन्यू[^.!?।\n…]*?[.!?।…]+',
            r'(?i)(?:वीडियो\s+को\s+लाइक\s+करें|चैनल\s+को\s+सब्सक्राइब\s+करें)[^.!?।\n…]*?[.!?।…]+',
        ]
        english_patterns = [
            r'(?i)^(?:Hi|Hello|Hey|Welcome|Good\s+(?:morning|evening|afternoon)|What\'s\s+up|Howdy)\s*(?:guys|everyone|everybody|friends|folks|viewers|there|all)?[,!.\s]*',
            r'(?i)(?:welcome\s+(?:back\s+)?to\s+(?:my|our|the)\s+(?:youtube\s+)?channel)[^.!?\n]*?[.!?]+',
            r'(?i)(?:my\s+name\s+is\s+[^.!?\n]+?(?:and\s+welcome|and\s+today|and\s+in\s+this\s+video)[^.!?\n]*?[.!?]+)',
            r'(?i)(?:in\s+this\s+video\s+(?:we\s+are\s+going\s+to|we\s+will)\s+continue\s+our\s+playlist)[^.!?\n]*?[.!?]+',
            r'(?i)(?:don\'t\s+forget\s+to\s+(?:like|subscribe|comment|share)|hit\s+the\s+(?:bell|subscribe)\s+(?:icon|button))[^.!?\n]*?[.!?]+',
            r'(?i)(?:thanks\s+for\s+watching\s+(?:and\s+see\s+you\s+in\s+the\s+next\s+video)?)[^.!?\n]*?[.!?]+',
        ]
        cleaned = text
        for pat in hindi_patterns + english_patterns:
            cleaned = re.sub(pat, '', cleaned)
        cleaned = re.sub(r'^[,\s.!।…\-]+', '', cleaned)
        return cleaned.strip()

    @classmethod
    def _scrub_text(cls, text: Optional[str]) -> Optional[str]:
        if not text:
            return text
        # 1. Enforce strict terminology corrections (e.g. Model Command Protocol -> Model Context Protocol)
        cleaned = re.sub(r"(?i)\bModel\s+Command\s+Protocol\b", "Model Context Protocol", text)

        # 2. Strip conversational salutations, YouTuber channel intros, and subscriber banter
        cleaned = cls._scrub_salutations(cleaned)

        # 3. Regex to strip sentences mentioning placeholder diagrams or visuals
        cleaned = re.sub(
            r"(?i)(?:a\s+)?diagram\s+(?:could|can|might)\s+be\s+used\s+here[^.!?]*[.!?]?",
            "",
            cleaned
        )
        cleaned = re.sub(
            r"(?i)\b(?:insert|placeholder\s+for|add\s+a)\s+(?:diagram|image|visual)[^.!?]*[.!?]?",
            "",
            cleaned
        )

        # 4. Clean spacing while preserving paragraph structure
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
        return cleaned

    def _clean_notes_placeholders(self, notes: StructuredVideoNotes):
        notes.executive_summary = self._scrub_text(notes.executive_summary)
        notes.comprehensive_theory_background = self._scrub_text(notes.comprehensive_theory_background)
        notes.architecture_and_workflows = self._scrub_text(notes.architecture_and_workflows)
        notes.revision_sheet = self._scrub_text(notes.revision_sheet)

        DUMMY_DOMAINS = ("example.com", "domain.com", "cloud.domain.com", "placeholder.org", "test.com", "foo.bar")

        def _is_valid_source(src) -> bool:
            if not src or not getattr(src, "url", None):
                return False
            url_lower = src.url.lower()
            return not any(d in url_lower for d in DUMMY_DOMAINS)

        if notes.all_sources:
            notes.all_sources = [s for s in notes.all_sources if _is_valid_source(s)]

        for s in notes.sections:
            s.from_video = self._scrub_text(s.from_video)
            s.additional_theory = self._scrub_text(s.additional_theory)
            s.markdown_content = self._scrub_text(s.markdown_content) or ""
            if s.cited_sources:
                s.cited_sources = [src for src in s.cited_sources if _is_valid_source(src)]
            # Programmatically prevent empty or stub theory blocks from rendering
            if s.additional_theory and len(s.additional_theory.strip()) < 20:
                s.additional_theory = None
            if s.from_video and len(s.from_video.strip()) < 15:
                if s.markdown_content and len(s.markdown_content.strip()) > 25:
                    s.from_video = s.markdown_content
                else:
                    s.from_video = None

    def _ground_timestamps(
        self,
        notes: StructuredVideoNotes,
        segment_map: Dict[str, TranscriptSegment],
        video_id: str
    ):
        """Enforces application-code verification of timestamps. Never allows LLM to invent timestamps."""
        for section in notes.sections:
            valid_starts: List[float] = []
            for seg_id in section.evidence_segment_ids:
                if seg_id in segment_map:
                    valid_starts.append(segment_map[seg_id].start_seconds)

            if valid_starts:
                earliest_start = min(valid_starts)
                section.timestamp_seconds = earliest_start
                section.timestamped_watch_url = construct_video_url(video_id, earliest_start)
            else:
                section.timestamp_seconds = None
                section.timestamped_watch_url = construct_video_url(video_id)

    async def generate_notes_for_video(
        self,
        video_metadata: dict,
        transcript: TranscriptData,
        detail_level: str = "standard",
        topic_plan: Optional[VideoTopicPlan] = None,
        research_bundle: Optional[VideoResearchBundle] = None
    ) -> StructuredVideoNotes:
        segment_map: Dict[str, TranscriptSegment] = {s.id: s for s in transcript.segments}
        raw_evidence = [s.model_dump() for s in transcript.segments]
        formatted_text = "\n".join(f"[{s.id} @ {s.formatted_start}] {s.text}" for s in transcript.segments)

        notes = await self.llm.generate_structured_notes(
            video_metadata=video_metadata,
            transcript_text=formatted_text,
            evidence_segments=raw_evidence,
            detail_level=detail_level,
            topic_plan=topic_plan,
            research_bundle=research_bundle
        )

        video_id = video_metadata.get("video_id", "")
        self._ground_timestamps(notes, segment_map, video_id)
        self._clean_notes_placeholders(notes)
        return notes

    async def revise_notes_for_video(
        self,
        video_metadata: dict,
        transcript: TranscriptData,
        notes: StructuredVideoNotes,
        review: ReviewReport,
        research_bundle: Optional[VideoResearchBundle] = None
    ) -> StructuredVideoNotes:
        segment_map: Dict[str, TranscriptSegment] = {s.id: s for s in transcript.segments}
        transcript_text = transcript.get_text()

        revised = await self.llm.revise_notes(
            notes=notes,
            review=review,
            transcript_text=transcript_text,
            research_bundle=research_bundle
        )

        video_id = video_metadata.get("video_id", "")
        self._ground_timestamps(revised, segment_map, video_id)
        self._clean_notes_placeholders(revised)
        return revised
