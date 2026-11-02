export type ResearchMode = "auto" | "documents" | "web";

export type DocumentStatus = "processing" | "ready" | "failed";

export interface DocumentMetadata {
    id: string;
    filename: string;
    status: DocumentStatus;
    chunks: number;
    file_type: string;
    size_bytes: number;
    error: string | null;
    created_at: string;
}

export interface Citation {
    index: number;
    type: "document" | "web";
    filename?: string | null;
    page?: number | null;
    snippet?: string | null;
    title?: string | null;
    url?: string | null;
    source?: string | null;
}

export interface ResearchResult {
    answer: string;
    citations: Citation[];
    sources_used: string[];
    retries: number;
    mode_used: ResearchMode;
}

export interface ChatMessage {
    id: string;
    role: "user" | "assistant";
    question?: string;
    result?: ResearchResult;
    error?: string;
    isStreaming?: boolean;
}

/** One step in the live agent progress tracker. */
export interface ProgressStep {
    key: string;
    label: string;
    status: "pending" | "active" | "done" | "skipped";
}

/** Raw SSE event names emitted by POST /api/research/stream */
export type StreamEventName =
    | "query_analyzed"
    | "source_selected"
    | "document_search_started"
    | "document_search_completed"
    | "web_search_started"
    | "web_search_completed"
    | "evaluation_started"
    | "retry_started"
    | "answer_generation_started"
    | "answer_completed"
    | "done"
    | "error";
