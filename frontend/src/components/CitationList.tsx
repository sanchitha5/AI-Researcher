import { FileText, Globe } from "lucide-react";
import type { Citation } from "../types/research";

interface CitationListProps {
    citations: Citation[];
}

export default function CitationList({ citations }: CitationListProps) {
    if (citations.length === 0) return null;

    return (
        <div className="mt-4 border-t border-border pt-3.5">
            <p className="mb-2 text-xs font-medium uppercase tracking-wide text-ink-faint">Sources</p>
            <ul className="flex flex-col gap-2">
                {citations.map((c) => (
                    <li key={c.index} className="flex items-start gap-2 text-[13px]">
                        <span className="mt-0.5 shrink-0 text-ink-faint">[{c.index}]</span>
                        {c.type === "document" ? (
                            <span className="flex items-center gap-1.5 text-ink-soft">
                                <FileText size={13} className="shrink-0 text-ink-faint" />
                                {c.filename} &mdash; Page {c.page}
                            </span>
                        ) : (
                            <a
                                href={c.url ?? "#"}
                                target="_blank"
                                rel="noreferrer"
                                className="flex items-center gap-1.5 text-accent hover:underline"
                            >
                                <Globe size={13} className="shrink-0 text-ink-faint" />
                                <span className="text-ink-soft">{c.source}</span> &mdash; {c.title}
                            </a>
                        )}
                    </li>
                ))}
            </ul>
        </div>
    );
}
