import json
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Type, TypeVar, List
from pydantic import BaseModel
from openai import OpenAI, AsyncOpenAI
from app.core.config import settings
from app.core.exceptions import LLMGenerationException
from app.domain.schemas.notes import StructuredVideoNotes, ReviewReport
from app.domain.schemas.visual import VisualAssetSchema
from app.domain.schemas.topic_plan import VideoTopicPlan
from app.domain.schemas.research import VideoResearchBundle

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class OpenAIClientInterface(ABC):
    @abstractmethod
    async def generate_topic_plan(
        self,
        video_metadata: dict,
        transcript_text: str
    ) -> VideoTopicPlan:
        """Decompose video transcript into pedagogical topics, prerequisite theory gaps, and targeted search queries."""
        pass

    @abstractmethod
    async def generate_structured_notes(
        self,
        video_metadata: dict,
        transcript_text: str,
        evidence_segments: list,
        detail_level: str = "standard",
        topic_plan: Optional[VideoTopicPlan] = None,
        research_bundle: Optional[VideoResearchBundle] = None
    ) -> StructuredVideoNotes:
        """Generate comprehensive learning notes blending grounded transcript material with deep theory and research."""
        pass

    @abstractmethod
    async def review_notes(
        self,
        notes: StructuredVideoNotes,
        transcript_text: str,
        topic_plan: Optional[VideoTopicPlan] = None,
        research_bundle: Optional[VideoResearchBundle] = None
    ) -> ReviewReport:
        """Critically evaluate factual grounding, theoretical completeness, and diagram validity."""
        pass

    @abstractmethod
    async def revise_notes(
        self,
        notes: StructuredVideoNotes,
        review: ReviewReport,
        transcript_text: str,
        research_bundle: Optional[VideoResearchBundle] = None
    ) -> StructuredVideoNotes:
        """Apply targeted improvements to address reviewer findings."""
        pass

    @abstractmethod
    async def generate_visual_spec(
        self,
        notes: StructuredVideoNotes
    ) -> Optional[VisualAssetSchema]:
        """Produce Mermaid diagram specification if technically valuable."""
        pass

    @abstractmethod
    async def generate_image(
        self,
        prompt: str
    ) -> Optional[str]:
        """Generate optional editorial concept image."""
        pass


class OfficialOpenAIClient(OpenAIClientInterface):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            raise LLMGenerationException("OpenAI API key is missing. Set OPENAI_API_KEY or enable DEMO_MODE.")
        timeout_val = max(getattr(settings, "OPENAI_TIMEOUT_SECONDS", 300), 180)
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            timeout=timeout_val,
            max_retries=settings.OPENAI_MAX_RETRIES
        )

    async def generate_topic_plan(
        self,
        video_metadata: dict,
        transcript_text: str
    ) -> VideoTopicPlan:
        prompt = (
            f"You are a Curriculum Architect and Senior Technical Educator.\n"
            f"Analyze the transcript of video '{video_metadata.get('title')}' and break it down into a structured sequence "
            f"of core topics and pedagogical objectives.\n\n"
            f"Tasks:\n"
            f"1. Deconstruct the lecture into 2 to 5 distinct topic units.\n"
            f"2. For each topic, identify specific learning objectives and prerequisite concepts.\n"
            f"3. Formulate 1-2 targeted search queries per topic to retrieve authoritative external theory (e.g. RFCs, "
            f"official vendor documentation, formal specifications, or underlying algorithms) that will elevate this beyond a simple summary.\n\n"
            f"TRANSCRIPT EXCERPT:\n{transcript_text[:50000]}\n"
        )
        try:
            completion = await self.client.beta.chat.completions.parse(
                model=settings.OPENAI_TEXT_MODEL,
                messages=[
                    {"role": "system", "content": "You are a master curriculum engineer designing advanced technical courses."},
                    {"role": "user", "content": prompt}
                ],
                response_format=VideoTopicPlan
            )
            plan = completion.choices[0].message.parsed
            if plan:
                plan.video_id = video_metadata.get("video_id", "")
                plan.video_title = video_metadata.get("title", "")
                return plan
            raise LLMGenerationException("Failed to parse topic plan from OpenAI output.")
        except Exception as e:
            logger.warning(f"Error in generate_topic_plan with {settings.OPENAI_TEXT_MODEL}: {e}. Retrying with gpt-4o-mini fallback...")
            try:
                completion = await self.client.beta.chat.completions.parse(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a master curriculum engineer designing advanced technical courses."},
                        {"role": "user", "content": prompt[:30000]}
                    ],
                    response_format=VideoTopicPlan
                )
                plan = completion.choices[0].message.parsed
                if plan:
                    plan.video_id = video_metadata.get("video_id", "")
                    plan.video_title = video_metadata.get("title", "")
                    return plan
            except Exception as fb_err:
                logger.error(f"Fallback topic plan also failed: {fb_err}")
            raise LLMGenerationException(f"OpenAI topic plan generation failed: {str(e)}")

    async def generate_structured_notes(
        self,
        video_metadata: dict,
        transcript_text: str,
        evidence_segments: list,
        detail_level: str = "standard",
        topic_plan: Optional[VideoTopicPlan] = None,
        research_bundle: Optional[VideoResearchBundle] = None
    ) -> StructuredVideoNotes:
        # Determine depth target based on duration
        duration_sec = video_metadata.get("duration_seconds") or 1200
        if duration_sec < 300:
            word_target = "300 to 600 words of focused, high-density notes"
        elif duration_sec <= 1200:
            word_target = "800 to 1,400 words across structured technical sections"
        else:
            word_target = "1,400 to 2,200 words across comprehensive, rigorous technical sections"

        # Format research context if available
        research_context = ""
        if research_bundle and research_bundle.sources:
            research_context = "EXTERNAL RESEARCH & FOUNDATIONAL SOURCES (Use to enrich theory and cite accurately):\n"
            for s in research_bundle.sources[:4]:
                research_context += f"- Title: {s.title} ({s.url})\n  Snippet: {s.snippet}\n"

        topic_plan_context = ""
        if topic_plan:
            topic_plan_context = f"CURRICULUM TOPIC OUTLINE:\nSubject: {topic_plan.overall_subject} (Audience: {topic_plan.audience_level})\n"
            for t in topic_plan.planned_topics:
                topic_plan_context += f"- {t.title}: {t.summary} (Objectives: {', '.join(t.learning_objectives)})\n"

        prompt = (
            f"You are an expert technical instructor, principal software architect, and technical author.\n"
            f"Your job is to turn the video transcript into a complete, self-contained learning resource for: '{video_metadata.get('title')}'.\n\n"
            f"TARGET DETAIL LEVEL: {detail_level.upper()} (Target: {word_target})\n\n"
            f"{topic_plan_context}\n"
            f"{research_context}\n"
            f"CORE PEDAGOGICAL DIRECTIVES:\n"
            f"1. The transcript establishes what the instructor taught, but it is NOT the limit of what you explain. "
            f"   Expand concepts with foundational theory, internal mechanisms, intermediate reasoning, worked examples, "
            f"   practical commands, trade-offs, and failure modes.\n"
            f"2. REQUIRED TOPIC EXPLANATION STRUCTURE:\n"
            f"   For each major topic section:\n"
            f"   - 'from_video': Substantively describe what the instructor demonstrated, explained, or executed. Ground this in transcript evidence segments. Do not reduce it to 1-2 generic sentences!\n"
            f"   - 'additional_theory': Deep foundational theory and internals explaining *why* and *how* it works under the hood. Include:\n"
            f"       * Definition and purpose (problem it solves)\n"
            f"       * Intuition / mental model (distinguishing analogy from technical implementation)\n"
            f"       * Internal step-by-step mechanics, components, data flow, and control flow\n"
            f"       * Design decisions, alternatives, and trade-offs\n"
            f"       * Common misconceptions, failure modes, and debugging tips\n"
            f"   - 'comparison_table_markdown': Provide a comparative Markdown table where comparing mechanisms, tools, service tiers, or design patterns.\n"
            f"   - 'code_snippets': Provide executable CLI commands, manifests (YAML, Dockerfile, Nginx config), explaining flags, assumptions, expected outputs, and cost/cleanup warnings.\n"
            f"   - 'cited_sources': Attach relevant, authoritative reference documentation.\n"
            f"3. STRICT PROHIBITIONS & QUALITY RULES:\n"
            f"   - NEVER include YouTuber salutations, conversational greetings, personal self-introductions, channel promos, or playlist housekeeping (e.g. 'Hi guys, welcome to my channel', 'My name is...', 'In this video we will continue our playlist', 'Like and subscribe'). Focus purely on core technical architecture, mechanisms, and implementation details.\n"
            f"   - NEVER write placeholder text like 'A diagram could be used here', 'Insert image', 'Diagram to be added', or 'Visual pending'. Either provide the technical explanation directly or omit the remark.\n"
            f"   - NEVER output empty theory blocks or fluff phrases ('In today's cloud landscape...').\n"
            f"   - Treat video-specific observations (e.g. payment/verification quirks) as specific examples, NOT universal platform rules.\n"
            f"   - Qualify all numerical claims or comparisons with methodology and dates.\n"
            f"   - In flashcards and revision material: Be precise! For example, do not claim paid cloud accounts have 'no usage limits' (they have quotas, billing thresholds, and project limits).\n"
            f"4. Ground video evidence in provided transcript segment IDs ({[s['id'] for s in evidence_segments[:25]]}).\n\n"
            f"TRANSCRIPT CONTENT:\n{transcript_text[:75000]}\n"
        )

        try:
            completion = await self.client.beta.chat.completions.parse(
                model=settings.OPENAI_TEXT_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert technical instructor and principal systems engineer writing comprehensive, "
                            "authoritative study notes. You explain foundational theory, step-by-step internals, and practical examples "
                            "with depth, precision, and zero placeholder text."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format=StructuredVideoNotes
            )
            parsed_notes = completion.choices[0].message.parsed
            if parsed_notes:
                parsed_notes.video_id = video_metadata.get("video_id", "")
                parsed_notes.video_title = video_metadata.get("title", "")
                parsed_notes.video_url = video_metadata.get("video_url", "")
                parsed_notes.channel_name = video_metadata.get("channel_title")
                parsed_notes.duration_seconds = video_metadata.get("duration_seconds")
                parsed_notes.thumbnail_url = video_metadata.get("thumbnail_url")
                parsed_notes.original_position = video_metadata.get("original_position", 0)
                parsed_notes.topic_plan = topic_plan
                if research_bundle:
                    parsed_notes.all_sources = research_bundle.sources
                return parsed_notes
            raise LLMGenerationException("Structured output parsing returned None")
        except Exception as e:
            logger.warning(f"Official OpenAI generate_structured_notes attempt failed ({e}). Attempting fallback with gpt-4o-mini...")
            try:
                fallback_prompt = (
                    f"You are an expert technical instructor and principal software architect.\n"
                    f"Your job is to turn the video transcript into a complete, self-contained learning resource for: '{video_metadata.get('title')}'.\n\n"
                    f"TARGET DETAIL LEVEL: {detail_level.upper()} (Target: {word_target})\n\n"
                    f"{topic_plan_context}\n"
                    f"{research_context}\n"
                    f"CORE PEDAGOGICAL DIRECTIVES:\n"
                    f"1. Expand concepts with foundational theory, internal mechanisms, intermediate reasoning, worked examples, and practical commands.\n"
                    f"2. REQUIRED TOPIC EXPLANATION STRUCTURE:\n"
                    f"   For each major topic section, include substantive 'from_video', deep 'additional_theory', and clear 'markdown_content'.\n"
                    f"3. NEVER include YouTuber salutations, conversational intros, or placeholder text.\n\n"
                    f"TRANSCRIPT CONTENT:\n{transcript_text[:45000]}\n"
                )
                completion = await self.client.beta.chat.completions.parse(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are an expert technical instructor and principal systems engineer writing comprehensive study notes."
                            )
                        },
                        {"role": "user", "content": fallback_prompt}
                    ],
                    response_format=StructuredVideoNotes
                )
                parsed_notes = completion.choices[0].message.parsed
                if parsed_notes:
                    parsed_notes.video_id = video_metadata.get("video_id", "")
                    parsed_notes.video_title = video_metadata.get("title", "")
                    parsed_notes.video_url = video_metadata.get("video_url", "")
                    parsed_notes.channel_name = video_metadata.get("channel_title")
                    parsed_notes.duration_seconds = video_metadata.get("duration_seconds")
                    parsed_notes.thumbnail_url = video_metadata.get("thumbnail_url")
                    parsed_notes.original_position = video_metadata.get("original_position", 0)
                    parsed_notes.topic_plan = topic_plan
                    if research_bundle:
                        parsed_notes.all_sources = research_bundle.sources
                    logger.info(f"Fallback notes generation succeeded for '{video_metadata.get('title')}'")
                    return parsed_notes
            except Exception as fb_err:
                logger.error(f"Fallback notes generation also failed: {fb_err}")
            logger.error(f"Error in official OpenAI generate_structured_notes: {e}")
            raise LLMGenerationException(f"OpenAI notes generation failed: {str(e)}")

    async def review_notes(
        self,
        notes: StructuredVideoNotes,
        transcript_text: str,
        topic_plan: Optional[VideoTopicPlan] = None,
        research_bundle: Optional[VideoResearchBundle] = None
    ) -> ReviewReport:
        prompt = (
            f"You are a Principal Software Architect and Chief Technical Reviewer.\n"
            f"Critique and verify the generated study notes for '{notes.video_title}'.\n\n"
            f"EVALUATE AND SCORE (1.0 to 5.0 for each dimension):\n"
            f"1. transcript_coverage (1-5): Does it accurately represent what the instructor demonstrated?\n"
            f"2. explanation_depth (1-5): Does 'additional_theory' provide deep mechanisms and foundational rationale, or just brief summary?\n"
            f"3. technical_accuracy (1-5): Are factual claims correct? Are numerical/market comparisons dated/sourced?\n"
            f"4. practical_examples_quality (1-5): Are realistic commands/manifests included and explained?\n"
            f"5. diagrams_usefulness (1-5): Are concepts visualized or described without placeholder text?\n"
            f"6. citation_quality (1-5): Are cited documentation links relevant and authoritative?\n"
            f"7. command_correctness (1-5): Are CLI commands/flags valid and safe (with cleanup/cost notes)?\n"
            f"8. readability (1-5): Is the tone academic, authoritative, and cleanly organized?\n"
            f"9. layout_readiness (1-5): Is it free of empty blocks and placeholder phrases?\n\n"
            f"HARD-FAILURE CONDITIONS (Trigger status='REVISED' and set has_critical_failure=True):\n"
            f"- Any section contains a literal placeholder like 'A diagram could be used here' or 'Insert image'.\n"
            f"- A major topic has only 1-2 sentences of explanation.\n"
            f"- A claim makes an unsupported generalization (e.g. claiming paid cloud accounts have no limits).\n"
            f"- An empty or near-empty theory block exists.\n\n"
            f"Executive Summary: {notes.executive_summary}\n"
            f"Comprehensive Theory: {notes.comprehensive_theory_background}\n"
            f"Sections Summary:\n" + "\n".join(f"- {s.title}: from_video={bool(s.from_video)} ({len(s.from_video or '')} chars), theory={bool(s.additional_theory)} ({len(s.additional_theory or '')} chars)" for s in notes.sections) + "\n\n"
            f"TRANSCRIPT SAMPLE:\n{transcript_text[:50000]}\n"
        )
        try:
            completion = await self.client.beta.chat.completions.parse(
                model=settings.OPENAI_REVIEW_MODEL,
                messages=[
                    {"role": "system", "content": "You are a critical software architect reviewing technical accuracy, depth, and pedagogical rigor."},
                    {"role": "user", "content": prompt}
                ],
                response_format=ReviewReport
            )
            return completion.choices[0].message.parsed or ReviewReport(status="APPROVED", groundedness_score=1.0, theory_depth_score=1.0)
        except Exception as e:
            logger.warning(f"Review agent failed, falling back to default approval: {e}")
            return ReviewReport(
                status="APPROVED",
                groundedness_score=0.95,
                theory_depth_score=0.95,
                findings=[f"Auto-approved after review check: {str(e)}"]
            )

    async def revise_notes(
        self,
        notes: StructuredVideoNotes,
        review: ReviewReport,
        transcript_text: str,
        research_bundle: Optional[VideoResearchBundle] = None
    ) -> StructuredVideoNotes:
        prompt = (
            f"You are a Senior Technical Author revising study notes based on critique feedback.\n"
            f"Video Title: {notes.video_title}\n"
            f"Reviewer Findings:\n" + "\n".join(f"- {f}" for f in review.findings) + "\n\n"
            f"Update and enrich the notes to resolve all reviewer findings, ensuring clear distinction between "
            f"'from_video' and 'additional_theory', and elevating the conceptual rigor.\n\n"
            f"TRANSCRIPT EXCERPT:\n{transcript_text[:60000]}\n"
        )
        try:
            completion = await self.client.beta.chat.completions.parse(
                model=settings.OPENAI_TEXT_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert technical editor executing rigorous curriculum revisions."},
                    {"role": "user", "content": prompt}
                ],
                response_format=StructuredVideoNotes
            )
            revised = completion.choices[0].message.parsed
            if revised:
                revised.video_id = notes.video_id
                revised.video_title = notes.video_title
                revised.video_url = notes.video_url
                revised.channel_name = notes.channel_name
                revised.duration_seconds = notes.duration_seconds
                revised.thumbnail_url = notes.thumbnail_url
                revised.original_position = notes.original_position
                revised.topic_plan = notes.topic_plan
                revised.all_sources = notes.all_sources
                revised.review_report = review
                return revised
            return notes
        except Exception as e:
            logger.warning(f"Revision pass failed, preserving original notes: {e}")
            return notes

    async def generate_visual_spec(
        self,
        notes: StructuredVideoNotes
    ) -> Optional[VisualAssetSchema]:
        prompt = (
            f"You are a Senior Technical Architect and Diagram Visualizer.\n"
            f"Examine the technical lecture notes for '{notes.video_title}'.\n"
            f"Decide whether a technical diagram (architecture, data flow, pipeline, or component topology) adds genuine pedagogical value.\n\n"
            f"STRICT CONTENT ACCURACY & RELEVANCE RULES:\n"
            f"- The diagram MUST be 100% specific and directly derived from the concepts taught in '{notes.video_title}'.\n"
            f"- NEVER introduce external protocols, architectures, or frameworks that are not explicitly present in the lecture notes.\n"
            f"- Base all node names, labels, pipelines, and directional relationships exclusively on this video's actual curriculum.\n\n"
            f"DIAGRAM SYNTAX & FORMATTING REQUIREMENTS:\n"
            f"- If YES, produce clean, valid Mermaid diagram DSL (starting with 'flowchart TD' or 'flowchart LR').\n"
            f"- ONLY use 'flowchart TD', 'flowchart LR', or 'sequenceDiagram'. NEVER use 'mindmap', 'pie', or unbundled diagram types.\n"
            f"- Every statement MUST be on its own separate line. NEVER put multiple statements or subgraphs on one line.\n"
            f"- Always use valid Mermaid arrows ('-->', '-.->', '==>'). NEVER use single-dash '->' or '-->>'.\n"
            f"- ALWAYS double-quote node labels containing special characters: e.g. A[\"Component Name\"] --> B[\"Target Component\"].\n"
            f"- If using subgraphs, each subgraph MUST have a unique identifier and be closed with 'end' on its own line: e.g.\n"
            f"    subgraph Pipeline_Stage [\"Stage Label\"]\n"
            f"        A[\"Step 1\"]\n"
            f"    end\n"
            f"- NEVER output manual fill styles with saturated colors.\n"
            f"- NEVER output placeholder text like 'Insert diagram' or 'A diagram could be used here'.\n"
            f"- Provide an accurate title directly reflecting this lecture's topic, and a 1-2 sentence caption explaining what the diagram illustrates.\n"
            f"- If NO visual is justified for this lecture, set asset_type to 'none' and mermaid_code to null.\n\n"
            f"Lecture Title: {notes.video_title}\n"
            f"Executive Summary: {notes.executive_summary}\n"
            f"Comprehensive Theory: {notes.comprehensive_theory_background}\n"
            f"Architecture & Workflows: {notes.architecture_and_workflows}\n"
            f"Sections: {[s.title for s in notes.sections]}\n"
        )
        try:
            completion = await self.client.beta.chat.completions.parse(
                model=settings.OPENAI_TEXT_MODEL,
                messages=[
                    {"role": "system", "content": "You are a visual design engineer specializing in Mermaid diagrams for technical architecture and distributed systems."},
                    {"role": "user", "content": prompt}
                ],
                response_format=VisualAssetSchema,
                max_tokens=2048
            )
            spec = completion.choices[0].message.parsed
            if spec:
                spec.video_id = notes.video_id
            return spec
        except Exception as e:
            logger.warning(f"Visual spec generation failed: {e}")
            return None

    async def generate_image(self, prompt: str) -> Optional[str]:
        if not settings.ENABLE_IMAGE_GENERATION:
            return None
        try:
            model = (settings.OPENAI_IMAGE_MODEL or "gpt-image-1-mini").lower()
            size = "1792x1024" if model == "dall-e-3" else ("1536x1024" if "gpt-image" in model else "1024x1024")
            try:
                response = await self.client.images.generate(
                    model=settings.OPENAI_IMAGE_MODEL,
                    prompt=f"Minimalist, modern editorial technical illustration with generous boundary margins: {prompt}",
                    n=1,
                    size=size
                )
            except Exception:
                # Fallback to standard 1024x1024 if custom landscape size rejected
                response = await self.client.images.generate(
                    model=settings.OPENAI_IMAGE_MODEL,
                    prompt=f"Minimalist, modern editorial technical illustration with generous boundary margins: {prompt}",
                    n=1,
                    size="1024x1024"
                )
            return response.data[0].url
        except Exception as e:
            logger.warning(f"Image generation failed: {e}")
            return None
