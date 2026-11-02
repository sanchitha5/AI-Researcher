import { useCallback, useEffect, useRef, useState } from "react";
import { AlertCircle } from "lucide-react";
import Header from "../components/Header";
import Sidebar from "../components/Sidebar";
import EmptyState from "../components/EmptyState";
import AgentProgress from "../components/AgentProgress";
import AnswerCard from "../components/AnswerCard";
import QuestionInput from "../components/QuestionInput";
import ResearchModeSelector from "../components/ResearchModeSelector";
import SourcePanel from "../components/SourcePanel";
import {
    checkHealth,
    deleteDocument,
    listDocuments,
    streamResearch,
    uploadDocument,
} from "../services/api";
import { applyStreamEvent, buildInitialSteps } from "../services/progress";
import type {
    ChatMessage,
    Citation,
    DocumentMetadata,
    ProgressStep,
    ResearchMode,
} from "../types/research";

let messageIdCounter = 0;
const nextId = () => `msg-${++messageIdCounter}-${Date.now()}`;

export default function ResearchPage() {
    const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [mode, setMode] = useState<ResearchMode>("auto");
    const [question, setQuestion] = useState("");
    const [isResearching, setIsResearching] = useState(false);
    const [progressSteps, setProgressSteps] = useState<ProgressStep[]>(buildInitialSteps("auto"));
    const [backendWarning, setBackendWarning] = useState<string | null>(null);
    const [activeSources, setActiveSources] = useState<Citation[] | null>(null);

    const scrollRef = useRef<HTMLDivElement>(null);
    const abortRef = useRef<AbortController | null>(null);

    // --- Initial load: documents + backend health check ---
    useEffect(() => {
        refreshDocuments();
        checkHealth()
            .then((health) => {
                const missing: string[] = [];
                if (!health.groq_configured) missing.push("GROQ_API_KEY");
                if (!health.tavily_configured) missing.push("TAVILY_API_KEY");
                if (missing.length) {
                    setBackendWarning(
                        `Missing backend configuration: ${missing.join(", ")}. Add these to backend/.env to enable research.`
                    );
                }
            })
            .catch(() => {
                setBackendWarning("Could not reach the backend at http://localhost:8000. Is it running?");
            });
    }, []);

    useEffect(() => {
        scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
    }, [messages, progressSteps]);

    const refreshDocuments = useCallback(async () => {
        try {
            const docs = await listDocuments();
            setDocuments(docs);
            // Documents that were still "processing" on the last fetch might be
            // done now — poll briefly if anything is still in progress.
            if (docs.some((d) => d.status === "processing")) {
                setTimeout(refreshDocuments, 1500);
            }
        } catch {
            // Non-fatal — the sidebar will just show whatever we last had.
        }
    }, []);

    const handleUpload = useCallback(
        async (files: File[]) => {
            for (const file of files) {
                try {
                    await uploadDocument(file);
                } catch {
                    // Errors are recoverable via the document list status; still refresh.
                }
            }
            refreshDocuments();
        },
        [refreshDocuments]
    );

    const handleDeleteDocument = useCallback(async (id: string) => {
        setDocuments((prev) => prev.filter((d) => d.id !== id));
        try {
            await deleteDocument(id);
        } catch {
            refreshDocuments();
        }
    }, [refreshDocuments]);

    const handleNewResearch = useCallback(() => {
        abortRef.current?.abort();
        setMessages([]);
        setQuestion("");
        setIsResearching(false);
        setActiveSources(null);
        setProgressSteps(buildInitialSteps(mode));
    }, [mode]);

    const runResearch = useCallback(
        async (questionText: string) => {
            const trimmed = questionText.trim();
            if (!trimmed || isResearching) return;

            const userMessage: ChatMessage = { id: nextId(), role: "user", question: trimmed };
            const assistantMessage: ChatMessage = { id: nextId(), role: "assistant", isStreaming: true };

            setMessages((prev) => [...prev, userMessage, assistantMessage]);
            setQuestion("");
            setIsResearching(true);
            setProgressSteps(buildInitialSteps(mode));

            const controller = new AbortController();
            abortRef.current = controller;

            const readyDocumentIds = documents.filter((d) => d.status === "ready").map((d) => d.id);

            await streamResearch(
                trimmed,
                mode,
                readyDocumentIds,
                {
                    onEvent: (event, data) => {
                        setProgressSteps((prev) => applyStreamEvent(prev, event, data));

                        if (event === "done") {
                            setMessages((prev) =>
                                prev.map((m) =>
                                    m.id === assistantMessage.id ? { ...m, isStreaming: false, result: data } : m
                                )
                            );
                            setIsResearching(false);
                        }
                    },
                    onError: (message) => {
                        setMessages((prev) =>
                            prev.map((m) => (m.id === assistantMessage.id ? { ...m, isStreaming: false, error: message } : m))
                        );
                        setIsResearching(false);
                    },
                },
                controller.signal
            );

            setIsResearching(false);
        },
        [mode, isResearching, documents]
    );

    const hasActiveSession = messages.length > 0;

    return (
        <div className="flex h-screen w-full overflow-hidden bg-canvas text-ink">
            <Sidebar
                documents={documents}
                onUpload={handleUpload}
                onDelete={handleDeleteDocument}
                backendWarning={backendWarning}
            />

            <div className="flex min-w-0 flex-1 flex-col">
                <Header onNewResearch={handleNewResearch} hasActiveSession={hasActiveSession} />

                <div className="flex min-h-0 flex-1">
                    <div className="flex min-w-0 flex-1 flex-col">
                        {!hasActiveSession ? (
                            <EmptyState
                                mode={mode}
                                onModeChange={setMode}
                                question={question}
                                onQuestionChange={setQuestion}
                                onSubmit={() => runResearch(question)}
                                disabled={isResearching}
                            />
                        ) : (
                            <>
                                <div ref={scrollRef} className="flex-1 overflow-y-auto">
                                    <div className="mx-auto flex max-w-2xl flex-col gap-6 px-6 py-6">
                                        {messages.map((message, i) => {
                                            const isLastAssistant =
                                                message.role === "assistant" && i === messages.length - 1;
                                            return (
                                                <div key={message.id} className="animate-fadeIn">
                                                    {message.role === "user" ? (
                                                        <div>
                                                            <p className="mb-1 text-xs font-medium text-ink-faint">You</p>
                                                            <p className="text-[15px] leading-relaxed text-ink">{message.question}</p>
                                                        </div>
                                                    ) : (
                                                        <div>
                                                            <p className="mb-2 text-xs font-medium text-ink-faint">AI Research Agent</p>

                                                            {message.isStreaming && isLastAssistant && (
                                                                <AgentProgress steps={progressSteps} />
                                                            )}

                                                            {message.error && (
                                                                <div className="flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 px-3.5 py-3 text-sm text-red-700">
                                                                    <AlertCircle size={16} className="mt-0.5 shrink-0" />
                                                                    <div>
                                                                        <p className="font-medium">Unable to complete research.</p>
                                                                        <p className="mt-0.5 text-red-600">{message.error}</p>
                                                                    </div>
                                                                </div>
                                                            )}

                                                            {message.result && (
                                                                <AnswerCard
                                                                    result={message.result}
                                                                    onViewSources={() => setActiveSources(message.result!.citations)}
                                                                />
                                                            )}
                                                        </div>
                                                    )}
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>

                                <div className="border-t border-border bg-white px-6 py-4">
                                    <div className="mx-auto flex max-w-2xl flex-col gap-2.5">
                                        <ResearchModeSelector mode={mode} onChange={setMode} compact />
                                        <QuestionInput
                                            value={question}
                                            onChange={setQuestion}
                                            onSubmit={() => runResearch(question)}
                                            disabled={isResearching}
                                            placeholder="Ask a follow-up question..."
                                        />
                                    </div>
                                </div>
                            </>
                        )}
                    </div>

                    {activeSources && (
                        <SourcePanel citations={activeSources} onClose={() => setActiveSources(null)} />
                    )}
                </div>
            </div>
        </div>
    );
}
