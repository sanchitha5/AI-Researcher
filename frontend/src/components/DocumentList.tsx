import { CheckCircle2, FileText, Loader2, TriangleAlert, X } from "lucide-react";
import type { DocumentMetadata } from "../types/research";

interface DocumentListProps {
    documents: DocumentMetadata[];
    onDelete: (id: string) => void;
}

export default function DocumentList({ documents, onDelete }: DocumentListProps) {
    if (documents.length === 0) {
        return <p className="px-1 text-xs text-ink-faint">No documents yet.</p>;
    }

    return (
        <ul className="flex flex-col gap-1.5">
            {documents.map((doc) => (
                <li
                    key={doc.id}
                    className="group flex items-start gap-2 rounded-lg border border-transparent px-2 py-1.5 hover:border-border hover:bg-white"
                >
                    <div className="mt-0.5 shrink-0 text-ink-faint">
                        <FileText size={15} />
                    </div>
                    <div className="min-w-0 flex-1">
                        <p className="truncate text-xs font-medium text-ink" title={doc.filename}>
                            {doc.filename}
                        </p>
                        <div className="mt-0.5 flex items-center gap-1 text-[11px]">
                            {doc.status === "processing" && (
                                <span className="flex items-center gap-1 text-ink-faint">
                                    <Loader2 size={11} className="animate-spin" />
                                    Processing&hellip;
                                </span>
                            )}
                            {doc.status === "ready" && (
                                <span className="flex items-center gap-1 text-success">
                                    <CheckCircle2 size={11} />
                                    Ready &middot; {doc.chunks} chunks
                                </span>
                            )}
                            {doc.status === "failed" && (
                                <span className="flex items-center gap-1 text-red-600" title={doc.error ?? undefined}>
                                    <TriangleAlert size={11} />
                                    Failed
                                </span>
                            )}
                        </div>
                    </div>
                    <button
                        onClick={() => onDelete(doc.id)}
                        className="mt-0.5 shrink-0 rounded p-0.5 text-ink-faint opacity-0 transition-opacity hover:bg-surface hover:text-ink group-hover:opacity-100"
                        aria-label={`Remove ${doc.filename}`}
                    >
                        <X size={13} />
                    </button>
                </li>
            ))}
        </ul>
    );
}
