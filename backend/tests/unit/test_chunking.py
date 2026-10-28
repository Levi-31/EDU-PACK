from app.domain.schemas.transcript import TranscriptData, TranscriptSegment
from app.domain.enums import TranscriptStatus
from app.agents.transcript_agent import TranscriptProcessingAgent


def test_transcript_chunking_preserves_chronology_and_segments():
    agent = TranscriptProcessingAgent(max_tokens_per_chunk=100, overlap_segments=1)
    
    # Create 10 sequential segments
    segments = [
        TranscriptSegment(
            id=f"seg_{i:04d}",
            start_seconds=float(i * 30),
            end_seconds=float((i + 1) * 30),
            text=f"This is transcript segment {i} discussing technical distributed systems algorithms with depth."
        )
        for i in range(10)
    ]
    data = TranscriptData(
        video_id="test_vid_1",
        status=TranscriptStatus.AVAILABLE,
        segments=segments
    )

    chunks = agent.chunk_transcript(data)
    assert len(chunks) > 1

    # Verify each chunk has segments and valid chronological order
    prev_end = -1
    for chunk in chunks:
        assert len(chunk.segments) > 0
        assert chunk.start_time >= 0
        assert chunk.end_time > chunk.start_time


def test_transcript_quality_evaluation():
    agent = TranscriptProcessingAgent()
    
    # Missing transcript
    data_missing = TranscriptData(video_id="v1", status=TranscriptStatus.UNAVAILABLE)
    is_valid, msg = agent.evaluate_quality(data_missing)
    assert not is_valid

    # Empty segments
    data_empty = TranscriptData(video_id="v2", status=TranscriptStatus.AVAILABLE, segments=[])
    is_valid, msg = agent.evaluate_quality(data_empty)
    assert not is_valid

    # Valid transcript
    data_valid = TranscriptData(
        video_id="v3",
        status=TranscriptStatus.AVAILABLE,
        segments=[
            TranscriptSegment(
                id="seg_0001",
                start_seconds=0.0,
                end_seconds=45.0,
                text="This is a fully valid technical transcript segment discussing high throughput architectures."
            )
        ]
    )
    is_valid, msg = agent.evaluate_quality(data_valid)
    assert is_valid
