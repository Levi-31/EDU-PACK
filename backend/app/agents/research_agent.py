import asyncio
import logging
from typing import List, Dict, Set
from urllib.parse import urlparse

from app.domain.schemas.topic_plan import VideoTopicPlan
from app.domain.schemas.research import VideoResearchBundle, ResearchSource, TopicResearchResult
from app.integrations.research.base import BaseResearchProvider

logger = logging.getLogger(__name__)


class ResearchTheoryAgent:
    """
    Autonomous research agent that retrieves authoritative external documentation,
    specifications, and foundational theoretical context via search providers (Tavily).
    Deduplicates results, synthesizes findings, and respects concurrency limits.
    """

    def __init__(self, research_provider: BaseResearchProvider, max_queries_per_video: int = 3, max_parallel: int = 3):
        self.provider = research_provider
        self.max_queries_per_video = max_queries_per_video
        self.max_parallel = max_parallel

    async def research_for_video(
        self,
        video_metadata: dict,
        topic_plan: VideoTopicPlan,
        enable_research: bool = True
    ) -> VideoResearchBundle:
        vid = video_metadata.get("video_id", "")
        if not enable_research:
            return VideoResearchBundle(video_id=vid)

        # Collect queries from topic plan (prioritize topic queries + global queries)
        queries: List[tuple[str, str]] = []  # (topic_id, query)
        for topic in topic_plan.planned_topics:
            for q in topic.research_queries[:1]:
                if q and (topic.topic_id, q) not in queries:
                    queries.append((topic.topic_id, q))

        for gq in topic_plan.global_research_queries:
            if gq and ("global", gq) not in queries:
                queries.append(("global", gq))

        # Enforce max queries per video limit
        selected_queries = queries[:self.max_queries_per_video]
        if not selected_queries:
            # Fallback query if plan had none
            fallback_query = f"{video_metadata.get('title', '')} architecture documentation"
            selected_queries = [("global", fallback_query)]

        logger.info(
            "Executing research for video '%s' (%s) with %d queries",
            video_metadata.get("title", ""),
            vid,
            len(selected_queries)
        )

        semaphore = asyncio.Semaphore(self.max_parallel)
        seen_urls: Set[str] = set()
        all_sources: List[ResearchSource] = []
        topic_results: List[TopicResearchResult] = []

        async def execute_query(topic_id: str, query: str):
            async with semaphore:
                try:
                    sources = await self.provider.search(query=query, max_results=3)
                    unique_sources: List[ResearchSource] = []
                    for s in sources:
                        if s.url and s.url not in seen_urls:
                            seen_urls.add(s.url)
                            unique_sources.append(s)
                            all_sources.append(s)

                    topic_results.append(
                        TopicResearchResult(
                            topic_id=topic_id,
                            query=query,
                            sources=unique_sources,
                            key_findings=[s.snippet[:150] for s in unique_sources if s.snippet]
                        )
                    )
                except Exception as e:
                    logger.warning("Research query '%s' failed: %s", query, e)

        tasks = [execute_query(tid, q) for tid, q in selected_queries]
        await asyncio.gather(*tasks)

        logger.info("Research complete for video '%s': %d unique sources found", vid, len(all_sources))
        return VideoResearchBundle(
            video_id=vid,
            queries_executed=[q for _, q in selected_queries],
            sources=all_sources,
            topic_results=topic_results,
            enrichment_notes=f"Retrieved {len(all_sources)} authoritative sources across {len(selected_queries)} targeted queries."
        )

