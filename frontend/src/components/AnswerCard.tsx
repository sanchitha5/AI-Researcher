import ReactMarkdown from "react-markdown";
import { PanelRightOpen } from "lucide-react";
import type { ResearchResult } from "../types/research";
import CitationList from "./CitationList";

interface AnswerCardProps {
    result: ResearchResult;
    onViewSources: () => void;
}

const MODE_LABEL: Record<string, string> = {
    auto: "Auto",
    documents: "Documents",
    web: "Web",
};

export default function AnswerCard({ result, onViewSources }: AnswerCardProps) {
    return (
        <div className="animate-slideUp">
            <div className="answer-prose text-[15px] text-ink">
                <ReactMarkdown>{result.answer}</ReactMarkdown>
            </div>

            <CitationList citations={result.citations} />

            <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-ink-faint">
                <span className="rounded-full border border-border px-2 py-0.5">
                    {MODE_LABEL[result.mode_used] ?? result.mode_used} mode
                </span>
                {result.retries > 0 && (
                    <span className="rounded-full border border-border px-2 py-0.5">
                        {result.retries} search {result.retries === 1 ? "refinement" : "refinements"}
                    </span>
                )}
                {result.citations.length > 0 && (
                    <button
                        onClick={onViewSources}
                        className="flex items-center gap-1 rounded-full border border-border px-2 py-0.5 text-ink-soft transition-colors hover:border-accent/40 hover:text-accent"
                    >
                        <PanelRightOpen size={12} />
                        Inspect evidence
                    </button>
                )}
            </div>
        </div>
    );
}
