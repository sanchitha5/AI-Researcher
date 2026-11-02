import { Search, SquarePen } from "lucide-react";

interface HeaderProps {
    onNewResearch: () => void;
    hasActiveSession: boolean;
}

export default function Header({ onNewResearch, hasActiveSession }: HeaderProps) {
    return (
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-border px-5">
            <div className="flex items-center gap-2">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent text-white">
                    <Search size={15} strokeWidth={2.5} />
                </div>
                <span className="text-[15px] font-semibold text-ink">AI Researcher</span>
            </div>

            <button
                onClick={onNewResearch}
                disabled={!hasActiveSession}
                className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium text-ink-soft transition-colors hover:bg-surface hover:text-ink disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-transparent"
            >
                <SquarePen size={15} />
                New Research
            </button>
        </header>
    );
}
