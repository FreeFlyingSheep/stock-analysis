<script lang="ts">
    import { t } from "$lib/i18n";
    import { streamChatMessage } from "$lib/api";

    type Message = {
        role: "user" | "assistant";
        content: string;
    };

    let { floating = false, onClose = undefined } = $props<{
        floating?: boolean;
        onClose?: () => void;
    }>();

    let messages = $state<Message[]>([]);
    let inputMessage = $state("");
    let isLoading = $state(false);
    let error = $state<string | null>(null);

    async function sendMessage() {
        if (!inputMessage.trim() || isLoading) return;

        const userMessage = inputMessage.trim();
        inputMessage = "";
        messages = [...messages, { role: "user", content: userMessage }];
        isLoading = true;
        error = null;

        let currentAssistantMessage = "";
        let hasStartedResponse = false;

        try {
            for await (const event of streamChatMessage(userMessage)) {
                if (event.type === "token") {
                    if (!hasStartedResponse) {
                        hasStartedResponse = true;
                        messages = [
                            ...messages,
                            { role: "assistant", content: event.data },
                        ];
                    } else {
                        currentAssistantMessage += event.data;
                        messages = messages.map((msg, idx) =>
                            idx === messages.length - 1
                                ? {
                                      ...msg,
                                      content: msg.content + event.data,
                                  }
                                : msg,
                        );
                    }
                }
            }
        } catch (err) {
            error = err instanceof Error ? err.message : $t("chatErrorMessage");
            console.error("Chat error:", err);
        } finally {
            isLoading = false;
        }
    }

    function handleKeydown(event: KeyboardEvent) {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    }

    function clearChat() {
        messages = [];
        error = null;
    }
</script>

<div class={`chat-window ${floating ? "floating" : ""}`}>
    <header class="chat-header">
        <div class="chat-title">
            <span aria-hidden="true">💬</span>
            <div>
                <p class="label">{$t("chat.title")}</p>
                <p class="muted">{$t("chat.subtitle")}</p>
            </div>
        </div>
        {#if onClose}
            <button
                class="icon-button"
                onclick={onClose}
                aria-label={$t("chat.close")}
            >
                ✕
            </button>
        {/if}
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
            {#if isLoading}
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
                    <div class="bubble error-bubble">{error}</div>
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
            disabled={isLoading}
        ></textarea>
        <button
            class="primary"
            onclick={sendMessage}
            disabled={!inputMessage.trim() || isLoading}
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

    .label {
        margin: 0;
        font-weight: 700;
    }

    .muted {
        margin: 0;
        color: var(--color-text-secondary);
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

    .icon-button {
        border: 1px solid var(--color-border);
        background: var(--color-panel);
        border-radius: 10px;
        padding: 0.5rem;
        cursor: pointer;
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
    }

    .primary:disabled {
        opacity: 0.6;
        cursor: not-allowed;
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
    }
</style>
