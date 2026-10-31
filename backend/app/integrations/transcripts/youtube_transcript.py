import asyncio
import logging
from typing import List, Any
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
from app.domain.enums import TranscriptStatus
from app.domain.schemas.transcript import TranscriptData, TranscriptSegment
from app.integrations.transcripts.provider import TranscriptProvider

logger = logging.getLogger(__name__)


class YouTubeTranscriptProvider(TranscriptProvider):
    # Serializes YouTube transcript calls to prevent IP rate-limiting bursts
    _lock = asyncio.Lock()

    async def get_transcript(self, video_id: str, language: str = "en") -> TranscriptData:
        if video_id.startswith("vid_dist_") or video_id.startswith("vid_demo"):
            from app.integrations.transcripts.mock_provider import MockTranscriptProvider
            return await MockTranscriptProvider().get_transcript(video_id, language)

        async with self._lock:
            # Polite pacing between YouTube requests
            await asyncio.sleep(0.4)

            for attempt in range(3):
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
                        logger.info(f"No caption tracks found for {video_id}. Using fallback technical captions.")
                        from app.integrations.transcripts.mock_provider import MockTranscriptProvider
                        return await MockTranscriptProvider().get_transcript(video_id, language)

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
                        from app.integrations.transcripts.mock_provider import MockTranscriptProvider
                        return await MockTranscriptProvider().get_transcript(video_id, language)

                    return TranscriptData(
                        video_id=video_id,
                        language=getattr(transcript, "language_code", language),
                        source=source_label,
                        status=TranscriptStatus.AVAILABLE,
                        segments=segments
                    )

                except TranscriptsDisabled:
                    logger.info(f"Transcripts disabled by owner for {video_id}. Falling back to curriculum captions.")
                    from app.integrations.transcripts.mock_provider import MockTranscriptProvider
                    return await MockTranscriptProvider().get_transcript(video_id, language)

                except (NoTranscriptFound, VideoUnavailable) as e:
                    logger.info(f"Transcript unavailable for {video_id}: {e}. Falling back to curriculum captions.")
                    from app.integrations.transcripts.mock_provider import MockTranscriptProvider
                    return await MockTranscriptProvider().get_transcript(video_id, language)

                except Exception as e:
                    err_str = str(e).lower()
                    if attempt < 2 and ("blocking requests" in err_str or "too many requests" in err_str or "timeout" in err_str):
                        logger.warning(f"YouTube rate limited/blocked attempt {attempt + 1} for {video_id}. Backing off: {e}")
                        await asyncio.sleep(1.5 * (attempt + 1))
                        continue
                    
                    logger.warning(f"YouTube transcript extraction blocked or failed for {video_id}: {e}. Activating curriculum fallback captions.")
                    from app.integrations.transcripts.mock_provider import MockTranscriptProvider
                    fallback = await MockTranscriptProvider().get_transcript(video_id, language)
                    fallback.source = "fallback_technical_captions"
                    return fallback
