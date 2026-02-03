<script lang="ts">
    import { onDestroy } from "svelte";
    import { t } from "$lib/i18n";
    import { streamChatMessage, type StreamStatus } from "$lib/api";

    type Message = {
        role: "user" | "assistant";
        content: string;
    };

    let {
        floating = false,
        onClose = undefined,
        stockCode = undefined,
        threadId = undefined,
        threadTitle = undefined,
        initialMessages = undefined,
        onMessagesChange = undefined,
        onThreadTitleChange = undefined,
    } = $props<{
        floating?: boolean;
        onClose?: () => void;
        stockCode?: string;
        threadId?: string;
        threadTitle?: string;
        initialMessages?: Message[];
        onMessagesChange?: (messages: Message[]) => void;
        onThreadTitleChange?: (title: string) => void;
    }>();

    const createThreadId = () =>
        `chat_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;

    let internalThreadId = $state(createThreadId());
    let messages = $state<Message[]>([]);
    let inputMessage = $state("");
    let streamStatus = $state<StreamStatus>("stopped");
    let error = $state<string | null>(null);
    let closeStream = $state<(() => void) | null>(null);

    let messageCounter = 0;

    function generateMessageId(): string {
        messageCounter++;
        return `msg_${internalThreadId}_${messageCounter}`;
    }

    const applyMessages = (next: Message[]) => {
        messages = next;
        onMessagesChange?.(next);
    };

    const deriveTitle = (content: string) => {
        const trimmed = content.trim();
        if (!trimmed) return "";
        return trimmed.length > 40 ? `${trimmed.slice(0, 40)}...` : trimmed;
    };

    function sendMessage() {
        if (
            !inputMessage.trim() ||
            streamStatus === "starting" ||
            streamStatus === "connecting"
        )
            return;

        const userMessage = inputMessage.trim();
        inputMessage = "";
        error = null;
        applyMessages([...messages, { role: "user", content: userMessage }]);
        if (!threadTitle || threadTitle.trim().length === 0) {
            const nextTitle = deriveTitle(userMessage);
            if (nextTitle) {
                onThreadTitleChange?.(nextTitle);
            }
        }

        let assistantContent = "";
        let messageAdded = false;
        const messageId = generateMessageId();

        closeStream = streamChatMessage(
            internalThreadId,
            messageId,
            userMessage,
            {
                onToken: (token: string) => {
                    assistantContent += token;
                    if (!messageAdded) {
                        applyMessages([
                            ...messages,
                            { role: "assistant", content: assistantContent },
                        ]);
                        messageAdded = true;
                    } else {
                        applyMessages(
                            messages.map((msg, idx) =>
                                idx === messages.length - 1
                                    ? { ...msg, content: assistantContent }
                                    : msg,
                            ),
                        );
                    }
                },
                onDone: () => {
                    closeStream = null;
                },
                onError: (err: Error) => {
                    error = err.message;
                    closeStream = null;
                    console.error("Chat error:", err.message);
                },
                onStatus: (s) => {
                    streamStatus = s;
                },
            },
            stockCode,
        );
    }

    function handleKeydown(event: KeyboardEvent) {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    }

    function clearChat() {
        applyMessages([]);
        error = null;
    }

    function stopStream() {
        if (closeStream) {
            closeStream();
            closeStream = null;
        }
    }

    const switchThread = (nextThreadId: string, seedMessages: Message[]) => {
        stopStream();
        internalThreadId = nextThreadId;
        messageCounter = 0;
        messages = seedMessages;
        streamStatus = "stopped";
        error = null;
    };

    $effect(() => {
        const seedMessages = initialMessages ? [...initialMessages] : [];
        if (threadId && threadId !== internalThreadId) {
            switchThread(threadId, seedMessages);
            return;
        }
        if (!threadId && messages.length === 0 && seedMessages.length > 0) {
            messages = seedMessages;
        }
    });

    onDestroy(() => stopStream());
</script>

<div class={`chat-window ${floating ? "floating" : ""}`}>
    <header class="chat-header">
        <div class="chat-title">
            <span aria-hidden="true">💬</span>
            <div>
                <p class="label">{threadTitle || $t("chat.title")}</p>
                <p class="muted">{$t("chat.subtitle")}</p>
            </div>
        </div>
        <div class="chat-actions">
            {#if stockCode}
                <div class="stock-pill" title={stockCode}>#{stockCode}</div>
            {/if}
            {#if streamStatus === "reconnecting"}
                <div
                    class="status-indicator reconnecting"
                    title={$t("chat.reconnecting") ?? "Reconnecting..."}
                >
                    🔄
                </div>
            {/if}
            {#if onClose}
                <button
                    class="icon-button"
                    onclick={onClose}
                    aria-label={$t("chat.close")}
                >
                    ✕
                </button>
            {/if}
        </div>
    </header>

    <div class="messages">
        {#if messages.length === 0}
            <div class="welcome">
                <div class="welcome-icon">🤖</div>
                <h2>{$t("chat.emptyTitle")}</h2>
                <p class="muted">{$t("chat.emptyLead")}</p>
                <div class="suggestions">
                    <button
                        class="pill"
                        onclick={() => {
                            inputMessage = $t("chat.suggestion1");
                            sendMessage();
                        }}
                    >
                        {$t("chat.suggestion1")}
                    </button>
                    <button
                        class="pill"
                        onclick={() => {
                            inputMessage = $t("chat.suggestion2");
                            sendMessage();
                        }}
                    >
                        {$t("chat.suggestion2")}
                    </button>
                    <button
                        class="pill"
                        onclick={() => {
                            inputMessage = $t("chat.suggestion3");
                            sendMessage();
                        }}
                    >
                        {$t("chat.suggestion3")}
                    </button>
                </div>
            </div>
        {:else}
            {#each messages as message}
                <div class={`message ${message.role}`}>
                    <div class="avatar">
                        {#if message.role === "user"}
                            👤
                        {:else if message.role === "assistant"}
                            🤖
                        {/if}
                    </div>
                    <div class="bubble">{message.content}</div>
                </div>
            {/each}

            {#if streamStatus === "starting" || streamStatus === "connecting" || streamStatus === "connected"}
                <div class="message assistant">
                    <div class="avatar">🤖</div>
                    <div class="bubble loading">
                        <span class="dot"></span>
                        <span class="dot"></span>
                        <span class="dot"></span>
                    </div>
                </div>
            {/if}

            {#if error}
                <div class="error-message">
                    <div class="avatar">⚠️</div>
                    <div class="bubble error-bubble">
                        <div>{error}</div>
                        <button
                            class="error-dismiss"
                            onclick={() => (error = null)}>✕</button
                        >
                    </div>
                </div>
            {/if}
        {/if}
    </div>

    <div class="input-row">
        {#if messages.length > 0}
            <button
                class="icon-button"
                onclick={clearChat}
                title={$t("chat.clear")}
                aria-label={$t("chat.clear")}
            >
                🗑️
            </button>
        {/if}
        <textarea
            bind:value={inputMessage}
            onkeydown={handleKeydown}
            placeholder={$t("chat.placeholder")}
            rows="1"
            disabled={streamStatus === "starting" ||
                streamStatus === "connecting"}
        ></textarea>
        <button
            class="primary"
            onclick={sendMessage}
            disabled={!inputMessage.trim() ||
                (streamStatus !== "stopped" &&
                    streamStatus !== "done" &&
                    streamStatus !== "error")}
        >
            {$t("chat.send")}
        </button>
    </div>
</div>

<style>
    .chat-window {
        display: flex;
        flex-direction: column;
        background: var(--color-panel);
        border: 1px solid var(--color-border-strong);
        border-radius: 16px;
        box-shadow: var(--shadow-lg);
        width: 720px;
        min-height: 400px;
        max-height: 80vh;
        flex-shrink: 0;
    }

    .chat-window.floating {
        width: 420px;
    }

    @media (max-width: 768px) {
        .chat-window {
            width: 100%;
            min-width: 280px;
        }
    }

    .chat-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 1.25rem;
        border-bottom: 1px solid var(--color-border);
        backdrop-filter: blur(6px);
    }

    .chat-title {
        display: flex;
        gap: 0.75rem;
        align-items: center;
    }

    .chat-actions {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .stock-pill {
        border: 1px solid var(--color-border);
        background: var(--color-surface);
        padding: 0.25rem 0.6rem;
        border-radius: 999px;
        font-size: 0.85rem;
        color: var(--color-text-secondary);
    }

    .label {
        margin: 0;
        font-weight: 700;
    }

    .muted {
        margin: 0;
        color: var(--color-text-secondary);
    }

    .status-indicator {
        font-size: 1rem;
        animation: pulse 1.5s infinite;
    }

    .status-indicator.reconnecting {
        animation: spin 1s linear infinite;
    }

    @keyframes spin {
        from {
            transform: rotate(0deg);
        }
        to {
            transform: rotate(360deg);
        }
    }

    @keyframes pulse {
        0%,
        100% {
            opacity: 1;
        }
        50% {
            opacity: 0.6;
        }
    }

    .messages {
        flex: 1;
        overflow-y: auto;
        padding: 1.25rem;
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
        min-width: 0;
    }

    .welcome {
        text-align: center;
        padding: 1rem;
        border: 1px dashed var(--color-border);
        border-radius: 12px;
        width: 100%;
    }

    .welcome-icon {
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }

    .suggestions {
        margin-top: 1rem;
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        justify-content: center;
    }

    .pill {
        border: 1px solid var(--color-border);
        padding: 0.35rem 0.75rem;
        border-radius: 999px;
        background: var(--color-surface);
        cursor: pointer;
        transition:
            border-color 0.2s,
            transform 0.15s;
    }

    .pill:hover {
        border-color: var(--color-primary);
        transform: translateY(-1px);
    }

    .message {
        display: flex;
        gap: 0.5rem;
        max-width: 90%;
    }

    .message.user {
        align-self: flex-end;
        flex-direction: row-reverse;
    }

    .avatar {
        width: 32px;
        height: 32px;
        border-radius: 10px;
        background: var(--color-surface);
        display: grid;
        place-items: center;
        border: 1px solid var(--color-border);
        flex-shrink: 0;
    }

    .bubble {
        padding: 0.65rem 0.85rem;
        border-radius: 12px;
        background: var(--color-surface-strong);
        border: 1px solid var(--color-border);
        line-height: 1.5;
        word-break: break-word;
    }

    .message.user .bubble {
        background: var(--color-primary);
        color: #fff;
        border-color: var(--color-primary);
    }

    .loading {
        display: flex;
        gap: 0.25rem;
        align-items: center;
        min-width: 50px;
    }

    .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--color-text-secondary);
        animation: bounce 1.4s infinite ease-in-out both;
    }

    .dot:nth-child(1) {
        animation-delay: -0.32s;
    }

    .dot:nth-child(2) {
        animation-delay: -0.16s;
    }

    @keyframes bounce {
        0%,
        80%,
        100% {
            transform: scale(0);
        }
        40% {
            transform: scale(1);
        }
    }

    .input-row {
        display: flex;
        gap: 0.75rem;
        padding: 1rem 1.25rem;
        border-top: 1px solid var(--color-border);
        align-items: center;
        background: var(--color-surface);
    }

    textarea {
        flex: 1;
        resize: none;
        min-height: 44px;
        max-height: 120px;
        border-radius: 12px;
        border: 1px solid var(--color-border);
        padding: 0.65rem 0.85rem;
        font: inherit;
        background: var(--color-panel);
    }

    textarea:focus {
        outline: 2px solid var(--color-primary);
        border-color: var(--color-primary);
    }

    textarea:disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }

    .icon-button {
        border: 1px solid var(--color-border);
        background: var(--color-panel);
        border-radius: 10px;
        padding: 0.5rem;
        cursor: pointer;
        transition: border-color 0.2s;
    }

    .icon-button:hover {
        border-color: var(--color-primary);
    }

    .primary {
        background: var(--color-primary);
        color: #fff;
        border: none;
        border-radius: 12px;
        padding: 0.65rem 1rem;
        cursor: pointer;
        box-shadow: var(--shadow-sm);
        font-weight: 600;
        transition: opacity 0.2s;
    }

    .primary:hover:not(:disabled) {
        opacity: 0.9;
    }

    .primary:disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }

    .danger {
        background: #ef4444;
        color: #fff;
        border: none;
        border-radius: 12px;
        padding: 0.65rem 1rem;
        cursor: pointer;
        box-shadow: var(--shadow-sm);
        font-weight: 600;
        transition: opacity 0.2s;
    }

    .danger:hover {
        opacity: 0.9;
    }

    .error-message {
        display: flex;
        gap: 0.5rem;
        max-width: 90%;
        align-self: flex-start;
    }

    .error-bubble {
        background: rgba(239, 68, 68, 0.1) !important;
        border-color: #ef4444 !important;
        color: #dc2626;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .error-dismiss {
        background: none;
        border: none;
        color: #dc2626;
        cursor: pointer;
        font-size: 1rem;
        padding: 0;
        flex-shrink: 0;
    }

    .error-dismiss:hover {
        opacity: 0.7;
    }
</style>
