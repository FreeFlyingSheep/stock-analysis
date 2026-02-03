import type {
    StockApiResponse,
    StockDetailApiResponse,
    AnalysisApiResponse,
    AnalysisDetailApiResponse,
    ChatStartIn,
    ChatStartOut,
    StreamEvent,
} from "./types";

const API_BASE_URL = "/api";

async function fetchApi<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`);
    if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
    }
    return response.json();
}

export interface GetStocksParams {
    page?: number;
    size?: number;
    classification?: string;
    industry?: string;
}

export async function getStocks(
    params: GetStocksParams = {},
): Promise<StockApiResponse> {
    const searchParams = new URLSearchParams();
    if (params.page) searchParams.set("page", params.page.toString());
    if (params.size) searchParams.set("size", params.size.toString());
    if (params.classification)
        searchParams.set("classification", params.classification);
    if (params.industry) searchParams.set("industry", params.industry);

    const query = searchParams.toString();
    return fetchApi<StockApiResponse>(`/stocks${query ? `?${query}` : ""}`);
}

export async function getStockDetails(
    stockCode: string,
): Promise<StockDetailApiResponse> {
    return fetchApi<StockDetailApiResponse>(`/stocks/${stockCode}`);
}

export interface GetAnalysisParams {
    page?: number;
    size?: number;
}

export async function getAnalysis(
    params: GetAnalysisParams = {},
): Promise<AnalysisApiResponse> {
    const searchParams = new URLSearchParams();
    if (params.page) searchParams.set("page", params.page.toString());
    if (params.size) searchParams.set("size", params.size.toString());

    const query = searchParams.toString();
    return fetchApi<AnalysisApiResponse>(
        `/analysis${query ? `?${query}` : ""}`,
    );
}

export async function getAnalysisDetails(
    stockCode: string,
): Promise<AnalysisDetailApiResponse> {
    return fetchApi<AnalysisDetailApiResponse>(`/analysis/${stockCode}`);
}

export type StreamStatus =
    | "starting"
    | "connecting"
    | "connected"
    | "reconnecting"
    | "done"
    | "stopped"
    | "error";

export interface StreamChatOptions {
    onToken: (token: string) => void;
    onDone: () => void;
    onError: (error: Error) => void;
    onStatus?: (status: StreamStatus) => void;
}

export function streamChatMessage(
    threadId: string,
    messageId: string,
    message: string,
    options: StreamChatOptions,
    stockCode?: string,
): () => void {
    const abort = new AbortController();
    let es: EventSource | null = null;
    let closed = false;
    let pingTimeout: ReturnType<typeof setTimeout> | null = null;
    let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
    let reconnectAttempts = 0;
    const MAX_RECONNECT_ATTEMPTS = 10;
    const PING_TIMEOUT_MS = 45000;

    let lastStatus: StreamStatus | null = null;
    const setStatus = (s: StreamStatus) => {
        if (lastStatus === s) return;
        lastStatus = s;
        options.onStatus?.(s);
    };

    const clearAllTimeouts = () => {
        if (pingTimeout !== null) {
            clearTimeout(pingTimeout);
            pingTimeout = null;
        }
        if (reconnectTimeout !== null) {
            clearTimeout(reconnectTimeout);
            reconnectTimeout = null;
        }
    };

    const resetPingTimeout = () => {
        if (pingTimeout !== null) {
            clearTimeout(pingTimeout);
        }
        pingTimeout = setTimeout(() => {
            if (!closed && lastStatus !== "done" && lastStatus !== "error") {
                console.warn(
                    "No keep-alive ping received - connection may be stale",
                );
                attemptReconnect();
            }
        }, PING_TIMEOUT_MS);
    };

    const parseEventPayload = (event: MessageEvent): StreamEvent | null => {
        if (typeof event.data !== "string" || event.data.length === 0) {
            return null;
        }

        try {
            const parsed = JSON.parse(event.data) as StreamEvent;
            if (parsed && typeof parsed === "object" && "data" in parsed) {
                return parsed;
            }
        } catch {
            // Fall back to raw string payloads.
        }

        return {
            id: 0,
            event: event.type as StreamEvent["event"],
            data: String(event.data),
        };
    };

    const attachEventListeners = (eventSource: EventSource) => {
        eventSource.addEventListener("token", (event: MessageEvent) => {
            const streamEvent = parseEventPayload(event);
            resetPingTimeout();
            if (streamEvent) {
                options.onToken(streamEvent.data);
                return;
            }

            setStatus("error");
            options.onError(new Error("Invalid token payload"));
        });

        eventSource.addEventListener("done", () => {
            clearAllTimeouts();
            setStatus("done");
            eventSource.close();
            es = null;
            options.onDone();
        });

        eventSource.addEventListener("error", (event: MessageEvent) => {
            clearAllTimeouts();
            const streamEvent = parseEventPayload(event);
            const errorMsg =
                streamEvent?.data && streamEvent.data.length > 0
                    ? streamEvent.data
                    : "server error";
            setStatus("error");
            eventSource.close();
            es = null;
            options.onError(new Error(errorMsg));
        });

        eventSource.addEventListener("ping", () => {
            resetPingTimeout();
        });

        eventSource.onerror = () => {
            if (!closed && lastStatus !== "done") {
                attemptReconnect();
            }
        };
    };

    const setupStream = async (streamUrl: string) => {
        if (closed) return;

        setStatus("connecting");
        es = new EventSource(streamUrl);

        es.onopen = () => {
            setStatus("connected");
            resetPingTimeout();
        };

        attachEventListeners(es);
    };

    const attemptReconnect = async () => {
        if (closed || reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
            if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
                setStatus("error");
                options.onError(
                    new Error("Failed to reconnect: max attempts exceeded"),
                );
            }
            return;
        }

        reconnectAttempts++;
        const backoffMs = Math.min(
            1000 * Math.pow(2, reconnectAttempts - 1),
            30000,
        );

        console.log(
            `Reconnecting (attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS}) in ${backoffMs}ms...`,
        );
        setStatus("reconnecting");

        reconnectTimeout = setTimeout(async () => {
            if (closed) return;

            try {
                const res = await fetch("/api/chat/start", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        thread_id: threadId,
                        message_id: messageId,
                        message: message,
                        stock_code: stockCode ?? null,
                    } as ChatStartIn),
                    signal: abort.signal,
                });

                if (!res.ok) {
                    const text = await res.text().catch(() => "");
                    throw new Error(`Start failed: ${res.status} ${text}`);
                }

                const { stream_url } = (await res.json()) as ChatStartOut;

                // Close old connection
                es?.close();
                es = null;

                // Setup new stream
                await setupStream(stream_url);
                reconnectAttempts = 0; // Reset on successful reconnect
                console.log("Reconnected successfully");
            } catch (err) {
                console.warn(
                    `Reconnect attempt ${reconnectAttempts} failed:`,
                    err instanceof Error ? err.message : String(err),
                );
                if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS && !closed) {
                    attemptReconnect();
                } else {
                    setStatus("error");
                    options.onError(
                        new Error("Failed to reconnect: max attempts exceeded"),
                    );
                }
            }
        }, backoffMs);
    };

    (async () => {
        try {
            setStatus("starting");

            const res = await fetch("/api/chat/start", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    thread_id: threadId,
                    message_id: messageId,
                    message: message,
                    stock_code: stockCode ?? null,
                } as ChatStartIn),
                signal: abort.signal,
            });

            if (!res.ok) {
                const text = await res.text().catch(() => "");
                setStatus("error");
                throw new Error(`Start failed: ${res.status} ${text}`);
            }

            const { stream_url } = (await res.json()) as ChatStartOut;

            await setupStream(stream_url);
        } catch (e) {
            clearAllTimeouts();
            if (abort.signal.aborted) return;
            setStatus("error");
            options.onError(e instanceof Error ? e : new Error(String(e)));
        }
    })();

    return () => {
        closed = true;
        clearAllTimeouts();
        abort.abort();
        es?.close();
        es = null;
        setStatus("stopped");
    };
}
