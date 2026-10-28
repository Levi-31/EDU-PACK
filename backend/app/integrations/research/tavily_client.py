import logging
import re
from urllib.parse import urlparse
from typing import List
import httpx

from app.integrations.research.base import BaseResearchProvider
from app.domain.schemas.research import ResearchSource

logger = logging.getLogger(__name__)


class TavilyResearchProvider(BaseResearchProvider):
    def __init__(self, api_key: str, search_depth: str = "advanced", timeout_seconds: float = 15.0):
        self.api_key = api_key
        self.search_depth = search_depth
        self.timeout_seconds = timeout_seconds
        self.api_url = "https://api.tavily.com/search"

    def _sanitize_snippet(self, text: str) -> str:
        """Sanitize web text against prompt injection markers or malicious formatting."""
        if not text:
            return ""
        # Remove null bytes and carriage returns
        text = text.replace("\x00", "").replace("\r", " ")
        # Strip potential prompt jailbreak tags
        text = re.sub(r"<\/?(system|assistant|user|prompt|context|instructions)[^>]*>", "", text, flags=re.IGNORECASE)
        # Collapse excessive whitespace
        text = re.sub(r"\s+", " ", text).strip()
        # Cap length to 1000 chars per snippet for context efficiency
        return text[:1000]

    async def search(self, query: str, max_results: int = 5) -> List[ResearchSource]:
        if not self.api_key or not query.strip():
            return []

        payload = {
            "api_key": self.api_key,
            "query": query.strip(),
            "search_depth": self.search_depth,
            "include_answer": False,
            "max_results": min(max_results, 10),
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(self.api_url, json=payload)
                if response.status_code != 200:
                    logger.warning(
                        "Tavily search API returned status %s: %s",
                        response.status_code,
                        response.text[:200]
                    )
                    return []

                data = response.json()
                raw_results = data.get("results", [])
                sources: List[ResearchSource] = []

                for item in raw_results:
                    url = item.get("url", "")
                    title = item.get("title", "Reference Source")
                    raw_content = item.get("content", "") or item.get("snippet", "")
                    cleaned_snippet = self._sanitize_snippet(raw_content)

                    domain = ""
                    if url:
                        try:
                            domain = urlparse(url).netloc.lower()
                        except Exception:
                            domain = ""

                    sources.append(
                        ResearchSource(
                            title=title,
                            url=url,
                            domain=domain,
                            snippet=cleaned_snippet,
                            relevance_summary=f"External documentation retrieved for query: '{query}'",
                            score=float(item.get("score", 0.0)) if item.get("score") is not None else None,
                        )
                    )

                logger.info("Tavily search for '%s' returned %d sources", query, len(sources))
                return sources

        except Exception as exc:
            logger.error("Failed to query Tavily API for '%s': %s", query, exc)
            return []

