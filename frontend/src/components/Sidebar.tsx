import { useRef } from "react";
import { AlertCircle } from "lucide-react";
import type { DocumentMetadata } from "../types/research";
import UploadZone from "./UploadZone";
import DocumentList from "./DocumentList";

interface SidebarProps {
    documents: DocumentMetadata[];
    onUpload: (files: File[]) => void;
    onDelete: (id: string) => void;
    backendWarning: string | null;
}

export default function Sidebar({ documents, onUpload, onDelete, backendWarning }: SidebarProps) {
    const scrollRef = useRef<HTMLDivElement>(null);

    return (
        <aside className="hidden w-72 shrink-0 flex-col border-r border-border bg-sidebar md:flex">
            <div className="flex h-14 shrink-0 items-center border-b border-border px-4">
                <span className="text-sm font-semibold text-ink">Documents</span>
            </div>

            <div className="flex flex-1 flex-col gap-4 overflow-y-auto px-3 py-4" ref={scrollRef}>
                <UploadZone onFilesSelected={onUpload} compact />

                <div>
                    <p className="mb-1.5 px-1 text-xs font-medium uppercase tracking-wide text-ink-faint">
                        Uploaded ({documents.length})
                    </p>
                    <DocumentList documents={documents} onDelete={onDelete} />
                </div>
            </div>

            {backendWarning && (
                <div className="mx-3 mb-3 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-2.5 py-2 text-[11px] leading-4 text-amber-800">
                    <AlertCircle size={13} className="mt-0.5 shrink-0" />
                    <span>{backendWarning}</span>
                </div>
            )}
        </aside>
    );
}
