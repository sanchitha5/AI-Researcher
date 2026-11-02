import { FileText, Globe, X } from "lucide-react";
import type { Citation } from "../types/research";

interface SourcePanelProps {
    citations: Citation[];
    onClose: () => void;
}

export default function SourcePanel({ citations, onClose }: SourcePanelProps) {
    const docCitations = citations.filter((c) => c.type === "document");
    const webCitations = citations.filter((c) => c.type === "web");

    return (
        <aside className="animate-slideUp flex h-full w-full max-w-sm shrink-0 flex-col border-l border-border bg-sidebar">
            <div className="flex h-14 shrink-0 items-center justify-between border-b border-border px-4">
                <h2 className="text-sm font-semibold text-ink">Sources</h2>
                <button
                    onClick={onClose}
                    className="rounded p-1 text-ink-faint hover:bg-surface hover:text-ink"
                    aria-label="Close source panel"
                >
                    <X size={16} />
                </button>
            </div>

            <div className="flex-1 overflow-y-auto px-4 py-4">
                {docCitations.length > 0 && (
                    <div className="mb-6">
                        <p className="mb-2 flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-ink-faint">
                            <FileText size={12} /> Documents
                        </p>
                        <div className="flex flex-col gap-2.5">
                            {docCitations.map((c) => (
                                <div key={c.index} className="rounded-lg border border-border bg-white p-3">
                                    <p className="text-xs font-semibold text-ink">
                                        [{c.index}] {c.filename}
                                    </p>
                                    <p className="mt-0.5 text-[11px] text-ink-faint">Page {c.page}</p>
                                    <p className="mt-2 text-[13px] leading-5 text-ink-soft">&ldquo;{c.snippet}&rdquo;</p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {webCitations.length > 0 && (
                    <div>
                        <p className="mb-2 flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-ink-faint">
                            <Globe size={12} /> Web
                        </p>
                        <div className="flex flex-col gap-2.5">
                            {webCitations.map((c) => (
                                <a
                                    key={c.index}
                                    href={c.url ?? "#"}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="block rounded-lg border border-border bg-white p-3 transition-colors hover:border-accent/40"
                                >
                                    <p className="text-xs font-semibold text-ink">
                                        [{c.index}] {c.source}
                                    </p>
                                    <p className="mt-0.5 text-[13px] leading-5 text-ink-soft">{c.title}</p>
                                    <p className="mt-1.5 truncate text-[11px] text-accent">{c.url}</p>
                                </a>
                            ))}
                        </div>
                    </div>
                )}

                {citations.length === 0 && <p className="text-sm text-ink-faint">No sources for this answer.</p>}
            </div>
        </aside>
    );
}
