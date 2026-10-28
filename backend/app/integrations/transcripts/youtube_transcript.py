import logging
from typing import List
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
from app.domain.enums import TranscriptStatus
from app.domain.schemas.transcript import TranscriptData, TranscriptSegment
from app.integrations.transcripts.provider import TranscriptProvider

logger = logging.getLogger(__name__)


class YouTubeTranscriptProvider(TranscriptProvider):
    async def get_transcript(self, video_id: str, language: str = "en") -> TranscriptData:
        try:
            # Check available transcript list
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # 1. Try to find preferred manually created transcript
            transcript = None
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

            # 3. Fallback to any available transcript and translate if needed
            if not transcript:
                try:
                    for t in transcript_list:
                        transcript = t
                        source_label = f"fallback_{t.language_code}"
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

            # Fetch actual raw snippet list
            raw_snippets = transcript.fetch()
            segments: List[TranscriptSegment] = []

            for idx, item in enumerate(raw_snippets):
                start = float(item.get("start", 0.0))
                duration = float(item.get("duration", 0.0))
                end = round(start + duration, 2)
                text = item.get("text", "").strip()
                if not text:
                    continue

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
                    language=transcript.language_code,
                    source=source_label,
                    status=TranscriptStatus.UNAVAILABLE,
                    error_message="Transcript segments list was empty."
                )

            return TranscriptData(
                video_id=video_id,
                language=transcript.language_code,
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
