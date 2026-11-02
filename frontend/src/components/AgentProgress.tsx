import { Check, Loader2 } from "lucide-react";
import type { ProgressStep } from "../types/research";

interface AgentProgressProps {
    steps: ProgressStep[];
}

export default function AgentProgress({ steps }: AgentProgressProps) {
    const visibleSteps = steps.filter((s) => s.status !== "skipped");

    return (
        <div className="animate-fadeIn rounded-xl border border-border bg-surface px-4 py-3.5">
            <p className="mb-2 text-xs font-medium uppercase tracking-wide text-ink-faint">
                AI Research Agent
            </p>
            <ul className="flex flex-col gap-1.5">
                {visibleSteps.map((step) => (
                    <li key={step.key} className="flex items-center gap-2 text-[13px]">
                        <span
                            className={`flex h-4 w-4 shrink-0 items-center justify-center rounded-full ${step.status === "done"
                                    ? "bg-success text-white"
                                    : step.status === "active"
                                        ? "bg-accent-soft text-accent"
                                        : "bg-border text-transparent"
                                }`}
                        >
                            {step.status === "done" && <Check size={11} strokeWidth={3} />}
                            {step.status === "active" && <Loader2 size={11} className="animate-spin" />}
                        </span>
                        <span
                            className={
                                step.status === "pending"
                                    ? "text-ink-faint"
                                    : step.status === "active"
                                        ? "font-medium text-ink"
                                        : "text-ink-soft"
                            }
                        >
                            {step.label}
                        </span>
                    </li>
                ))}
            </ul>
        </div>
    );
}
