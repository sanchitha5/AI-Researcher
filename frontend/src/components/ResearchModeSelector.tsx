import { Files, Globe, Sparkles } from "lucide-react";
import type { ResearchMode } from "../types/research";

interface ResearchModeSelectorProps {
    mode: ResearchMode;
    onChange: (mode: ResearchMode) => void;
    compact?: boolean;
}

const OPTIONS: { value: ResearchMode; label: string; icon: typeof Sparkles }[] = [
    { value: "auto", label: "Auto", icon: Sparkles },
    { value: "documents", label: "Documents", icon: Files },
    { value: "web", label: "Web", icon: Globe },
];

export default function ResearchModeSelector({ mode, onChange, compact = false }: ResearchModeSelectorProps) {
    return (
        <div className="inline-flex items-center gap-1 rounded-lg border border-border bg-surface p-1">
            {OPTIONS.map(({ value, label, icon: Icon }) => {
                const active = mode === value;
                return (
                    <button
                        key={value}
                        type="button"
                        onClick={() => onChange(value)}
                        className={`flex items-center gap-1.5 rounded-md font-medium transition-colors ${compact ? "px-2.5 py-1 text-xs" : "px-3.5 py-1.5 text-sm"
                            } ${active ? "bg-white text-ink shadow-card" : "text-ink-soft hover:text-ink"}`}
                    >
                        <Icon size={compact ? 12 : 14} />
                        {label}
                    </button>
                );
            })}
        </div>
    );
}
