import logging
from typing import List
from app.integrations.research.base import BaseResearchProvider
from app.domain.schemas.research import ResearchSource

logger = logging.getLogger(__name__)


class MockResearchProvider(BaseResearchProvider):
    """High-fidelity mock research provider for testing and offline/demo execution."""

    def __init__(self):
        self._curated_knowledge = [
            {
                "keywords": ["gcp", "cloud", "iam", "hierarchy", "compute", "google"],
                "source": ResearchSource(
                    title="Google Cloud Architecture Framework: Core Design & Hierarchy",
                    url="https://cloud.google.com/architecture/framework",
                    domain="cloud.google.com",
                    snippet=(
                        "Google Cloud organizes resources hierarchically: Organization -> Folders -> "
                        "Projects -> Resources. IAM policies are inherited downward with least-privilege principles. "
                        "Compute Engine instances map directly to VPC networks and subnets across availability zones."
                    ),
                    relevance_summary="Official Google Cloud architectural documentation on resource hierarchy and IAM inheritance.",
                    score=0.98,
                ),
            },
            {
                "keywords": ["kubernetes", "k8s", "container", "pod", "deployment"],
                "source": ResearchSource(
                    title="Kubernetes Core Concepts: Architecture and Workloads",
                    url="https://kubernetes.io/docs/concepts/",
                    domain="kubernetes.io",
                    snippet=(
                        "Kubernetes orchestrates containerized workloads through a control plane (kube-apiserver, "
                        "etcd, kube-scheduler, kube-controller-manager) and worker nodes running kubelet and kube-proxy. "
                        "Pods encapsulate application containers sharing network namespaces and storage volumes."
                    ),
                    relevance_summary="Kubernetes official documentation on control plane topology and pod lifecycles.",
                    score=0.95,
                ),
            },
            {
                "keywords": ["docker", "container", "dockerfile", "image"],
                "source": ResearchSource(
                    title="Docker Engine Internals: Namespaces, Cgroups, and OverlayFS",
                    url="https://docs.docker.com/engine/architecture/",
                    domain="docs.docker.com",
                    snippet=(
                        "Docker uses Linux kernel namespaces (pid, net, ipc, mnt, uts, user) for isolation "
                        "and control groups (cgroups) for resource constraint allocation. Images are composed of layered "
                        "read-only union filesystems (OverlayFS) with a thin writable container layer."
                    ),
                    relevance_summary="Docker Engine architecture specification on container isolation mechanisms.",
                    score=0.96,
                ),
            },
            {
                "keywords": ["python", "asyncio", "concurrency", "gil"],
                "source": ResearchSource(
                    title="Python 3 Documentation: Asyncio, Coroutines and Event Loops",
                    url="https://docs.python.org/3/library/asyncio.html",
                    domain="docs.python.org",
                    snippet=(
                        "Asyncio provides single-threaded cooperative multitasking via an event loop executing "
                        "coroutines. Unlike OS thread preemption, coroutines yield control explicitly using 'await'. "
                        "CPU-bound tasks require multiprocessing to bypass the Global Interpreter Lock (GIL)."
                    ),
                    relevance_summary="Python standard library documentation on asynchronous execution models.",
                    score=0.94,
                ),
            },
            {
                "keywords": ["database", "sql", "acid", "index", "b-tree", "postgres"],
                "source": ResearchSource(
                    title="PostgreSQL Internals: MVCC and Write-Ahead Logging (WAL)",
                    url="https://www.postgresql.org/docs/current/wal-intro.html",
                    domain="postgresql.org",
                    snippet=(
                        "PostgreSQL guarantees ACID compliance through Multi-Version Concurrency Control (MVCC) "
                        "and Write-Ahead Logging (WAL). Changes are recorded to sequential log buffers before data pages "
                        "are flushed, ensuring crash recovery and zero read/write blocking conflicts."
                    ),
                    relevance_summary="PostgreSQL official documentation on concurrency control and storage integrity.",
                    score=0.97,
                ),
            },
            {
                "keywords": ["system design", "distributed", "consensus", "cap", "raft"],
                "source": ResearchSource(
                    title="The Raft Consensus Algorithm: In Search of an Understandable Consensus Algorithm",
                    url="https://raft.github.io/",
                    domain="raft.github.io",
                    snippet=(
                        "Raft achieves consensus via leader election, log replication, and safety guarantees. "
                        "A majority quorum (N/2 + 1) is required to commit log entries, preventing split-brain states "
                        "and ensuring consistent state machine execution across distributed clusters."
                    ),
                    relevance_summary="Authoritative specification of distributed state machine replication.",
                    score=0.99,
                ),
            },
        ]

    async def search(self, query: str, max_results: int = 5) -> List[ResearchSource]:
        query_lower = query.lower()
        matched: List[ResearchSource] = []

        for item in self._curated_knowledge:
            if any(kw in query_lower for kw in item["keywords"]):
                matched.append(item["source"])

        if not matched:
            # Fallback general engineering reference
            matched.append(
                ResearchSource(
                    title=f"Technical Reference: {query.title()}",
                    url=f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}",
                    domain="wikipedia.org",
                    snippet=(
                        f"Foundational concepts, industry standards, and architectural trade-offs related to {query}. "
                        "Includes mathematical formalisms, algorithmic complexities, and standard industry practices."
                    ),
                    relevance_summary=f"Foundational reference for topic: '{query}'",
                    score=0.88,
                )
            )

        logger.info("[MOCK RESEARCH] Simulated search for '%s' returned %d sources", query, len(matched[:max_results]))
        return matched[:max_results]

