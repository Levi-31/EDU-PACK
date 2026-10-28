import asyncio
from typing import Optional, List
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
from app.domain.schemas.topic_plan import VideoTopicPlan, PlannedTopic
from app.domain.schemas.research import VideoResearchBundle, ResearchSource
from app.integrations.openai.client import OpenAIClientInterface


class MockOpenAIClient(OpenAIClientInterface):
    """
    Deterministic mock OpenAI client for demo mode and automated testing.
    Generates rich, schema-compliant technical notes with valid Mermaid diagrams,
    real code snippets, comprehensive theory, and review checks without external API keys.
    """

    async def generate_topic_plan(
        self,
        video_metadata: dict,
        transcript_text: str
    ) -> VideoTopicPlan:
        await asyncio.sleep(0.1)
        vid = video_metadata.get("video_id", "vid_demo")
        title = video_metadata.get("title", "Technical Architecture Lecture")

        if "consensus" in title.lower() or "vid_dist_001" in vid:
            return VideoTopicPlan(
                video_id=vid,
                video_title=title,
                overall_subject="Distributed Consensus & Replicated State Machines",
                audience_level="Advanced",
                planned_topics=[
                    PlannedTopic(
                        topic_id="topic_1",
                        title="Foundations of Consensus and the FLP Impossibility Theorem",
                        start_seconds=0.0,
                        end_seconds=180.0,
                        summary="The theoretical boundaries of consensus over asynchronous packet-dropping networks.",
                        learning_objectives=[
                            "Formulate the Fischer-Lynch-Paterson (FLP) impossibility result.",
                            "Distinguish safety invariants from liveness guarantees in distributed state machines."
                        ],
                        prerequisites=["Basic socket networking", "State machine basics"],
                        theoretical_depth_needed="high",
                        research_queries=["FLP Impossibility theorem proof", "Paxos vs Raft formal verification"],
                        suggested_diagram_type="architecture"
                    ),
                    PlannedTopic(
                        topic_id="topic_2",
                        title="Raft Leader Election and Randomized Heartbeats",
                        start_seconds=181.0,
                        end_seconds=420.0,
                        summary="Election timeout loops, randomized heartbeats, and split-vote mitigation.",
                        learning_objectives=[
                            "Calculate quorum majorities floor(N/2) + 1.",
                            "Trace RequestVote RPC workflows under simulated network partitions."
                        ],
                        prerequisites=["Consensus foundations"],
                        theoretical_depth_needed="medium",
                        research_queries=["Raft consensus algorithm paper Ongaro Ousterhout"],
                        suggested_diagram_type="sequence"
                    ),
                    PlannedTopic(
                        topic_id="topic_3",
                        title="Log Replication and Leader Completeness",
                        start_seconds=421.0,
                        end_seconds=750.0,
                        summary="Replication pipelines, commit index advancement, and durable write-ahead log fsync.",
                        learning_objectives=[
                            "Prove the Leader Completeness property.",
                            "Analyze linearizable read leases and the ReadIndex protocol."
                        ],
                        prerequisites=["Leader election mechanics"],
                        theoretical_depth_needed="high",
                        research_queries=["Raft linearizable reads ReadIndex leaseholder"],
                        suggested_diagram_type="flowchart"
                    )
                ],
                global_research_queries=["Raft consensus algorithm specification", "Distributed systems linearizability formalisms"]
            )
        else:
            return VideoTopicPlan(
                video_id=vid,
                video_title=title,
                overall_subject="Systems Engineering & Architecture",
                audience_level="Intermediate",
                planned_topics=[
                    PlannedTopic(
                        topic_id="topic_1",
                        title="Core Principles and Architectural Design",
                        start_seconds=0.0,
                        end_seconds=300.0,
                        summary=f"Foundational architectural patterns and design principles covered in {title}.",
                        learning_objectives=[
                            "Deconstruct modular system boundaries.",
                            "Evaluate coupling and cohesion in service components."
                        ],
                        prerequisites=["Basic software engineering concepts"],
                        theoretical_depth_needed="medium",
                        research_queries=[f"{title} architectural patterns", "Systems architecture industry best practices"],
                        suggested_diagram_type="architecture"
                    ),
                    PlannedTopic(
                        topic_id="topic_2",
                        title="Operational Mechanics and Trade-Off Analysis",
                        start_seconds=301.0,
                        end_seconds=600.0,
                        summary="Implementation details, failure modes, and production observability.",
                        learning_objectives=[
                            "Analyze throughput versus latency trade-offs.",
                            "Implement deterministic error handling and retries."
                        ],
                        prerequisites=["Core principles"],
                        theoretical_depth_needed="medium",
                        research_queries=[f"{title} production considerations", "Distributed systems fault tolerance"],
                        suggested_diagram_type="sequence"
                    )
                ],
                global_research_queries=[f"{title} official specification", "Systems design reference architecture"]
            )

    async def generate_structured_notes(
        self,
        video_metadata: dict,
        transcript_text: str,
        evidence_segments: list,
        detail_level: str = "standard",
        topic_plan: Optional[VideoTopicPlan] = None,
        research_bundle: Optional[VideoResearchBundle] = None
    ) -> StructuredVideoNotes:
        await asyncio.sleep(0.2)
        vid = video_metadata.get("video_id", "vid_demo")
        title = video_metadata.get("title", "Technical Computing Overview")
        video_url = video_metadata.get("video_url", f"https://www.youtube.com/watch?v={vid}")
        
        # Build segment IDs from evidence
        seg_ids = [s["id"] for s in evidence_segments] if evidence_segments else ["seg_0001"]
        seg_0 = seg_ids[0] if seg_ids else "seg_0001"
        seg_1 = seg_ids[min(1, len(seg_ids)-1)]
        seg_2 = seg_ids[min(2, len(seg_ids)-1)]
        seg_3 = seg_ids[min(3, len(seg_ids)-1)]

        curated_sources = research_bundle.sources if research_bundle and research_bundle.sources else [
            ResearchSource(
                title="Google Cloud Architecture Framework: Core Design & Hierarchy",
                url="https://cloud.google.com/architecture/framework",
                domain="cloud.google.com",
                snippet="Google Cloud resource hierarchy: Organization -> Folders -> Projects -> Resources. IAM policies are inherited downward with least-privilege principles.",
                relevance_summary="Official Google Cloud architectural documentation on resource hierarchy.",
                score=0.98
            )
        ]

        if "vid_dist_001" in vid or "consensus" in title.lower():
            return StructuredVideoNotes(
                schema_version="2.0",
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
                comprehensive_theory_background=(
                    "In distributed computing, achieving consensus across independent nodes over an unreliable network represents "
                    "the core synchronization bottleneck. Fischer, Lynch, and Paterson (FLP, 1985) proved that in a purely asynchronous "
                    "distributed system, no deterministic consensus protocol can guarantee both safety and liveness if even a single process "
                    "is subject to unannounced crash failures. To overcome this theoretical limitation, modern protocols like Raft and Paxos "
                    "introduce partial synchrony assumptions—specifically, utilizing randomized timeouts and heartbeat bounds to ensure progress "
                    "while preserving strict safety invariants under all partition scenarios."
                ),
                sections=[
                    NoteTopicSection(
                        title="1. Foundations of Consensus and the FLP Theorem",
                        markdown_content=(
                            "Distributed consensus is the problem of reaching agreement on a shared state value across a cluster of independent machines "
                            "communicating over an unreliable, packet-dropping network. Fischer, Lynch, and Paterson (FLP) established that in a strictly "
                            "asynchronous model, no deterministic algorithm can guarantee both safety and liveness if even one node can crash."
                        ),
                        from_video=(
                            "The instructor introduces why distributed consensus is challenging: machines experience packet drops, "
                            "clock drift, and node crashes. The lecture presents the core consensus contract: all non-faulty nodes "
                            "must decide on identical values in the identical sequence."
                        ),
                        additional_theory=(
                            "Formally, the consensus problem requires three invariants:\n"
                            "1. **Agreement (Safety):** Every non-faulty node must agree on the same value $v$.\n"
                            "2. **Validity (Integrity):** The decided value $v$ must have been proposed by at least one participant node.\n"
                            "3. **Termination (Liveness):** Every non-faulty node eventually reaches a decision.\n\n"
                            "Under the FLP impossibility result, asynchronous deterministic protocols sacrifice bounded termination "
                            "to maintain absolute agreement. Raft and Multi-Paxos circumvent this via weak synchrony assumptions: "
                            "they guarantee Safety under all network conditions (even total partitions), but guarantee Liveness only when "
                            "the network achieves bounded delay ($T_{heartbeat} \\ll T_{election} \\ll MTBF$)."
                        ),
                        comparison_table_markdown=(
                            "| Property | Multi-Paxos | Raft | Viewstamped Replication |\n"
                            "| :--- | :--- | :--- | :--- |\n"
                            "| **Leader Role** | Symmetric / Weak leader | Strong leader | Strong primary |\n"
                            "| **Understandability** | Low (notoriously opaque) | High (pedagogically designed) | Medium |\n"
                            "| **Log Overwrites** | Out-of-order log gaps | Strictly sequential logs | Strictly sequential logs |\n"
                            "| **Quorum Formula** | $\\lfloor N/2 \\rfloor + 1$ | $\\lfloor N/2 \\rfloor + 1$ | $\\lfloor N/2 \\rfloor + 1$ |"
                        ),
                        callouts=[
                            CalloutBox(
                                kind="important",
                                title="Safety vs. Liveness",
                                content="Safety ensures 'nothing bad happens' (no split-brain or duplicate leaders). Liveness ensures 'something good eventually happens' (progress is made)."
                            )
                        ],
                        cited_sources=curated_sources[:2],
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
                        from_video=(
                            "The instructor walks through the three Raft server states: Follower, Candidate, and Leader. "
                            "Demonstrates how heartbeat intervals prevent unnecessary elections and how split votes are mitigated using "
                            "randomized countdown timers."
                        ),
                        additional_theory=(
                            "The election mechanism enforces the **Election Safety** invariant: at most one leader can be elected in a given term. "
                            "Each server grants at most one vote per term on a first-come, first-served basis. Furthermore, servers refuse to vote "
                            "for a candidate whose log is less up-to-date than their own, using the comparison rule: "
                            "$(lastTerm_c > lastTerm_v) \\lor (lastTerm_c == lastTerm_v \\land lastIndex_c \\ge lastIndex_v)$."
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
                        from_video=(
                            "The instructor details the client write flow: client submits request to leader, leader writes to disk, "
                            "sends AppendEntries RPC to followers, waits for majority acknowledgment, and applies the entry."
                        ),
                        additional_theory=(
                            "Commitment is governed by the **Leader Completeness Property**: if an entry is committed in a given term, "
                            "that entry will be present in the logs of the leaders for all higher-numbered terms. "
                            "To serve linearizable read requests without disk writes, leaders implement the ReadIndex optimization, "
                            "confirming leadership status with a heartbeat broadcast before serving read state."
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
                common_misconceptions=[
                    "Misconception: A newly elected leader immediately knows all committed entries from past terms. Reality: The leader must commit an entry from its own current term before past entries can be safely considered committed.",
                    "Misconception: Raft requires an odd number of servers to function. Reality: Even numbers function, but odd numbers maximize fault tolerance per server (e.g. 5 nodes tolerate 2 failures, 6 nodes also tolerate only 2 failures)."
                ],
                glossary=[
                    GlossaryItem(term="Quorum", definition="A subset of nodes comprising a strict majority (floor(N/2) + 1) required to establish consensus."),
                    GlossaryItem(term="Split-Brain", definition="A catastrophic failure state where two nodes simultaneously believe they are the legitimate leader.")
                ],
                revision_sheet=(
                    "1. Always prefer odd cluster sizes (3, 5, 7) to avoid split votes.\n"
                    "2. Quorum size formula: Q = floor(N / 2) + 1.\n"
                    "3. Leaders never overwrite or truncate their own entries; they only overwrite out-of-date follower entries."
                ),
                flashcards=[
                    Flashcard(question="What guarantees that committed entries are never lost across term elections?", answer="The Leader Completeness Property: candidates must possess all committed entries to win votes."),
                    Flashcard(question="Why are Raft election timeouts randomized?", answer="To minimize the probability of split-vote ties among concurrent candidates.")
                ],
                topic_plan=topic_plan,
                all_sources=curated_sources,
                review_report=ReviewReport(
                    status="APPROVED",
                    groundedness_score=1.0,
                    theory_depth_score=1.0,
                    findings=["All claims verified against transcript timestamps", "Theoretical foundations clearly distinguished from video lecture", "Mermaid diagrams valid"]
                )
            )

        elif "vid_dist_002" in vid or "event" in title.lower():
            return StructuredVideoNotes(
                schema_version="2.0",
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
                comprehensive_theory_background=(
                    "Traditional relational data modeling centers on the Current State paradigm, where SQL UPDATE statements destructively overwrite previous attributes. "
                    "Event Sourcing shifts the system's foundational model from mutable current state to an append-only sequence of immutable domain events. "
                    "By combining Event Sourcing with CQRS (Command Query Responsibility Segregation, formalized by Greg Young), write models are optimized solely for "
                    "transactional consistency and business invariants, while read models are denormalized and horizontally scaled to serve specialized access patterns."
                ),
                sections=[
                    NoteTopicSection(
                        title="1. The Flaws of In-Place Row Mutation",
                        markdown_content=(
                            "Traditional CRUD operations perform in-place `UPDATE` statements, destroying the temporal history of how the system arrived "
                            "at that state. In high-concurrency transactional systems, row-level locks on hot balances cause thread starvation and deadlocks."
                        ),
                        from_video=(
                            "The instructor demonstrates the lock contention created by multiple transactions attempting to UPDATE "
                            "a single account row simultaneously, resulting in database deadlocks and lost audit history."
                        ),
                        additional_theory=(
                            "Mathematically, state at time $T$ is the left-fold of historical events over the initial state: "
                            "$S(T) = \\text{foldl}(f, S_0, [E_1, E_2, \\dots, E_T])$. "
                            "Because events are append-only, write transactions never encounter read-write lock conflicts, achieving "
                            "optimal throughput on sequential storage devices."
                        ),
                        comparison_table_markdown=(
                            "| Dimension | Traditional CRUD | Event Sourcing + CQRS |\n"
                            "| :--- | :--- | :--- |\n"
                            "| **Storage Mutation** | Destructive UPDATE/DELETE | Append-only INSERT |\n"
                            "| **Auditability** | Requires separate audit logs | Built-in temporal ledger |\n"
                            "| **Read Performance** | Complex JOINs over normalized tables | Denormalized projections tailored to queries |\n"
                            "| **Consistency Model** | Immediate strong consistency | Strong on write aggregate, eventual on read views |"
                        ),
                        cited_sources=curated_sources[:2],
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
                        from_video=(
                            "The instructor writes Python code showing how an Aggregate class loads events from an EventStore, "
                            "replays them sequentially to compute the balance, and validates a new withdrawal command."
                        ),
                        additional_theory=(
                            "To maintain high performance as an aggregate accumulates thousands of events, systems introduce Snapshots. "
                            "A snapshot records the aggregate state at event version $V_k$. Hydration only replays events with version $> V_k$. "
                            "Optimistic concurrency control is enforced by matching the aggregate's expected version in the append transaction."
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
                common_misconceptions=[
                    "Misconception: Projections must update synchronously with event writes. Reality: Projections are typically asynchronous; forcing synchronous writes re-introduces the distributed lock contention CQRS was designed to avoid.",
                    "Misconception: Event Sourcing replaces relational databases entirely. Reality: Event stores often leverage PostgreSQL JSONB with unique sequence constraints."
                ],
                glossary=[
                    GlossaryItem(term="Aggregate", definition="A cluster of associated objects treated as a single unit for data changes and invariant enforcement."),
                    GlossaryItem(term="Projection", definition="A read-optimized denormalized view derived from listening to event streams.")
                ],
                revision_sheet="Events are past-tense immutable facts. Commands can be rejected; events cannot.",
                flashcards=[
                    Flashcard(question="How does Event Sourcing handle high volume queries?", answer="Through CQRS read projections tailored to specific UI query patterns.")
                ],
                topic_plan=topic_plan,
                all_sources=curated_sources,
                review_report=ReviewReport(status="APPROVED", groundedness_score=1.0, theory_depth_score=1.0)
            )

        # Default generic enriched mock note
        return StructuredVideoNotes(
            schema_version="2.0",
            video_id=vid,
            video_title=title,
            video_url=video_url,
            channel_name=video_metadata.get("channel_title", "Technical Academy"),
            duration_seconds=video_metadata.get("duration_seconds", 900),
            thumbnail_url=video_metadata.get("thumbnail_url"),
            original_position=video_metadata.get("original_position", 0),
            is_mock=True,
            executive_summary=(
                f"[DEMO MODE / MOCK GENERATED NOTES] A comprehensive technical study guide on '{title}'. "
                "Covers foundational engineering principles, internal architecture, performance considerations, and operational trade-offs."
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
            comprehensive_theory_background=(
                f"Engineering robust architectures around '{title}' requires balancing system constraints across "
                "availability, consistency, and resource efficiency. The fundamental trade-offs stem from queueing theory, "
                "network latency bounds, and hardware memory hierarchies."
            ),
            sections=[
                NoteTopicSection(
                    title="1. Core Principles and Architectural Design",
                    markdown_content=(
                        f"In this section of '{title}', the foundational design principles are analyzed. "
                        "We examine how separating concerns into discrete modular components improves testability and resilience."
                    ),
                    from_video=(
                        f"The presenter outlines the core setup, terminology, and immediate prerequisites for {title}. "
                        "Demonstrates configuration parameters and component initialization."
                    ),
                    additional_theory=(
                        "From an architectural perspective, modular isolation bounds the fault domain. "
                        "Using well-defined API boundaries ensures independent deployability and simplifies regression testing."
                    ),
                    comparison_table_markdown=(
                        "| Feature | Traditional Pattern | Modern Modular Approach |\n"
                        "| :--- | :--- | :--- |\n"
                        "| **Coupling** | High / Monolithic | Loose / Contract-driven |\n"
                        "| **Scalability** | Vertical hardware scaling | Horizontal elastic scaling |\n"
                        "| **Resilience** | Single point of failure | Circuit-breaker isolation |"
                    ),
                    cited_sources=curated_sources[:2],
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
                    from_video=(
                        "The speaker demonstrates the configuration and step-by-step workflow in action, "
                        "highlighting key logs and verification commands."
                    ),
                    additional_theory=(
                        "Under load, systems encounter Little's Law ($L = \\lambda W$), meaning in-flight concurrency is directly proportional "
                        "to throughput and service time. Bounding in-flight concurrency with backpressure prevents system collapse."
                    ),
                    evidence_segment_ids=[seg_1],
                    timestamp_seconds=98.0,
                    timestamped_watch_url=f"{video_url}&t=98s"
                )
            ],
            architecture_and_workflows="Input Request -> Validation Pipeline -> Business Logic Engine -> Persistence Layer -> Observability Sink",
            trade_offs_and_decisions=["Throughput vs Latency: Batching increases bulk throughput at the cost of p50 latency."],
            pitfalls_and_limitations=["Unbounded queues risking Out-Of-Memory crashes under unexpected ingress spikes."],
            common_misconceptions=["Misconception: Adding more threads always improves throughput. Reality: Thread context switching overhead degrades throughput beyond CPU core capacity."],
            glossary=[GlossaryItem(term="Fault Tolerance", definition="The ability of a system to continue operating properly in the event of failure of some components.")],
            revision_sheet="Design for failure: enforce circuit breakers, timeouts, and structured error handling.",
            flashcards=[Flashcard(question="What is the primary trade-off of queue batching?", answer="Higher throughput at the expense of individual message latency.")],
            topic_plan=topic_plan,
            all_sources=curated_sources,
            review_report=ReviewReport(status="APPROVED", groundedness_score=1.0, theory_depth_score=1.0)
        )

    async def review_notes(
        self,
        notes: StructuredVideoNotes,
        transcript_text: str,
        topic_plan: Optional[VideoTopicPlan] = None,
        research_bundle: Optional[VideoResearchBundle] = None
    ) -> ReviewReport:
        await asyncio.sleep(0.1)
        return ReviewReport(
            status="APPROVED",
            groundedness_score=1.0,
            theory_depth_score=1.0,
            findings=[
                "All section titles and concepts match transcript technical scope.",
                "Timestamp references verified against transcript segments.",
                "Theoretical foundations clearly demarcated from source transcript facts.",
                "Citations and diagrams properly integrated."
            ],
            revisions_applied=0
        )

    async def revise_notes(
        self,
        notes: StructuredVideoNotes,
        review: ReviewReport,
        transcript_text: str,
        research_bundle: Optional[VideoResearchBundle] = None
    ) -> StructuredVideoNotes:
        await asyncio.sleep(0.1)
        notes.review_report.revisions_applied += 1
        return notes

    async def generate_visual_spec(self, notes: StructuredVideoNotes) -> Optional[VisualAssetSchema]:
        await asyncio.sleep(0.1)
        if "consensus" in notes.video_title.lower() or "vid_dist_001" in notes.video_id:
            mermaid = (
                "graph TD\n"
                "    subgraph Raft Cluster\n"
                "        L[\"Leader Node - Term 2\"] -->|AppendEntries RPC| F1[\"Follower 1 - Term 2\"]\n"
                "        L -->|AppendEntries RPC| F2[\"Follower 2 - Term 2\"]\n"
                "        L -.->|Network Partition| F3[\"Follower 3 - Isolated\"]\n"
                "    end\n"
                "    C[\"Client Command\"] -->|Write Proposal| L\n"
                "    F1 -->|Quorum Ack 2/3| L\n"
                "    L -->|Commit Index++| SM[\"State Machine\"]"
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
        else:
            mermaid = (
                "flowchart TD\n"
                "    A[\"Input Client Request\"] --> B{\"API Gateway & Auth\"}\n"
                "    B -->|Authorized| C[\"Service Processing Engine\"]\n"
                "    B -->|Unauthorized| D[\"401 / 403 Response\"]\n"
                "    C --> E[(\"Durable Data Store\")]\n"
                "    C --> F[\"Event Bus / Queue\"]\n"
                "    E --> G[\"200 OK Response\"]"
            )
            return VisualAssetSchema(
                video_id=notes.video_id,
                section_index=0,
                asset_type=VisualType.MERMAID_ARCHITECTURE,
                title=f"Architecture Overview for {notes.video_title}",
                description="System architecture overview diagram.",
                mermaid_code=mermaid,
                mime_type="image/svg+xml",
                is_generated=True,
                decision_reason="Architecture flow diagram visually clarifies request lifecycle and persistent state boundaries."
            )

    async def generate_image(self, prompt: str) -> Optional[str]:
        return None
