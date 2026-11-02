"""
The LangGraph agent graph.

This is the file to open first if you want to understand how the
research agent thinks. It wires together the nodes defined in
nodes.py using the routing decisions defined in router.py.

Graph shape:

    START
      |
      v
    analyze_query
      |
      v
    route_research
      |
      +----------------+
      v                v
    document_search   web_search        <- run whichever the router picked
      |                |
      +--------+-------+
               v
       evaluate_results
               |
       enough information?
         /            \\
       NO              YES
        |                |
   rewrite_query    generate_answer
        |                |
        v                v
   (loop back to      END
    document_search /
    web_search)

The loop is bounded by MAX_RETRIES (see router.route_after_evaluation)
so the agent can never spin forever.
"""

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from app.agent import nodes
from app.agent.router import route_after_analysis, route_after_evaluation
from app.agent.state import AgentState


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("analyze_query", nodes.analyze_query)
    graph.add_node("route_research", nodes.route_research)
    graph.add_node("document_search", nodes.document_search)
    graph.add_node("web_search", nodes.web_search)
    graph.add_node("evaluate_results", nodes.evaluate_results)
    graph.add_node("rewrite_query", nodes.rewrite_query)
    graph.add_node("generate_answer", nodes.generate_answer)

    graph.add_edge(START, "analyze_query")
    graph.add_edge("analyze_query", "route_research")

    # Fan out to document_search and/or web_search based on the router's decision.
    graph.add_conditional_edges(
        "route_research",
        route_after_analysis,
        {"document_search": "document_search", "web_search": "web_search"},
    )

    # Both search nodes converge on evaluate_results.
    graph.add_edge("document_search", "evaluate_results")
    graph.add_edge("web_search", "evaluate_results")

    # After evaluation: either we have enough info (-> generate_answer),
    # or we don't and haven't hit the retry limit (-> rewrite_query).
    graph.add_conditional_edges(
        "evaluate_results",
        route_after_evaluation,
        {"generate_answer": "generate_answer", "rewrite_query": "rewrite_query"},
    )

    # After rewriting the query, loop back through the same source(s)
    # that were originally selected (re-uses the same routing decision).
    graph.add_conditional_edges(
        "rewrite_query",
        route_after_analysis,
        {"document_search": "document_search", "web_search": "web_search"},
    )

    graph.add_edge("generate_answer", END)

    return graph.compile()


@lru_cache(maxsize=1)
def get_compiled_graph():
    """Compile the graph once and reuse it across requests."""
    return build_graph()
