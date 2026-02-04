<script lang="ts">
    import ChatWindow from "$lib/components/ChatWindow.svelte";
    import { t } from "$lib/i18n";
    import { chatHistory } from "$lib/chatHistory";
    import type { ChatMessage } from "$lib/types";

    let { stockCode = undefined } = $props<{ stockCode?: string }>();
    let isOpen = $state(false);
    let threadId = $state<string | undefined>(undefined);
    let threadAdded = $state(false);
    let messages = $state<ChatMessage[]>([]);
    let chatKey = $state(0);

    async function handleOpen() {
        isOpen = true;
    }

    async function ensureThread(): Promise<string> {
        if (threadId) return threadId;
        const id = await chatHistory.createThread(stockCode);
        threadId = id;
        return id;
    }

    function handleNewChat() {
        threadId = undefined;
        threadAdded = false;
        messages = [];
        chatKey += 1;
    }

    function handleMessagesChange(newMessages: ChatMessage[]) {
        messages = newMessages;
        if (threadId) {
            if (newMessages.length > 0 && !threadAdded) {
                chatHistory.addThread(threadId, stockCode);
                threadAdded = true;
            }
            chatHistory.updateMessages(threadId, newMessages);
        }
    }
</script>

<div class="floating-chat-shell">
    {#if isOpen}
        <div
            class="chat-overlay"
            role="button"
            tabindex="0"
            onclick={() => (isOpen = false)}
            onkeydown={(e) => e.key === "Enter" && (isOpen = false)}
        ></div>
    {/if}
    <div
        class={`chat-float ${isOpen ? "open" : "closed"}`}
        role="dialog"
        aria-label={$t("chat.title")}
        aria-hidden={!isOpen}
    >
        {#key chatKey}
            <ChatWindow
                floating
                {stockCode}
                {threadId}
                initialMessages={messages}
                onMessagesChange={handleMessagesChange}
                onEnsureThread={ensureThread}
                onNewChat={handleNewChat}
                onClose={() => (isOpen = false)}
            />
        {/key}
    </div>

    <button class="chat-trigger" onclick={handleOpen}>
        {isOpen ? $t("chat.close") : $t("chat.open")}
    </button>
</div>

<style>
    .floating-chat-shell {
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 999;
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 12px;
    }

    .chat-trigger {
        background: var(--color-primary);
        color: #fff;
        border: none;
        padding: 0.75rem 1rem;
        border-radius: 999px;
        box-shadow: var(--shadow-lg);
        cursor: pointer;
    }

    .chat-overlay {
        position: fixed;
        inset: 0;
        background: rgba(15, 23, 42, 0.3);
        backdrop-filter: blur(2px);
    }

    .chat-float {
        position: fixed;
        bottom: 72px;
        right: 24px;
    }

    .chat-float.closed {
        opacity: 0;
        pointer-events: none;
        transform: translateY(8px) scale(0.98);
        transition:
            opacity 0.15s ease,
            transform 0.15s ease;
    }

    .chat-float.open {
        opacity: 1;
        pointer-events: auto;
        transform: translateY(0) scale(1);
        transition:
            opacity 0.15s ease,
            transform 0.15s ease;
    }
</style>
