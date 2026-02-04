import { writable, get } from "svelte/store";
import type { ChatThread, ChatMessage } from "./types";
import {
    getChatThreads,
    getChatThreadDetails,
    createChatThread,
    updateChatThread,
    deleteChatThread,
} from "./api";

function createChatHistoryStore() {
    const { subscribe, set, update } = writable<ChatThread[]>([]);
    let initialized = false;
    let loading = false;

    return {
        subscribe,

        /** Initialize from backend API */
        async init(): Promise<void> {
            if (initialized || loading) return;
            loading = true;
            try {
                const response = await getChatThreads();
                const threads: ChatThread[] = response.data.map((t) => ({
                    id: t.threadId,
                    title: t.title,
                    messages: [], // Messages are loaded on demand
                    createdAt: t.createdAt,
                    updatedAt: t.updatedAt,
                }));
                set(threads);
                initialized = true;
            } catch (error) {
                console.error("Failed to load chat threads:", error);
                set([]);
            } finally {
                loading = false;
            }
        },

        /** Create a new thread locally (will be persisted on first message) */
        async createThread(stockCode?: string): Promise<string> {
            const id = `chat_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
            try {
                const created = await createChatThread({
                    threadId: id,
                    title: stockCode ?? "New Chat",
                    status: "active",
                });
                return created.threadId;
            } catch (error) {
                console.error("Failed to create chat thread:", error);
                return id;
            }
        },

        /** Add thread to store (called when first message is sent) */
        addThread(id: string, stockCode?: string) {
            const now = new Date().toISOString();
            const thread: ChatThread = {
                id,
                title: "",
                messages: [],
                stockCode,
                createdAt: now,
                updatedAt: now,
            };
            update((threads) => [thread, ...threads]);
        },

        /** Get a thread by ID */
        getThread(id: string): ChatThread | undefined {
            return get({ subscribe }).find((t) => t.id === id);
        },

        /** Get all threads */
        getThreads(): ChatThread[] {
            return get({ subscribe });
        },

        /** Load messages for a specific thread from backend */
        async loadThreadMessages(threadId: string): Promise<ChatMessage[]> {
            try {
                const response = await getChatThreadDetails(threadId);
                const messages: ChatMessage[] = response.data.map((m) => ({
                    role: m.role === "human" ? "user" : "assistant",
                    content: m.content,
                }));
                // Update the thread with loaded messages
                update((threads) =>
                    threads.map((t) =>
                        t.id === threadId
                            ? {
                                  ...t,
                                  messages,
                                  updatedAt: new Date().toISOString(),
                              }
                            : t,
                    ),
                );
                return messages;
            } catch (error) {
                console.error(
                    `Failed to load messages for thread ${threadId}:`,
                    error,
                );
                return [];
            }
        },

        /** Update thread title locally */
        async updateTitle(id: string, title: string) {
            update((threads) =>
                threads.map((t) =>
                    t.id === id
                        ? { ...t, title, updatedAt: new Date().toISOString() }
                        : t,
                ),
            );
            try {
                await updateChatThread(id, { title });
            } catch (error) {
                console.error("Failed to update chat title:", error);
            }
        },

        /** Update thread messages locally */
        updateMessages(id: string, messages: ChatMessage[]) {
            update((threads) =>
                threads.map((t) =>
                    t.id === id
                        ? {
                              ...t,
                              messages,
                              updatedAt: new Date().toISOString(),
                          }
                        : t,
                ),
            );
        },

        /** Delete a thread (local only for now) */
        async deleteThread(id: string) {
            update((threads) => threads.filter((t) => t.id !== id));
            try {
                await deleteChatThread(id);
            } catch (error) {
                console.error("Failed to delete chat thread:", error);
            }
        },

        /** Clear all threads */
        clearAll() {
            set([]);
        },
    };
}

export const chatHistory = createChatHistoryStore();
