from abc import ABC, abstractmethod
from typing import Optional
from app.domain.schemas.transcript import TranscriptData


class TranscriptProvider(ABC):
    @abstractmethod
    async def get_transcript(self, video_id: str, language: str = "en") -> TranscriptData:
        """
        Retrieves transcript segments and metadata for a video.
        Must return TranscriptData with accurate status:
        - AVAILABLE with segments
        - UNAVAILABLE / DISABLED / FAILED with explanatory error_message
        Never fabricates segments.
        """
        pass
