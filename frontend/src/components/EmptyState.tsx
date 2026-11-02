import { Search } from "lucide-react";
import type { ResearchMode } from "../types/research";
import ResearchModeSelector from "./ResearchModeSelector";
import QuestionInput from "./QuestionInput";

interface EmptyStateProps {
    mode: ResearchMode;
    onModeChange: (mode: ResearchMode) => void;
    question: string;
    onQuestionChange: (value: string) => void;
    onSubmit: () => void;
    disabled: boolean;
}

export default function EmptyState({
    mode,
    onModeChange,
    question,
    onQuestionChange,
    onSubmit,
    disabled,
}: EmptyStateProps) {
    return (
        <div className="flex flex-1 flex-col items-center justify-center px-6 py-10">
            <div className="w-full max-w-xl animate-fadeIn">
                <div className="mb-8 flex flex-col items-center text-center">
                    <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-accent text-white shadow-card">
                        <Search size={22} strokeWidth={2.2} />
                    </div>
                    <h1 className="text-2xl font-semibold tracking-tight text-ink">AI Research Agent</h1>
                    <p className="mt-2 text-[15px] text-ink-soft">
                        Research across your documents and the web.
                    </p>
                </div>

                <div className="mb-5 flex flex-col items-center gap-2">
                    <span className="text-xs font-medium text-ink-faint">Research source</span>
                    <ResearchModeSelector mode={mode} onChange={onModeChange} />
                </div>

                <QuestionInput
                    value={question}
                    onChange={onQuestionChange}
                    onSubmit={onSubmit}
                    disabled={disabled}
                    autoFocus
                />

                <p className="mt-3 text-center text-xs text-ink-faint">
                    Press Enter to research &middot; Shift + Enter for a new line
                </p>
            </div>
        </div>
    );
}
