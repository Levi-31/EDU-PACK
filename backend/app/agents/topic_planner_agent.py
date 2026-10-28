import logging
from typing import Optional
from app.domain.schemas.topic_plan import VideoTopicPlan, PlannedTopic
from app.domain.schemas.transcript import TranscriptData
from app.integrations.openai.client import OpenAIClientInterface

logger = logging.getLogger(__name__)


class TopicPlannerAgent:
    """
    Curriculum planner agent. Decomposes video transcripts into structured topics,
    learning objectives, theoretical prerequisite gaps, and targeted research queries.
    """

    def __init__(self, llm_client: OpenAIClientInterface):
        self.llm = llm_client

    async def plan_topics_for_video(
        self,
        video_metadata: dict,
        transcript: TranscriptData
    ) -> VideoTopicPlan:
        try:
            transcript_text = transcript.get_text()
            plan = await self.llm.generate_topic_plan(
                video_metadata=video_metadata,
                transcript_text=transcript_text
            )
            return plan
        except Exception as e:
            logger.warning(
                "Topic planning failed for '%s' (%s), using sensible fallback: %s",
                video_metadata.get("title", ""),
                video_metadata.get("video_id", ""),
                e
            )
            vid = video_metadata.get("video_id", "")
            title = video_metadata.get("title", "Technical Lecture")
            return VideoTopicPlan(
                video_id=vid,
                video_title=title,
                overall_subject="Systems Engineering & Cloud Computing",
                audience_level="Intermediate",
                planned_topics=[
                    PlannedTopic(
                        topic_id="topic_1",
                        title=f"Core Concepts of {title}",
                        summary="Foundational explanations and principles covered in this lecture.",
                        learning_objectives=[f"Understand the mechanics and purpose of {title}"],
                        prerequisites=["Basic engineering fundamentals"],
                        theoretical_depth_needed="medium",
                        research_queries=[f"{title} architecture overview", f"{title} best practices"]
                    )
                ],
                global_research_queries=[f"{title} official documentation"]
            )

