import logging
from app.core.config import Settings
from app.integrations.research.base import BaseResearchProvider
from app.integrations.research.tavily_client import TavilyResearchProvider
from app.integrations.research.mock_research import MockResearchProvider

logger = logging.getLogger(__name__)


def get_research_provider(settings: Settings) -> BaseResearchProvider:
    """Factory returning TavilyResearchProvider if configured, otherwise MockResearchProvider."""
    if not settings.ENABLE_WEB_RESEARCH:
        logger.info("Web research disabled via configuration; using MockResearchProvider.")
        return MockResearchProvider()

    if settings.TAVILY_API_KEY and settings.TAVILY_API_KEY.strip() and not settings.DEMO_MODE:
        logger.info("Initializing live TavilyResearchProvider.")
        return TavilyResearchProvider(
            api_key=settings.TAVILY_API_KEY.strip(),
            search_depth=settings.TAVILY_SEARCH_DEPTH,
        )

    logger.info("DEMO_MODE is True or TAVILY_API_KEY not configured; using high-fidelity MockResearchProvider.")
    return MockResearchProvider()

