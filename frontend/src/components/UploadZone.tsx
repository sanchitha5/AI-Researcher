import { useCallback, useRef, useState } from "react";
import { UploadCloud } from "lucide-react";

interface UploadZoneProps {
    onFilesSelected: (files: File[]) => void;
    compact?: boolean;
}

const ACCEPTED_TYPES = ".pdf,.txt,.md,.docx";

export default function UploadZone({ onFilesSelected, compact = false }: UploadZoneProps) {
    const [isDragging, setIsDragging] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);

    const handleDrop = useCallback(
        (e: React.DragEvent) => {
            e.preventDefault();
            setIsDragging(false);
            const files = Array.from(e.dataTransfer.files);
            if (files.length) onFilesSelected(files);
        },
        [onFilesSelected]
    );

    const handleBrowse = () => inputRef.current?.click();

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = Array.from(e.target.files ?? []);
        if (files.length) onFilesSelected(files);
        e.target.value = "";
    };

    return (
        <div
            onDragOver={(e) => {
                e.preventDefault();
                setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            onClick={handleBrowse}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => e.key === "Enter" && handleBrowse()}
            className={`group flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed text-center transition-colors ${compact ? "gap-1.5 px-3 py-5" : "gap-2.5 px-6 py-10"
                } ${isDragging
                    ? "border-accent bg-accent-soft"
                    : "border-border-strong bg-surface hover:border-accent/40 hover:bg-accent-soft/40"
                }`}
        >
            <div
                className={`flex items-center justify-center rounded-full bg-white text-accent shadow-card ${compact ? "h-8 w-8" : "h-11 w-11"
                    }`}
            >
                <UploadCloud size={compact ? 15 : 20} />
            </div>
            <div>
                <p className={`font-medium text-ink ${compact ? "text-xs" : "text-sm"}`}>
                    {compact ? "Drop files or " : "Drop documents here, or "}
                    <span className="text-accent">browse</span>
                </p>
                {!compact && <p className="mt-1 text-xs text-ink-faint">PDF &middot; TXT &middot; MD &middot; DOCX</p>}
            </div>
            <input
                ref={inputRef}
                type="file"
                multiple
                accept={ACCEPTED_TYPES}
                className="hidden"
                onChange={handleInputChange}
            />
        </div>
    );
}
