"""
Routing logic.

These are the small decision functions used as LangGraph
"conditional edges" — they inspect the current state and return a
string that tells the graph which node to go to next. Keeping them
separate from the node implementations makes the graph's branching
logic easy to scan in one place.
"""

from app.agent.state import AgentState


def route_after_analysis(state: AgentState) -> list[str]:
    """
    After analyze_query has decided `selected_sources`, fan out to
    whichever search node(s) are needed. LangGraph runs all returned
    branches (in parallel, conceptually) before continuing.
    """
    sources = state.get("selected_sources", [])
    branches = []
    if "document" in sources:
        branches.append("document_search")
    if "web" in sources:
        branches.append("web_search")
    # Safety net: if routing somehow produced nothing, fall back to web.
    return branches or ["web_search"]


def route_after_evaluation(state: AgentState) -> str:
    """
    After evaluate_results, decide whether we have enough information
    to answer, or whether we should rewrite the query and search again
    (bounded by max_retries to avoid infinite loops).
    """
    if state.get("sufficient_information"):
        return "generate_answer"

    if state.get("retry_count", 0) >= state.get("max_retries", 2):
        # Out of retries — answer with whatever we have rather than
        # looping forever. generate_answer will note the limitation.
        return "generate_answer"

    return "rewrite_query"
