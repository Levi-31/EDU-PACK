import asyncio
from typing import Optional
from app.domain.enums import VisualType
from app.domain.schemas.notes import (
    StructuredVideoNotes,
    NoteTopicSection,
    CodeSnippet,
    CalloutBox,
    Flashcard,
    GlossaryItem,
    ReviewReport
)
from app.domain.schemas.visual import VisualAssetSchema
from app.integrations.openai.client import OpenAIClientInterface


class MockOpenAIClient(OpenAIClientInterface):
    """
    Deterministic mock OpenAI client for demo mode and automated testing.
    Generates rich, schema-compliant technical notes with valid Mermaid diagrams,
    real code snippets, and review checks without external API keys.
    """

    async def generate_structured_notes(
        self,
        video_metadata: dict,
        transcript_text: str,
        evidence_segments: list,
        detail_level: str = "standard"
    ) -> StructuredVideoNotes:
        # Simulate slight processing latency for realistic async feel
        await asyncio.sleep(0.3)
        vid = video_metadata.get("video_id", "vid_demo")
        title = video_metadata.get("title", "Technical Computing Overview")
        video_url = video_metadata.get("video_url", f"https://www.youtube.com/watch?v={vid}")
        
        # Build segment IDs from evidence
        seg_ids = [s["id"] for s in evidence_segments] if evidence_segments else ["seg_0001"]
        seg_0 = seg_ids[0] if seg_ids else "seg_0001"
        seg_1 = seg_ids[min(1, len(seg_ids)-1)]
        seg_2 = seg_ids[min(2, len(seg_ids)-1)]
        seg_3 = seg_ids[min(3, len(seg_ids)-1)]

        if "vid_dist_001" in vid or "consensus" in title.lower():
            return StructuredVideoNotes(
                schema_version="1.0",
                video_id=vid,
                video_title=title,
                video_url=video_url,
                channel_name=video_metadata.get("channel_title", "MIT Distributed Systems Lab"),
                duration_seconds=video_metadata.get("duration_seconds", 1245),
                thumbnail_url=video_metadata.get("thumbnail_url"),
                original_position=video_metadata.get("original_position", 0),
                is_mock=True,
                executive_summary=(
                    "[DEMO MODE / MOCK GENERATED NOTES] This lecture dissects the fundamental mechanics of distributed consensus, "
                    "replicated state machines, and the formal trade-offs between Paxos and Raft. It explains how leader election, "
                    "quorum writes, and log commitment guarantees linearizable consistency under arbitrary network partitions."
                ),
                key_takeaways=[
                    "FLP Impossibility theorem dictates that asynchronous networks cannot guarantee deterministic consensus with unannounced crash failures.",
                    "Raft achieves practical consensus by breaking the state machine into 3 modular sub-problems: Leader Election, Log Replication, and Safety invariants.",
                    "A log entry is committed only when replicated to a strict majority quorum: floor(N/2) + 1 nodes.",
                    "The Leader Completeness Property prevents committed entries from ever being overwritten by succeeding term leaders."
                ],
                learning_objectives=[
                    "Analyze quorum slices and split-brain prevention under network partitions.",
                    "Trace Raft RPC workflows (RequestVote and AppendEntries) across server term transitions.",
                    "Implement linearizable read optimizations using ReadIndex and leaseholder leases."
                ],
                prerequisites=["Basic networking (TCP/IP socket semantics)", "Fundamentals of concurrency and write-ahead logs"],
                core_concepts=["Replicated State Machines", "Quorum Majority", "Term Numbers", "AppendEntries RPC", "Split-Brain Prevention"],
                sections=[
                    NoteTopicSection(
                        title="1. Foundations of Consensus and the FLP Theorem",
                        markdown_content=(
                            "Distributed consensus is the problem of reaching agreement on a shared state value across a cluster of independent machines "
                            "communicating over an unreliable, packet-dropping network. Fischer, Lynch, and Paterson (FLP) established that in a strictly "
                            "asynchronous model, no deterministic algorithm can guarantee both safety and liveness if even one node can crash."
                        ),
                        callouts=[
                            CalloutBox(
                                kind="important",
                                title="Safety vs. Liveness",
                                content="Safety ensures 'nothing bad happens' (no split-brain or duplicate leaders). Liveness ensures 'something good eventually happens' (progress is made)."
                            )
                        ],
                        evidence_segment_ids=[seg_0, seg_1],
                        timestamp_seconds=12.5,
                        timestamped_watch_url=f"{video_url}&t=12s"
                    ),
                    NoteTopicSection(
                        title="2. Raft Leader Election and Randomized Heartbeats",
                        markdown_content=(
                            "Raft nodes exist in one of three states: Follower, Candidate, or Leader. When follower election timeouts expire "
                            "without receiving heartbeats, the node increments its current term, votes for itself, and broadcasts RequestVote RPCs. "
                            "Randomized election timers (e.g., 150ms–300ms) prevent split-vote deadlocks."
                        ),
                        code_snippets=[
                            CodeSnippet(
                                language="python",
                                code=(
                                    "def handle_election_timeout(self):\n"
                                    "    self.current_term += 1\n"
                                    "    self.state = 'CANDIDATE'\n"
                                    "    self.voted_for = self.node_id\n"
                                    "    votes = 1\n"
                                    "    for peer in self.peers:\n"
                                    "        if self.send_request_vote(peer, self.current_term):\n"
                                    "            votes += 1\n"
                                    "    if votes > len(self.peers) // 2:\n"
                                    "        self.state = 'LEADER'\n"
                                    "        self.start_heartbeat_loop()"
                                ),
                                caption="Simplified Raft candidate transition and quorum election check."
                            )
                        ],
                        evidence_segment_ids=[seg_2],
                        timestamp_seconds=215.0,
                        timestamped_watch_url=f"{video_url}&t=215s"
                    ),
                    NoteTopicSection(
                        title="3. Log Replication and Strict Quorum Commitment",
                        markdown_content=(
                            "Once elected, the leader appends client proposals to its log and issues `AppendEntries` RPCs to all peers. "
                            "Each entry contains a term index and an monotonically increasing log index. Once a majority acknowledges "
                            "the entry, the leader advances its `commitIndex` and executes the command against the state machine."
                        ),
                        evidence_segment_ids=[seg_3],
                        timestamp_seconds=342.0,
                        timestamped_watch_url=f"{video_url}&t=342s"
                    )
                ],
                architecture_and_workflows=(
                    "Client -> Leader Node (Append log) -> AppendEntries RPC -> Follower Quorum (Ack) -> Commit Index Advance -> State Machine Execution -> Response to Client."
                ),
                trade_offs_and_decisions=[
                    "Paxos vs. Raft: Paxos has minimal symmetric message complexity but extreme implementation opacity; Raft prioritizes formal understandability and explicit leader leases.",
                    "In-memory vs. Disk fsync: Strict durable logging requires disk fsync on every log append, bounding throughput by NVMe write latency."
                ],
                pitfalls_and_limitations=[
                    "Split-brain occurrence when minority partition leaders attempt uncoordinated writes.",
                    "Slow follower lag inducing cascade memory pressure if leader holds large in-flight log queues."
                ],
                glossary=[
                    GlossaryItem(term="Quorum", definition="A subset of nodes comprising a strict majority (N/2 + 1) required to establish consensus."),
                    GlossaryItem(term="Split-Brain", definition="A catastrophic failure state where two nodes simultaneously believe they are the legitimate leader.")
                ],
                revision_sheet=(
                    "1. Always require odd cluster sizes (3, 5, 7) to avoid split votes.\n"
                    "2. Quorum size formula: Q = floor(N / 2) + 1.\n"
                    "3. Leaders never overwrite or truncate their own entries; they only overwrite out-of-date follower entries."
                ),
                flashcards=[
                    Flashcard(question="What guarantees that committed entries are never lost across term elections?", answer="The Leader Completeness Property: candidates must possess all committed entries to win votes."),
                    Flashcard(question="Why are Raft election timeouts randomized?", answer="To minimize the probability of split-vote ties among concurrent candidates.")
                ],
                review_report=ReviewReport(
                    status="APPROVED",
                    groundedness_score=1.0,
                    findings=["All claims verified against transcript timestamps", "Code snippet is marked as pedagogical illustration", "No hallucinated concepts detected"]
                )
            )

        elif "vid_dist_002" in vid or "event" in title.lower():
            return StructuredVideoNotes(
                schema_version="1.0",
                video_id=vid,
                video_title=title,
                video_url=video_url,
                channel_name=video_metadata.get("channel_title", "MIT Distributed Systems Lab"),
                duration_seconds=video_metadata.get("duration_seconds", 1560),
                thumbnail_url=video_metadata.get("thumbnail_url"),
                original_position=video_metadata.get("original_position", 1),
                is_mock=True,
                executive_summary=(
                    "[DEMO MODE / MOCK GENERATED NOTES] An engineering guide to Event Sourcing and Command Query Responsibility Segregation (CQRS). "
                    "Explores how append-only immutable event streams eliminate database lock contention, enable auditability, "
                    "and feed asynchronously projected read models for sub-millisecond query performance."
                ),
                key_takeaways=[
                    "Event Sourcing treats state as a sequence of immutable facts rather than ephemeral mutable database rows.",
                    "CQRS separates the write model (optimizing business invariant enforcement) from read models (optimizing query performance).",
                    "Snapshots prevent replay degradation for long-lived domain aggregates.",
                    "Consumer idempotency is non-negotiable when dealing with at-least-once message delivery."
                ],
                learning_objectives=[
                    "Design immutable domain event schemas with semantic versioning.",
                    "Structure write aggregates to guarantee zero mutation concurrency conflicts.",
                    "Build asynchronous projection workers with idempotent deduplication."
                ],
                prerequisites=["Relational database ACID guarantees", "Message broker semantics (at-least-once delivery)"],
                core_concepts=["Append-only Event Store", "Aggregate Root", "Projection Pipeline", "Eventual Consistency", "Idempotency Keys"],
                sections=[
                    NoteTopicSection(
                        title="1. The Flaws of In-Place Row Mutation",
                        markdown_content=(
                            "Traditional CRUD operations perform in-place `UPDATE` statements, destroying the temporal history of how the system arrived "
                            "at that state. In high-concurrency transactional systems, row-level locks on hot balances cause thread starvation and deadlocks."
                        ),
                        evidence_segment_ids=[seg_0, seg_1],
                        timestamp_seconds=8.0,
                        timestamped_watch_url=f"{video_url}&t=8s"
                    ),
                    NoteTopicSection(
                        title="2. Event Store Internals and Aggregate Hydration",
                        markdown_content=(
                            "In Event Sourcing, the database is an append-only log of events (`AccountCreated`, `MoneyDeposited`, `TransferExecuted`). "
                            "To process a new command, the aggregate is 'hydrated' by applying historical events in order."
                        ),
                        code_snippets=[
                            CodeSnippet(
                                language="python",
                                code=(
                                    "class BankAccountAggregate:\n"
                                    "    def __init__(self):\n"
                                    "        self.balance = 0\n"
                                    "        self.version = 0\n\n"
                                    "    def apply_event(self, event):\n"
                                    "        if event.name == 'Deposited':\n"
                                    "            self.balance += event.amount\n"
                                    "        elif event.name == 'Withdrawn':\n"
                                    "            self.balance -= event.amount\n"
                                    "        self.version += 1"
                                ),
                                caption="Aggregate hydration through sequential event application."
                            )
                        ],
                        evidence_segment_ids=[seg_2],
                        timestamp_seconds=158.0,
                        timestamped_watch_url=f"{video_url}&t=158s"
                    )
                ],
                architecture_and_workflows="Command -> Aggregate Command Handler -> Append Events -> Outbox Broker -> Projection Worker -> Read DB.",
                trade_offs_and_decisions=[
                    "Event Sourcing provides full auditability and time-travel debugging at the expense of eventual consistency latency and schema migration complexity."
                ],
                pitfalls_and_limitations=[
                    "Unversioned event payloads causing serialization failure on schema evolution.",
                    "Slow aggregate hydration on un-snapshotted entities exceeding 10,000 events."
                ],
                glossary=[
                    GlossaryItem(term="Aggregate", definition="A cluster of associated objects treated as a single unit for data changes and invariant enforcement."),
                    GlossaryItem(term="Projection", definition="A read-optimized denormalized view derived from listening to event streams.")
                ],
                revision_sheet="Events are past-tense immutable facts. Commands can be rejected; events cannot.",
                flashcards=[
                    Flashcard(question="How does Event Sourcing handle high volume queries?", answer="Through CQRS read projections tailored to specific UI query patterns.")
                ],
                review_report=ReviewReport(status="APPROVED", groundedness_score=1.0)
            )

        # Default generic mock note
        return StructuredVideoNotes(
            schema_version="1.0",
            video_id=vid,
            video_title=title,
            video_url=video_url,
            channel_name=video_metadata.get("channel_title", "Technical Academy"),
            duration_seconds=video_metadata.get("duration_seconds", 900),
            thumbnail_url=video_metadata.get("thumbnail_url"),
            original_position=video_metadata.get("original_position", 0),
            is_mock=True,
            executive_summary=(
                f"[DEMO MODE / MOCK GENERATED NOTES] A comprehensive technical summary of '{title}'. "
                "Covers fundamental principles, systems implementation, performance considerations, and architectural decisions."
            ),
            key_takeaways=[
                "Explicit interface boundaries reduce coupling in large scale systems.",
                "Idempotency keys and deterministic error recovery are essential for distributed fault tolerance.",
                "Continuous observability with p99 latency metrics isolates operational regressions."
            ],
            learning_objectives=[
                f"Master core concepts presented in {title}.",
                "Evaluate architectural trade-offs under real-world constraints."
            ],
            prerequisites=["Familiarity with modern software engineering practices"],
            core_concepts=["System Design", "Fault Isolation", "Scalability", "Telemetry"],
            sections=[
                NoteTopicSection(
                    title="1. Core Principles and Architectural Design",
                    markdown_content=(
                        f"In this section of '{title}', the foundational design principles are analyzed. "
                        "We examine how separating concerns into discrete modular components improves testability and resilience."
                    ),
                    evidence_segment_ids=[seg_0],
                    timestamp_seconds=15.0,
                    timestamped_watch_url=f"{video_url}&t=15s"
                ),
                NoteTopicSection(
                    title="2. Implementation Mechanics & Trade-offs",
                    markdown_content=(
                        "Practical implementation requires navigating operational trade-offs between memory footprint, "
                        "CPU utilization, and network round-trips."
                    ),
                    evidence_segment_ids=[seg_1],
                    timestamp_seconds=98.0,
                    timestamped_watch_url=f"{video_url}&t=98s"
                )
            ],
            architecture_and_workflows="Input Request -> Validation Pipeline -> Business Logic Engine -> Persistence Layer -> Observability Sink",
            trade_offs_and_decisions=["Throughput vs Latency: Batching increases bulk throughput at the cost of p50 latency."],
            pitfalls_and_limitations=["Unbounded queues risking Out-Of-Memory crashes under unexpected ingress spikes."],
            glossary=[GlossaryItem(term="Fault Tolerance", definition="The ability of a system to continue operating properly in the event of failure of some components.")],
            revision_sheet="Design for failure: enforce circuit breakers, timeouts, and structured error handling.",
            flashcards=[Flashcard(question="What is the primary trade-off of queue batching?", answer="Higher throughput at the expense of individual message latency.")],
            review_report=ReviewReport(status="APPROVED", groundedness_score=1.0)
        )

    async def review_notes(self, notes: StructuredVideoNotes, transcript_text: str) -> ReviewReport:
        await asyncio.sleep(0.1)
        return ReviewReport(
            status="APPROVED",
            groundedness_score=1.0,
            findings=[
                "All section titles and concepts match transcript technical scope.",
                "Timestamp references verified against transcript segments.",
                "Pedagogical examples accurately separated from source transcript facts."
            ],
            revisions_applied=0
        )

    async def generate_visual_spec(self, notes: StructuredVideoNotes) -> Optional[VisualAssetSchema]:
        await asyncio.sleep(0.1)
        if "consensus" in notes.video_title.lower() or "vid_dist_001" in notes.video_id:
            mermaid = (
                "graph TD\n"
                "    subgraph Raft Cluster\n"
                "        L[Leader Node - Term 2] -->|AppendEntries RPC| F1[Follower 1 - Term 2]\n"
                "        L -->|AppendEntries RPC| F2[Follower 2 - Term 2]\n"
                "        L -.->|Network Partition| F3[Follower 3 - Isolated]\n"
                "    end\n"
                "    C[Client Command] -->|Write Proposal| L\n"
                "    F1 -->|Quorum Ack 2/3| L\n"
                "    L -->|Commit Index++| SM[State Machine]"
            )
            return VisualAssetSchema(
                video_id=notes.video_id,
                section_index=1,
                asset_type=VisualType.MERMAID_ARCHITECTURE,
                title="Raft Cluster Leader Election and Quorum Replication",
                description="Architecture diagram showing leader quorum broadcast and partition fault tolerance.",
                mermaid_code=mermaid,
                mime_type="image/svg+xml",
                is_generated=True,
                decision_reason="Visual diagram strongly clarifies leader-follower quorum communication and split-brain isolation."
            )
        elif "event" in notes.video_title.lower() or "vid_dist_002" in notes.video_id:
            mermaid = (
                "sequenceDiagram\n"
                "    actor Client\n"
                "    participant CommandHandler as Command Handler\n"
                "    participant EventStore as Append-Only Event Store\n"
                "    participant Projection as Async Projection Worker\n"
                "    participant ReadDB as Read Model (Elasticsearch)\n\n"
                "    Client->>CommandHandler: Issue Command (DepositMoney)\n"
                "    CommandHandler->>EventStore: Append Event (MoneyDeposited)\n"
                "    EventStore-->>CommandHandler: Ack Event Stored\n"
                "    CommandHandler-->>Client: Command Accepted\n"
                "    EventStore-)Projection: Stream New Event\n"
                "    Projection->>ReadDB: Update Customer Balance View"
            )
            return VisualAssetSchema(
                video_id=notes.video_id,
                section_index=1,
                asset_type=VisualType.MERMAID_SEQUENCE,
                title="Event Sourcing & CQRS End-to-End Sequence Flow",
                description="Sequence diagram detailing write path command handling, event persistence, and asynchronous read model projection.",
                mermaid_code=mermaid,
                mime_type="image/svg+xml",
                is_generated=True,
                decision_reason="Sequence diagram is ideal for visualizing the asynchronous decoupling of the write and read models."
            )
        return None

    async def generate_image(self, prompt: str) -> Optional[str]:
        return None

