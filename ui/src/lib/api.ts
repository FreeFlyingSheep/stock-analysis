import type {
    StockApiResponse,
    StockDetailApiResponse,
    AnalysisApiResponse,
    AnalysisDetailApiResponse,
    ChatStartIn,
    ChatStartOut,
    StreamEvent,
    ChatThreadsResponse,
    ChatThreadDetailResponse,
    ChatThreadOutApi,
    ChatThreadUpdateIn,
    ChatThreadCreateIn,
} from "./types";
import { get } from "svelte/store";
import { locale as localeStore, translateStatic } from "./i18n";

const API_BASE_URL = "/api";

async function fetchApi<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`);
    if (!response.ok) {
        throw new Error(
            translateStatic("errors.apiError", {
                status: response.status.toString(),
                statusText: response.statusText,
            }),
        );
    }
    return response.json();
}

async function fetchApiJson<T>(
    endpoint: string,
    method: "POST" | "PATCH" | "DELETE",
    body?: unknown,
): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method,
        headers: body ? { "Content-Type": "application/json" } : undefined,
        body: body ? JSON.stringify(body) : undefined,
    });
    if (!response.ok) {
        throw new Error(
            translateStatic("errors.apiError", {
                status: response.status.toString(),
                statusText: response.statusText,
            }),
        );
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

export async function getChatThreads(): Promise<ChatThreadsResponse> {
    return fetchApi<ChatThreadsResponse>("/chats");
}

export async function getChatThreadDetails(
    threadId: string,
): Promise<ChatThreadDetailResponse> {
    return fetchApi<ChatThreadDetailResponse>(`/chats/${threadId}`);
}

export async function createChatThread(
    payload: ChatThreadCreateIn,
): Promise<ChatThreadOutApi> {
    return fetchApiJson<ChatThreadOutApi>("/chats", "POST", payload);
}

export async function updateChatThread(
    threadId: string,
    payload: ChatThreadUpdateIn,
): Promise<ChatThreadOutApi> {
    return fetchApiJson<ChatThreadOutApi>(
        `/chats/${threadId}`,
        "PATCH",
        payload,
    );
}

export async function deleteChatThread(
    threadId: string,
): Promise<ChatThreadOutApi> {
    return fetchApiJson<ChatThreadOutApi>(`/chats/${threadId}`, "DELETE");
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
    let haltReconnect = false;
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
            id: "0",
            event: event.type as StreamEvent["event"],
            data: String(event.data),
        };
    };

    const resolveLocale = (): string => {
        const current = get(localeStore);
        return current === "zh" ? "zh-CN" : "en-US";
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
            options.onError(
                new Error(translateStatic("errors.invalidTokenPayload")),
            );
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
                    : translateStatic("errors.serverError");
            setStatus("error");
            haltReconnect = true;
            eventSource.close();
            es = null;
            options.onError(new Error(errorMsg));
        });

        eventSource.addEventListener("ping", () => {
            resetPingTimeout();
        });

        eventSource.onerror = () => {
            if (!closed && !haltReconnect && lastStatus !== "done") {
                attemptReconnect();
            }
        };
    };

    const setupStream = async (streamUrl: string | undefined | null) => {
        if (closed) return;
        if (!streamUrl) {
            setStatus("error");
            options.onError(
                new Error(translateStatic("errors.missingStreamUrl")),
            );
            return;
        }

        setStatus("connecting");
        const resolvedUrl =
            streamUrl.startsWith("http://") ||
            streamUrl.startsWith("https://") ||
            streamUrl.startsWith("/api/")
                ? streamUrl
                : `${API_BASE_URL}${streamUrl.startsWith("/") ? "" : "/"}${streamUrl}`;
        es = new EventSource(resolvedUrl);

        es.onopen = () => {
            setStatus("connected");
            resetPingTimeout();
        };

        attachEventListeners(es);
    };

    const attemptReconnect = async () => {
        if (
            closed ||
            haltReconnect ||
            reconnectAttempts >= MAX_RECONNECT_ATTEMPTS
        ) {
            if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
                setStatus("error");
                options.onError(
                    new Error(translateStatic("errors.reconnectFailed")),
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
                        threadId: threadId,
                        messageId: messageId,
                        message: message,
                        locale: resolveLocale(),
                        stockCode: stockCode ?? null,
                    } as ChatStartIn),
                    signal: abort.signal,
                });

                if (!res.ok) {
                    const text = await res.text().catch(() => "");
                    throw new Error(
                        translateStatic("errors.startFailed", {
                            status: res.status.toString(),
                            error: text,
                        }),
                    );
                }

                const { streamUrl } = (await res.json()) as ChatStartOut;

                // Close old connection
                es?.close();
                es = null;

                // Setup new stream
                await setupStream(streamUrl);
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
                        new Error(translateStatic("errors.reconnectFailed")),
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
                    threadId: threadId,
                    messageId: messageId,
                    message: message,
                    locale: resolveLocale(),
                    stockCode: stockCode ?? null,
                } as ChatStartIn),
                signal: abort.signal,
            });

            if (!res.ok) {
                const text = await res.text().catch(() => "");
                setStatus("error");
                throw new Error(
                    translateStatic("errors.startFailed", {
                        status: res.status.toString(),
                        error: text,
                    }),
                );
            }

            const { streamUrl } = (await res.json()) as ChatStartOut;

            await setupStream(streamUrl);
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
