"""
LangGraph agent state.

This TypedDict is the single "shared memory" that flows through
every node in the graph. Each node reads whatever fields it needs
and returns a dict of the fields it wants to update — LangGraph
merges that into the overall state automatically.

Keeping this state flat and well-commented is intentional: a
workshop student should be able to read this file and immediately
understand what data the agent is carrying around at each step.
"""

from typing import Literal, TypedDict

ResearchMode = Literal["auto", "documents", "web"]
SelectedSource = Literal["document", "web"]


class DocumentChunkResult(TypedDict):
    filename: str
    page: int
    chunk_id: str
    content: str


class WebResult(TypedDict):
    title: str
    url: str
    content: str
    source: str


class AgentState(TypedDict, total=False):
    # --- Input ---
    question: str
    research_mode: ResearchMode
    document_ids: list[str]  # which uploaded docs to search (empty = all)
    documents_available: bool  # whether ANY documents have been uploaded

    # --- Routing decision ---
    selected_sources: list[SelectedSource]

    # --- Research results ---
    document_results: list[DocumentChunkResult]
    web_results: list[WebResult]

    # --- Evaluation / retry loop ---
    sufficient_information: bool
    evaluation_reasoning: str
    rewritten_query: str
    active_query: str  # the query actually used for the current search round
    retry_count: int
    max_retries: int

    # --- Output ---
    answer: str
    citations: list[dict]
    sources_used: list[str]

    # --- Streaming / progress (not sent to the LLM, only used for SSE events) ---
    events: list[dict]
