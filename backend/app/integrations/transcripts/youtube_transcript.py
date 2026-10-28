import logging
from typing import List, Any
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
from app.domain.enums import TranscriptStatus
from app.domain.schemas.transcript import TranscriptData, TranscriptSegment
from app.integrations.transcripts.provider import TranscriptProvider

logger = logging.getLogger(__name__)


class YouTubeTranscriptProvider(TranscriptProvider):
    async def get_transcript(self, video_id: str, language: str = "en") -> TranscriptData:
        try:
            api = YouTubeTranscriptApi()
            
            # Compatible with both youtube-transcript-api 1.x (instance method) and legacy 0.6.x (class method)
            if hasattr(api, "list"):
                transcript_list = api.list(video_id)
            elif hasattr(YouTubeTranscriptApi, "list_transcripts"):
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            else:
                transcript_list = YouTubeTranscriptApi.list(video_id)

            transcript = None
            source_label = "captions"

            # 1. Try manually created transcript in requested language or english
            try:
                transcript = transcript_list.find_manually_created_transcript([language, "en"])
                source_label = "manual_captions"
            except Exception:
                pass

            # 2. Try generated transcript
            if not transcript:
                try:
                    transcript = transcript_list.find_generated_transcript([language, "en"])
                    source_label = "auto_generated_captions"
                except Exception:
                    pass

            # 3. Try find_transcript
            if not transcript and hasattr(transcript_list, "find_transcript"):
                try:
                    transcript = transcript_list.find_transcript([language, "en"])
                    source_label = "captions"
                except Exception:
                    pass

            # 4. Fallback: Take the first available transcript
            if not transcript:
                try:
                    for t in transcript_list:
                        transcript = t
                        source_label = f"captions_{getattr(t, 'language_code', 'unknown')}"
                        break
                except Exception:
                    pass

            if not transcript:
                return TranscriptData(
                    video_id=video_id,
                    language=language,
                    source="youtube",
                    status=TranscriptStatus.UNAVAILABLE,
                    error_message=f"No accessible transcript found for video {video_id} in requested language '{language}'."
                )

            raw_snippets = transcript.fetch()
            segments: List[TranscriptSegment] = []

            for idx, item in enumerate(raw_snippets):
                # Support both FetchedTranscriptSnippet object and legacy dict
                if hasattr(item, "text"):
                    text = str(getattr(item, "text", "")).strip()
                    start = float(getattr(item, "start", 0.0))
                    duration = float(getattr(item, "duration", 0.0))
                elif isinstance(item, dict):
                    text = str(item.get("text", "")).strip()
                    start = float(item.get("start", 0.0))
                    duration = float(item.get("duration", 0.0))
                else:
                    continue

                if not text:
                    continue

                end = round(start + duration, 2)
                segments.append(
                    TranscriptSegment(
                        id=f"seg_{idx + 1:04d}",
                        start_seconds=round(start, 2),
                        end_seconds=end,
                        text=text
                    )
                )

            if not segments:
                return TranscriptData(
                    video_id=video_id,
                    language=getattr(transcript, "language_code", language),
                    source=source_label,
                    status=TranscriptStatus.UNAVAILABLE,
                    error_message="Transcript segments list was empty."
                )

            return TranscriptData(
                video_id=video_id,
                language=getattr(transcript, "language_code", language),
                source=source_label,
                status=TranscriptStatus.AVAILABLE,
                segments=segments
            )

        except TranscriptsDisabled:
            return TranscriptData(
                video_id=video_id,
                language=language,
                source="youtube",
                status=TranscriptStatus.DISABLED,
                error_message="Transcripts are disabled by the video owner."
            )
        except (NoTranscriptFound, VideoUnavailable) as e:
            return TranscriptData(
                video_id=video_id,
                language=language,
                source="youtube",
                status=TranscriptStatus.UNAVAILABLE,
                error_message=f"Video or transcript unavailable: {str(e)}"
            )
        except Exception as e:
            logger.warning(f"Failed to fetch transcript for {video_id}: {e}")
            return TranscriptData(
                video_id=video_id,
                language=language,
                source="youtube",
                status=TranscriptStatus.FAILED,
                error_message=f"Transcript extraction failed: {str(e)}"
            )
