from app.agent.router import route_after_analysis, route_after_evaluation


def test_route_after_analysis_document_only():
    state = {"selected_sources": ["document"]}
    assert route_after_analysis(state) == ["document_search"]


def test_route_after_analysis_web_only():
    state = {"selected_sources": ["web"]}
    assert route_after_analysis(state) == ["web_search"]


def test_route_after_analysis_both():
    state = {"selected_sources": ["document", "web"]}
    result = route_after_analysis(state)
    assert "document_search" in result
    assert "web_search" in result


def test_route_after_evaluation_sufficient_goes_to_answer():
    state = {"sufficient_information": True, "retry_count": 0, "max_retries": 2}
    assert route_after_evaluation(state) == "generate_answer"


def test_route_after_evaluation_insufficient_retries():
    state = {"sufficient_information": False, "retry_count": 0, "max_retries": 2}
    assert route_after_evaluation(state) == "rewrite_query"


def test_route_after_evaluation_stops_at_max_retries():
    state = {"sufficient_information": False, "retry_count": 2, "max_retries": 2}
    assert route_after_evaluation(state) == "generate_answer"
