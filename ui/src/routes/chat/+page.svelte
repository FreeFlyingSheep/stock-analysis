<script lang="ts">
    import { onMount } from "svelte";
    import ChatWindow from "$lib/components/ChatWindow.svelte";
    import ChatHistory from "$lib/components/ChatHistory.svelte";
    import { chatHistory } from "$lib/chatHistory";
    import type { ChatThread, ChatMessage } from "$lib/types";

    let activeThreadId = $state<string | undefined>(undefined);
    let activeThreadTitle = $state<string>("");
    let activeMessages = $state<ChatMessage[]>([]);
    let initialized = $state(false);

    onMount(async () => {
        await chatHistory.init();
        const threads = chatHistory.getThreads();
        if (threads.length > 0) {
            const latest = threads[0];
            const messages = await chatHistory.loadThreadMessages(latest.id);
            activeMessages = messages;
            activeThreadTitle = latest.title;
            activeThreadId = latest.id;
        }
        initialized = true;
    });

    async function handleSelectThread(thread: ChatThread) {
        const messages = await chatHistory.loadThreadMessages(thread.id);
        activeMessages = messages;
        activeThreadTitle = thread.title;
        activeThreadId = thread.id;
    }

    function handleMessagesChange(messages: ChatMessage[]) {
        activeMessages = messages;
        if (activeThreadId) {
            chatHistory.updateMessages(activeThreadId, messages);
        }
    }

    async function ensureThread(): Promise<string> {
        if (activeThreadId) return activeThreadId;
        const id = await chatHistory.createThread();
        chatHistory.addThread(id);
        activeThreadId = id;
        activeThreadTitle = "";
        activeMessages = [];
        return id;
    }

    function handleNewChatClick() {
        activeThreadId = undefined;
        activeThreadTitle = "";
        activeMessages = [];
    }

    function handleThreadTitleChange(title: string) {
        activeThreadTitle = title;
        if (activeThreadId) {
            chatHistory.updateTitle(activeThreadId, title);
        }
    }
</script>

<div class="chat-page">
    <aside class="history-sidebar">
        <ChatHistory {activeThreadId} onSelectThread={handleSelectThread} />
    </aside>
    <main class="chat-main">
        {#if !initialized}
            <div class="loading-state">Loading...</div>
        {:else}
            {#key activeThreadId}
                <ChatWindow
                    threadId={activeThreadId}
                    threadTitle={activeThreadTitle}
                    initialMessages={activeMessages}
                    onMessagesChange={handleMessagesChange}
                    onThreadTitleChange={handleThreadTitleChange}
                    onEnsureThread={ensureThread}
                    onNewChat={handleNewChatClick}
                />
            {/key}
        {/if}
    </main>
</div>

<style>
    .chat-page {
        display: flex;
        width: 1100px;
        height: 720px;
        max-width: 100%;
        min-height: 0;
        gap: 0;
        margin: 0 auto;
    }

    .history-sidebar {
        width: 280px;
        flex-shrink: 0;
        height: 100%;
        border-right: 1px solid var(--color-border);
        background: var(--color-surface);
    }

    .chat-main {
        flex: 1;
        display: flex;
        min-width: 0;
        height: 100%;
        min-height: 0;
    }

    .chat-main > :global(*) {
        flex: 1;
        width: 100%;
        height: 100%;
        min-height: 0;
    }

    .loading-state {
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--color-text-secondary);
    }

    @media (max-width: 768px) {
        .chat-page {
            flex-direction: column;
            width: 100%;
            height: auto;
        }

        .history-sidebar {
            width: 100%;
            height: 200px;
            border-right: none;
            border-bottom: 1px solid var(--color-border);
        }

        .chat-main {
            padding: 1rem;
        }
    }
</style>
