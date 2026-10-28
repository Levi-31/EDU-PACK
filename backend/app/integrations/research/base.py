from abc import ABC, abstractmethod
from typing import List
from app.domain.schemas.research import ResearchSource


class BaseResearchProvider(ABC):
    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> List[ResearchSource]:
        """Perform authoritative web search and return structured research sources."""
        pass

