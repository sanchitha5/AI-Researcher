"""
Research endpoints.

- POST /api/research         -> run the agent, return the final result (no streaming)
- POST /api/research/stream  -> run the agent, streaming progress events as SSE

Both endpoints build the same initial AgentState and run the same
LangGraph graph (app/agent/graph.py) — the streaming version just
also emits progress events as the graph executes, by listening to
LangGraph's `astream_events`.
"""

import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.agent.graph import get_compiled_graph
from app.agent.state import AgentState
from app.config import settings
from app.models.research import Citation, ResearchRequest, ResearchResponse
from app.services.document_service import get_ready_document_ids
from app.utils.sse import format_sse

router = APIRouter(prefix="/api/research", tags=["research"])

# Maps a LangGraph node name -> (event name to emit when it STARTS, event name to emit when it ENDS)
# `None` means "don't emit an event for this transition".
NODE_EVENTS: dict[str, tuple[str | None, str | None]] = {
    "analyze_query": (None, "query_analyzed"),
    "route_research": (None, "source_selected"),
    "document_search": ("document_search_started", "document_search_completed"),
    "web_search": ("web_search_started", "web_search_completed"),
    "evaluate_results": ("evaluation_started", None),
    "rewrite_query": ("retry_started", None),
    "generate_answer": ("answer_generation_started", "answer_completed"),
}


def _validate_request(request: ResearchRequest) -> None:
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    if not settings.groq_configured:
        raise HTTPException(
            status_code=503,
            detail="The AI model is not configured. Ask the workshop host to set GROQ_API_KEY in backend/.env.",
        )

    if request.mode == "web" and not settings.tavily_configured:
        raise HTTPException(
            status_code=503,
            detail="Web search is not configured. Set TAVILY_API_KEY in backend/.env, "
            "or switch to 'Documents' mode.",
        )

    if request.mode == "documents":
        if not settings.gemini_configured:
            raise HTTPException(
                status_code=503,
                detail="Google Gemini embeddings are not configured. Set GEMINI_API_KEY in backend/.env.",
            )
        if not get_ready_document_ids():
            raise HTTPException(
                status_code=400,
                detail="No documents have been uploaded yet. Upload a document first, or switch to 'Web' mode.",
            )


def _build_initial_state(request: ResearchRequest) -> AgentState:
    ready_ids = get_ready_document_ids()
    document_ids = [d for d in request.document_ids if d in ready_ids] or ready_ids

    return AgentState(
        question=request.question.strip(),
        research_mode=request.mode,
        document_ids=document_ids,
        documents_available=bool(ready_ids),
        selected_sources=[],
        document_results=[],
        web_results=[],
        sufficient_information=False,
        evaluation_reasoning="",
        rewritten_query="",
        active_query=request.question.strip(),
        retry_count=0,
        max_retries=settings.MAX_RETRIES,
        answer="",
        citations=[],
        sources_used=[],
    )


def _to_response(final_state: dict, mode: str) -> ResearchResponse:
    citations = [Citation(**c) for c in final_state.get("citations", [])]
    return ResearchResponse(
        answer=final_state.get("answer", ""),
        citations=citations,
        sources_used=final_state.get("sources_used", []),
        retries=final_state.get("retry_count", 0),
        mode_used=mode,
    )


@router.post("", response_model=ResearchResponse)
async def run_research(request: ResearchRequest) -> ResearchResponse:
    _validate_request(request)
    graph = get_compiled_graph()
    initial_state = _build_initial_state(request)

    try:
        final_state = await graph.ainvoke(initial_state)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502,
            detail="The research agent hit an unexpected error. Please try again.",
        ) from exc

    return _to_response(final_state, request.mode)


@router.post("/stream")
async def run_research_stream(request: ResearchRequest):
    _validate_request(request)
    graph = get_compiled_graph()
    initial_state = _build_initial_state(request)

    async def event_generator():
        # Accumulate partial state updates as nodes complete, so that by the
        # end we have the equivalent of the graph's final merged state.
        merged_state: dict = dict(initial_state)
        try:
            async for event in graph.astream_events(initial_state, version="v2"):
                kind = event.get("event")
                name = event.get("name")

                if name not in NODE_EVENTS:
                    continue

                start_event, end_event = NODE_EVENTS[name]

                if kind == "on_chain_start" and start_event:
                    yield format_sse(start_event, {"node": name})

                if kind == "on_chain_end":
                    output = event.get("data", {}).get("output", {}) or {}
                    if isinstance(output, dict):
                        merged_state.update(output)
                    if end_event:
                        data = _summarize_node_output(name, output)
                        yield format_sse(end_event, data)

            if merged_state.get("answer"):
                response = _to_response(merged_state, request.mode)
                yield format_sse("done", response.model_dump())
            else:
                yield format_sse(
                    "error",
                    {"message": "The research agent did not produce a final answer. Please try again."},
                )
        except Exception as exc:  # noqa: BLE001
            yield format_sse(
                "error",
                {"message": f"An unexpected error occurred while researching: {exc.__class__.__name__}"},
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _summarize_node_output(node_name: str, output: dict) -> dict:
    """Build a small, frontend-friendly payload describing what a node produced."""
    if node_name == "route_research":
        return {"selected_sources": output.get("selected_sources", [])}
    if node_name == "document_search":
        return {"count": len(output.get("document_results", []))}
    if node_name == "web_search":
        return {"count": len(output.get("web_results", []))}
    if node_name == "generate_answer":
        return {
            "answer": output.get("answer", ""),
            "citations": output.get("citations", []),
            "sources_used": output.get("sources_used", []),
        }
    return {}
