from typing import List, Dict
from app.domain.enums import TranscriptStatus
from app.domain.schemas.transcript import TranscriptData, TranscriptSegment
from app.integrations.transcripts.provider import TranscriptProvider


class MockTranscriptProvider(TranscriptProvider):
    """
    Mock transcript provider that supplies high-quality, realistic technical transcripts
    with genuine start and end timestamps. Also reproduces edge cases (unavailable transcripts).
    """

    MOCK_TRANSCRIPTS: Dict[str, TranscriptData] = {
        "vid_dist_001": TranscriptData(
            video_id="vid_dist_001",
            language="en",
            source="verified_captions",
            status=TranscriptStatus.AVAILABLE,
            segments=[
                TranscriptSegment(
                    id="seg_0001",
                    start_seconds=12.5,
                    end_seconds=45.0,
                    text="Welcome to lecture one on distributed consensus. Today we analyze how replicated state machines maintain consistency across unreliable networks."
                ),
                TranscriptSegment(
                    id="seg_0002",
                    start_seconds=46.2,
                    end_seconds=115.8,
                    text="In any asynchronous network, network partitions and packet delays are inevitable. The classic FLP impossibility result proved that deterministic consensus is impossible in an asynchronous system with even a single unannounced failure."
                ),
                TranscriptSegment(
                    id="seg_0003",
                    start_seconds=118.0,
                    end_seconds=212.5,
                    text="To make practical progress, modern protocols like Raft and Multi-Paxos introduce partial synchrony and randomized election timeouts. Raft decomposes consensus into three independent sub-problems: Leader Election, Log Replication, and Safety."
                ),
                TranscriptSegment(
                    id="seg_0004",
                    start_seconds=215.0,
                    end_seconds=340.2,
                    text="Let's examine the Raft leader election phase. Every server starts in the Follower state. If a follower receives no heartbeat within its election timer—typically between 150 to 300 milliseconds—it transitions to Candidate and increments its term counter."
                ),
                TranscriptSegment(
                    id="seg_0005",
                    start_seconds=342.0,
                    end_seconds=490.6,
                    text="Once elected, the Leader accepts client commands, appends entries to its local log, and broadcasts AppendEntries RPCs. A log entry is committed only when it has been replicated to a strict quorum—a majority of servers, which is floor of N over 2 plus 1."
                ),
                TranscriptSegment(
                    id="seg_0006",
                    start_seconds=493.0,
                    end_seconds=680.0,
                    text="The critical safety property is the Leader Completeness property: if a log entry is committed in a given term, that entry will be present in the logs of the leaders for all higher-numbered terms. This prevents committed entries from ever being overwritten."
                ),
                TranscriptSegment(
                    id="seg_0007",
                    start_seconds=685.0,
                    end_seconds=850.4,
                    text="In production systems like etcd or CockroachDB, linearizable reads are guaranteed either by routing read requests through the leader's commit index using ReadIndex, or through leaseholder leases."
                )
            ]
        ),
        "vid_dist_002": TranscriptData(
            video_id="vid_dist_002",
            language="en",
            source="verified_captions",
            status=TranscriptStatus.AVAILABLE,
            segments=[
                TranscriptSegment(
                    id="seg_0001",
                    start_seconds=8.0,
                    end_seconds=62.4,
                    text="In this session, we investigate Event Sourcing combined with Command Query Responsibility Segregation, commonly known as CQRS."
                ),
                TranscriptSegment(
                    id="seg_0002",
                    start_seconds=65.0,
                    end_seconds=155.2,
                    text="Traditional CRUD architectures mutate row state in-place, losing temporal history and creating concurrency contention on hot database rows."
                ),
                TranscriptSegment(
                    id="seg_0003",
                    start_seconds=158.0,
                    end_seconds=295.0,
                    text="In Event Sourcing, every change is captured as an immutable domain event appended to an append-only event stream. The current state is derived by replaying the events from the beginning of time or from a periodic snapshot."
                ),
                TranscriptSegment(
                    id="seg_0004",
                    start_seconds=298.5,
                    end_seconds=460.0,
                    text="CQRS cleanly decouples the write model from the read model. Commands target the domain aggregate to enforce business invariants, while projection handlers consume events asynchronously to populate read-optimized Elasticsearch or PostgreSQL views."
                ),
                TranscriptSegment(
                    id="seg_0005",
                    start_seconds=465.0,
                    end_seconds=610.8,
                    text="Handling eventual consistency requires idempotent event handlers and tracking high-watermark consumer offsets to guarantee at-least-once delivery without duplicate state mutations."
                )
            ]
        ),
        "vid_dist_003": TranscriptData(
            video_id="vid_dist_003",
            language="en",
            source="youtube",
            status=TranscriptStatus.UNAVAILABLE,
            segments=[],
            error_message="Transcript is unavailable because the video is set to private or restricted access by the channel owner."
        ),
        "vid_dist_004": TranscriptData(
            video_id="vid_dist_004",
            language="en",
            source="verified_captions",
            status=TranscriptStatus.AVAILABLE,
            segments=[
                TranscriptSegment(
                    id="seg_0001",
                    start_seconds=10.0,
                    end_seconds=75.0,
                    text="Welcome back. Today we delve into the storage internals of Apache Kafka and how log-structured storage achieves tens of millions of events per second."
                ),
                TranscriptSegment(
                    id="seg_0002",
                    start_seconds=78.0,
                    end_seconds=190.4,
                    text="At its core, a Kafka topic partition is an append-only commit log on disk. Sequential disk I/O on modern SSDs and NVMe drives approaches theoretical memory bandwidth, completely avoiding random disk seeks."
                ),
                TranscriptSegment(
                    id="seg_0003",
                    start_seconds=194.0,
                    end_seconds=340.5,
                    text="Kafka leverages the operating system page cache rather than managing an in-process JVM buffer cache. When consumers read data, Kafka uses the sendfile system call for zero-copy data transfer directly from the OS page cache to the network socket."
                ),
                TranscriptSegment(
                    id="seg_0004",
                    start_seconds=345.0,
                    end_seconds=510.0,
                    text="Consumer groups coordinate partition assignments using group coordinators. If a consumer crashes, the group triggers a partition rebalance, recalculating ownership so remaining workers resume consuming from committed offsets."
                )
            ]
        )
    }

    async def get_transcript(self, video_id: str, language: str = "en") -> TranscriptData:
        if video_id in self.MOCK_TRANSCRIPTS:
            return self.MOCK_TRANSCRIPTS[video_id]

        # For any generic video ID, generate a structured technical transcript
        return TranscriptData(
            video_id=video_id,
            language=language,
            source="mock_technical_captions",
            status=TranscriptStatus.AVAILABLE,
            segments=[
                TranscriptSegment(
                    id="seg_0001",
                    start_seconds=15.0,
                    end_seconds=95.0,
                    text=f"Welcome to technical overview for lecture {video_id}. Today we dissect architecture, implementation trade-offs, and operational best practices."
                ),
                TranscriptSegment(
                    id="seg_0002",
                    start_seconds=98.0,
                    end_seconds=220.0,
                    text="First, consider the structural constraints of the system. We prioritize bounded latency, fault isolation, and deterministic recovery mechanisms."
                ),
                TranscriptSegment(
                    id="seg_0003",
                    start_seconds=225.0,
                    end_seconds=380.0,
                    text="When scaling across multiple nodes, idempotency keys and exponential backoff retry algorithms prevent cascade failures and retry storms."
                ),
                TranscriptSegment(
                    id="seg_0004",
                    start_seconds=385.0,
                    end_seconds=520.0,
                    text="In conclusion, benchmark your critical path under synthetic load and continuously monitor percentile latency (p99 and p99.9)."
                )
            ]
        )

