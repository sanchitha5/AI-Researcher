import type { ProgressStep, ResearchMode, StreamEventName } from "../types/research";

const STEP_LABELS: Record<string, string> = {
    analyze: "Understanding your question",
    select: "Selecting research sources",
    search_docs: "Searching uploaded documents",
    search_web: "Searching the web",
    evaluate: "Checking research quality",
    refine: "Refining search",
    generate: "Generating answer",
};

export function buildInitialSteps(mode: ResearchMode): ProgressStep[] {
    const keys = ["analyze", "select", "search_docs", "search_web", "evaluate", "refine", "generate"];
    return keys.map((key) => {
        let status: ProgressStep["status"] = "pending";
        // In non-auto modes, "selecting sources" is instant/not meaningful — skip it visually.
        if (key === "select" && mode !== "auto") status = "skipped";
        if (key === "search_docs" && mode === "web") status = "skipped";
        if (key === "search_web" && mode === "documents") status = "skipped";
        return { key, label: STEP_LABELS[key], status };
    });
}

function setStatus(steps: ProgressStep[], key: string, status: ProgressStep["status"]): ProgressStep[] {
    return steps.map((s) => (s.key === key && s.status !== "skipped" ? { ...s, status } : s));
}

export function applyStreamEvent(
    steps: ProgressStep[],
    event: StreamEventName,
    data: any
): ProgressStep[] {
    let next = steps;

    switch (event) {
        case "query_analyzed":
            next = setStatus(next, "analyze", "done");
            next = setStatus(next, "select", "active");
            break;

        case "source_selected": {
            next = setStatus(next, "select", "done");
            const sources: string[] = data?.selected_sources ?? [];
            if (!sources.includes("document")) next = setStatus(next, "search_docs", "skipped");
            if (!sources.includes("web")) next = setStatus(next, "search_web", "skipped");
            break;
        }

        case "document_search_started":
            next = setStatus(next, "search_docs", "active");
            break;
        case "document_search_completed":
            next = setStatus(next, "search_docs", "done");
            break;

        case "web_search_started":
            next = setStatus(next, "search_web", "active");
            break;
        case "web_search_completed":
            next = setStatus(next, "search_web", "done");
            break;

        case "evaluation_started":
            next = setStatus(next, "evaluate", "active");
            // If we're evaluating again after a retry, the previous refine step is complete.
            next = setStatus(next, "refine", "done");
            break;

        case "retry_started":
            next = setStatus(next, "evaluate", "done");
            next = setStatus(next, "refine", "active");
            // Loop back: mark the selected search steps pending again so they visibly re-run.
            next = next.map((s) =>
                (s.key === "search_docs" || s.key === "search_web") && s.status !== "skipped"
                    ? { ...s, status: "pending" }
                    : s
            );
            break;

        case "answer_generation_started":
            next = setStatus(next, "evaluate", "done");
            next = setStatus(next, "refine", "done");
            next = setStatus(next, "generate", "active");
            break;

        case "answer_completed":
        case "done":
            next = setStatus(next, "generate", "done");
            break;
    }

    return next;
}
