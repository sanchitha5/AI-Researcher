import type { DocumentMetadata, ResearchMode, StreamEventName } from "../types/research";

// In dev, Vite proxies /api and /health to the FastAPI backend (see vite.config.ts).
// In production, set VITE_API_BASE_URL to the deployed backend's origin.
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export class ApiError extends Error {
    status: number;
    constructor(message: string, status: number) {
        super(message);
        this.status = status;
    }
}

async function handleJsonResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
        let detail = `Request failed with status ${response.status}`;
        try {
            const body = await response.json();
            if (body?.detail) detail = body.detail;
        } catch {
            // response wasn't JSON — keep the generic message
        }
        throw new ApiError(detail, response.status);
    }
    return response.json() as Promise<T>;
}

export async function checkHealth(): Promise<{
    status: string;
    gemini_configured?: boolean;
    groq_configured: boolean;
    tavily_configured: boolean;
}> {
    const response = await fetch(`${API_BASE}/health`);
    return handleJsonResponse(response);
}

export async function uploadDocument(file: File): Promise<DocumentMetadata & { error?: string | null }> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE}/api/documents/upload`, {
        method: "POST",
        body: formData,
    });
    return handleJsonResponse(response);
}

export async function listDocuments(): Promise<DocumentMetadata[]> {
    const response = await fetch(`${API_BASE}/api/documents`);
    const data = await handleJsonResponse<{ documents: DocumentMetadata[] }>(response);
    return data.documents;
}

export async function deleteDocument(id: string): Promise<void> {
    const response = await fetch(`${API_BASE}/api/documents/${id}`, { method: "DELETE" });
    await handleJsonResponse(response);
}

export interface StreamCallbacks {
    onEvent: (event: StreamEventName, data: any) => void;
    onError: (message: string) => void;
}

/**
 * Calls POST /api/research/stream and parses the Server-Sent Events
 * response manually using the Fetch streaming body reader (works the
 * same everywhere, no EventSource-only limitations like GET-only).
 */
export async function streamResearch(
    question: string,
    mode: ResearchMode,
    documentIds: string[],
    callbacks: StreamCallbacks,
    signal?: AbortSignal
): Promise<void> {
    let response: Response;
    try {
        response = await fetch(`${API_BASE}/api/research/stream`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question, mode, document_ids: documentIds }),
            signal,
        });
    } catch {
        callbacks.onError("Could not reach the research backend. Is it running?");
        return;
    }

    if (!response.ok || !response.body) {
        let detail = "Unable to start research.";
        try {
            const body = await response.json();
            if (body?.detail) detail = body.detail;
        } catch {
            // ignore
        }
        callbacks.onError(detail);
        return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const chunks = buffer.split("\n\n");
        buffer = chunks.pop() ?? "";

        for (const chunk of chunks) {
            const lines = chunk.split("\n");
            let eventName: string | null = null;
            let dataLine = "";

            for (const line of lines) {
                if (line.startsWith("event:")) eventName = line.slice(6).trim();
                if (line.startsWith("data:")) dataLine += line.slice(5).trim();
            }

            if (!eventName) continue;

            try {
                const data = dataLine ? JSON.parse(dataLine) : {};
                if (eventName === "error") {
                    callbacks.onError(data.message ?? "The research agent encountered an error.");
                } else {
                    callbacks.onEvent(eventName as StreamEventName, data);
                }
            } catch {
                // Malformed event — skip it rather than crashing the whole stream.
            }
        }
    }
}
