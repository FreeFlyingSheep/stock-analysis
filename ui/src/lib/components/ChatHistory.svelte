<script lang="ts">
    import { t } from "$lib/i18n";
    import { chatHistory } from "$lib/chatHistory";
    import type { ChatThread } from "$lib/types";

    let { activeThreadId = undefined, onSelectThread = undefined } = $props<{
        activeThreadId?: string;
        onSelectThread?: (thread: ChatThread) => void;
    }>();

    let threads = $state<ChatThread[]>([]);

    $effect(() => {
        const unsub = chatHistory.subscribe((t) => {
            threads = t;
        });
        return unsub;
    });

    function handleSelectThread(thread: ChatThread) {
        onSelectThread?.(thread);
    }

    function handleDeleteThread(e: MouseEvent, id: string) {
        e.stopPropagation();
        chatHistory.deleteThread(id);
    }

    function formatDate(dateStr: string): string {
        const date = new Date(dateStr);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffDays === 0) {
            return date.toLocaleTimeString(undefined, {
                hour: "2-digit",
                minute: "2-digit",
            });
        } else if (diffDays === 1) {
            return "Yesterday";
        } else if (diffDays < 7) {
            return date.toLocaleDateString(undefined, { weekday: "short" });
        } else {
            return date.toLocaleDateString(undefined, {
                month: "short",
                day: "numeric",
            });
        }
    }
</script>

<div class="chat-history">
    <div class="history-header">
        <span class="header-icon">💬</span>
        <span class="header-title">{$t("stock.history")}</span>
    </div>

    <div class="thread-list">
        {#if threads.length === 0}
            <div class="empty-state">
                <p class="muted">{$t("chat.noHistory")}</p>
            </div>
        {:else}
            {#each threads as thread (thread.id)}
                <div
                    class={`thread-item ${thread.id === activeThreadId ? "active" : ""}`}
                    role="button"
                    tabindex="0"
                    onclick={() => handleSelectThread(thread)}
                    onkeydown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                            handleSelectThread(thread);
                        }
                    }}
                >
                    <div class="thread-content">
                        <div class="thread-header">
                            <span class="thread-title">
                                {thread.title || $t("chat.newChat")}
                            </span>
                            <span class="thread-date">
                                {formatDate(thread.updatedAt)}
                            </span>
                        </div>
                    </div>
                    <button
                        class="delete-btn"
                        onclick={(e) => handleDeleteThread(e, thread.id)}
                        title={$t("chat.delete")}
                        aria-label={$t("chat.delete")}
                    >
                        🗑️
                    </button>
                </div>
            {/each}
        {/if}
    </div>
</div>

<style>
    .chat-history {
        display: flex;
        flex-direction: column;
        height: 100%;
        background: var(--color-panel);
        overflow: hidden;
    }

    .history-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 1rem;
        border-bottom: 1px solid var(--color-border);
    }

    .header-icon {
        font-size: 1.25rem;
    }

    .header-title {
        font-weight: 600;
        font-size: 1rem;
    }

    .thread-list {
        flex: 1;
        overflow-y: auto;
        padding: 0.5rem;
    }

    .empty-state {
        text-align: center;
        padding: 2rem 1rem;
    }

    .muted {
        color: var(--color-text-secondary);
    }

    .thread-item {
        width: 100%;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.75rem;
        border: 1px solid transparent;
        border-radius: 10px;
        background: transparent;
        cursor: pointer;
        text-align: left;
        transition:
            background 0.2s,
            border-color 0.2s;
    }

    .thread-item:hover {
        background: var(--color-surface);
        border-color: var(--color-border);
    }

    .thread-item.active {
        background: var(--color-surface-strong);
        border-color: var(--color-primary);
    }

    .thread-content {
        flex: 1;
        min-width: 0;
        pointer-events: none;
    }

    .thread-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 0.5rem;
    }

    .thread-title {
        font-weight: 600;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        flex: 1;
    }

    .thread-date {
        font-size: 0.75rem;
        color: var(--color-text-secondary);
        flex-shrink: 0;
    }

    .delete-btn {
        flex-shrink: 0;
        background: none;
        border: none;
        cursor: pointer;
        padding: 0.25rem;
        opacity: 0;
        transition: opacity 0.2s;
    }

    .thread-item:hover .delete-btn {
        opacity: 0.6;
    }

    .delete-btn:hover {
        opacity: 1 !important;
    }
</style>
