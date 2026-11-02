"""
LangGraph nodes.

Each function here is one node in the agent graph. A node takes the
current AgentState, does one clear job, and returns a dict of the
state fields it wants to update (LangGraph merges this into the
overall state).

Node responsibilities (see graph.py for how these connect):

    analyze_query     -> read the question, set the active search query
    route_research    -> decide which source(s) to search (doc/web/both)
    document_search   -> query ChromaDB for relevant chunks
    web_search         -> query Tavily for relevant web results
    evaluate_results   -> ask the LLM if we have enough to answer
    rewrite_query      -> ask the LLM for a better search query, retry
    generate_answer    -> ask the LLM to write the final cited answer
"""

import json
import re

from app.agent.prompts import (
    ANSWER_GENERATION_PROMPT,
    EVALUATION_PROMPT,
    REWRITE_QUERY_PROMPT,
    ROUTING_PROMPT,
)
from app.agent.state import AgentState
from app.rag.retriever import retrieve_document_chunks
from app.services.groq_service import get_llm
from app.services.tavily_service import TavilyNotConfiguredError, TavilySearchError
from app.services.tavily_service import web_search as tavily_web_search


def _parse_json_object(text: str) -> dict:
    """
    Best-effort extraction of a JSON object from an LLM response.

    LLMs occasionally wrap JSON in markdown fences or add a stray
    sentence before/after it, so we look for the first {...} block
    rather than assuming the whole response is clean JSON.
    """
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in LLM response: {text!r}")
    return json.loads(match.group(0))


# ---------------------------------------------------------------------------
# 1. analyze_query
# ---------------------------------------------------------------------------


def analyze_query(state: AgentState) -> dict:
    """Set the initial active search query from the user's question."""
    return {
        "active_query": state["question"],
        "retry_count": 0,
    }


# ---------------------------------------------------------------------------
# 2. route_research
# ---------------------------------------------------------------------------


def route_research(state: AgentState) -> dict:
    """
    Decide which source(s) to search.

    - mode "documents" -> always ["document"]
    - mode "web"        -> always ["web"]
    - mode "auto"       -> ask the LLM to decide based on the question
    """
    mode = state.get("research_mode", "auto")

    if mode == "documents":
        return {"selected_sources": ["document"]}

    if mode == "web":
        return {"selected_sources": ["web"]}

    # --- auto mode: let the LLM decide ---
    documents_available = state.get("documents_available", False)

    if not documents_available:
        # No documents uploaded at all -- nothing to route to but the web.
        return {"selected_sources": ["web"]}

    prompt = ROUTING_PROMPT.format(
        documents_available="yes" if documents_available else "no",
        question=state["question"],
    )

    try:
        llm = get_llm()
        response = llm.invoke(prompt)
        parsed = _parse_json_object(response.content)
        sources = parsed.get("sources", ["web"])
        sources = [s for s in sources if s in ("document", "web")] or ["web"]
    except Exception:  # noqa: BLE001 - fall back to a safe default on any LLM hiccup
        sources = ["document", "web"]

    return {"selected_sources": sources}


# ---------------------------------------------------------------------------
# 3. document_search
# ---------------------------------------------------------------------------


def document_search(state: AgentState) -> dict:
    """Retrieve the most relevant chunks from ChromaDB."""
    query = state.get("active_query") or state["question"]
    document_ids = state.get("document_ids") or None

    try:
        results = retrieve_document_chunks(query, document_ids=document_ids)
    except Exception:  # noqa: BLE001 - a broken vector store shouldn't crash the agent
        results = []

    return {"document_results": results}


# ---------------------------------------------------------------------------
# 4. web_search
# ---------------------------------------------------------------------------


def web_search(state: AgentState) -> dict:
    """Retrieve the most relevant results from Tavily."""
    query = state.get("active_query") or state["question"]

    try:
        results = tavily_web_search(query)
    except (TavilyNotConfiguredError, TavilySearchError):
        results = []
    except Exception:  # noqa: BLE001
        results = []

    return {"web_results": results}


# ---------------------------------------------------------------------------
# 5. evaluate_results
# ---------------------------------------------------------------------------


def _build_research_context(state: AgentState) -> str:
    parts = []
    for i, chunk in enumerate(state.get("document_results", []), start=1):
        parts.append(f"[Document {i}] {chunk['filename']} (page {chunk['page']}):\n{chunk['content']}")
    for i, result in enumerate(state.get("web_results", []), start=1):
        parts.append(f"[Web {i}] {result['title']} ({result['source']}):\n{result['content']}")
    return "\n\n".join(parts) if parts else "(no results found)"


def evaluate_results(state: AgentState) -> dict:
    """Ask the LLM whether the retrieved research is good enough to answer with."""
    has_any_results = bool(state.get("document_results") or state.get("web_results"))

    if not has_any_results:
        return {
            "sufficient_information": False,
            "evaluation_reasoning": "No results were found for this query.",
        }

    research_context = _build_research_context(state)
    prompt = EVALUATION_PROMPT.format(
        question=state["question"],
        research_context=research_context,
    )

    try:
        llm = get_llm()
        response = llm.invoke(prompt)
        parsed = _parse_json_object(response.content)
        sufficient = bool(parsed.get("sufficient", True))
        reasoning = str(parsed.get("reasoning", ""))
    except Exception:  # noqa: BLE001 - if evaluation fails, assume sufficient rather than looping forever
        sufficient = True
        reasoning = "Evaluation step failed; proceeding with available results."

    return {"sufficient_information": sufficient, "evaluation_reasoning": reasoning}


# ---------------------------------------------------------------------------
# 6. rewrite_query
# ---------------------------------------------------------------------------


def rewrite_query(state: AgentState) -> dict:
    """Ask the LLM for a better search query, then bump the retry counter."""
    research_context = _build_research_context(state)
    prompt = REWRITE_QUERY_PROMPT.format(
        question=state["question"],
        previous_query=state.get("active_query", state["question"]),
        research_context=research_context,
    )

    try:
        llm = get_llm()
        response = llm.invoke(prompt)
        new_query = response.content.strip().strip('"')
        if not new_query:
            raise ValueError("empty rewrite")
    except Exception:  # noqa: BLE001 - fall back to the original question
        new_query = state["question"]

    return {
        "rewritten_query": new_query,
        "active_query": new_query,
        "retry_count": state.get("retry_count", 0) + 1,
        # Clear previous round's results so evaluate_results judges the new round fairly.
        "document_results": [],
        "web_results": [],
    }


# ---------------------------------------------------------------------------
# 7. generate_answer
# ---------------------------------------------------------------------------


def generate_answer(state: AgentState) -> dict:
    """Ask the LLM to write the final answer, grounded in numbered evidence."""
    document_results = state.get("document_results", [])
    web_results = state.get("web_results", [])

    evidence_lines = []
    citations = []
    index = 1

    for chunk in document_results:
        evidence_lines.append(f"[{index}] (Document — {chunk['filename']}, page {chunk['page']}): {chunk['content']}")
        citations.append(
            {
                "index": index,
                "type": "document",
                "filename": chunk["filename"],
                "page": chunk["page"],
                "snippet": chunk["content"][:280],
            }
        )
        index += 1

    for result in web_results:
        evidence_lines.append(f"[{index}] (Web — {result['source']}): {result['title']} — {result['content']}")
        citations.append(
            {
                "index": index,
                "type": "web",
                "title": result["title"],
                "url": result["url"],
                "source": result["source"],
            }
        )
        index += 1

    sources_used = []
    if document_results:
        sources_used.append("documents")
    if web_results:
        sources_used.append("web")

    if not evidence_lines:
        answer = (
            "I couldn't find enough information to answer this question. "
            "Try uploading a relevant document, rephrasing your question, "
            "or switching research mode."
        )
        return {"answer": answer, "citations": [], "sources_used": []}

    numbered_evidence = "\n\n".join(evidence_lines)
    prompt = ANSWER_GENERATION_PROMPT.format(
        question=state["question"],
        numbered_evidence=numbered_evidence,
    )

    try:
        llm = get_llm()
        response = llm.invoke(prompt)
        answer = response.content.strip()
    except Exception as exc:  # noqa: BLE001
        answer = (
            "I found relevant research, but was unable to generate a final answer "
            f"due to an error contacting the language model ({exc.__class__.__name__}). "
            "Please check your GROQ_API_KEY and try again."
        )

    if not state.get("sufficient_information", True) and state.get("retry_count", 0) > 0:
        answer += (
            "\n\n*Note: after refining the search, the available sources still may not "
            "fully cover this question. The answer above reflects the best information found.*"
        )

    return {"answer": answer, "citations": citations, "sources_used": sources_used}
