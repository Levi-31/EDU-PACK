import re
from typing import List, Optional
from app.domain.enums import TranscriptStatus
from app.domain.schemas.transcript import TranscriptData, TranscriptSegment


def parse_timestamp_to_seconds(ts_str: str) -> float:
    """Parses '00:01:23,456' (SRT) or '00:01:23.456' (VTT) to seconds"""
    clean = ts_str.strip().replace(",", ".")
    parts = clean.split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    return 0.0


class UserUploadTranscriptProvider:
    """Parses user-uploaded SRT, VTT, or timestamped TXT files into TranscriptData"""

    @classmethod
    def parse_srt_or_vtt(cls, video_id: str, content: str, language: str = "en") -> TranscriptData:
        lines = content.strip().splitlines()
        segments: List[TranscriptSegment] = []
        
        time_pattern = re.compile(r"(\d{1,2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}[,\.]\d{3})")
        
        current_id = 1
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            match = time_pattern.search(line)
            if match:
                start_sec = round(parse_timestamp_to_seconds(match.group(1)), 2)
                end_sec = round(parse_timestamp_to_seconds(match.group(2)), 2)
                text_lines = []
                i += 1
                while i < len(lines) and lines[i].strip() and not time_pattern.search(lines[i]):
                    # filter out pure digit sequence numbers
                    if not lines[i].strip().isdigit():
                        text_lines.append(lines[i].strip())
                    i += 1
                text = " ".join(text_lines)
                if text:
                    segments.append(
                        TranscriptSegment(
                            id=f"seg_{current_id:04d}",
                            start_seconds=start_sec,
                            end_seconds=end_sec,
                            text=text
                        )
                    )
                    current_id += 1
            else:
                i += 1

        if not segments:
            # Fallback: Treat as plain text without timestamps
            plain_text = content.strip()
            if plain_text:
                return TranscriptData(
                    video_id=video_id,
                    language=language,
                    source="user_upload_txt",
                    status=TranscriptStatus.USER_PROVIDED,
                    segments=[
                        TranscriptSegment(
                            id="seg_0001",
                            start_seconds=0.0,
                            end_seconds=60.0,
                            text=plain_text[:5000]
                        )
                    ],
                    raw_text=plain_text
                )
            return TranscriptData(
                video_id=video_id,
                language=language,
                source="user_upload",
                status=TranscriptStatus.FAILED,
                error_message="Uploaded transcript file contained no readable text or timestamps."
            )

        return TranscriptData(
            video_id=video_id,
            language=language,
            source="user_upload_srt_vtt",
            status=TranscriptStatus.USER_PROVIDED,
            segments=segments
        )

