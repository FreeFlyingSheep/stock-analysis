<script lang="ts">
    import ChatWindow from "$lib/components/ChatWindow.svelte";
    import { t } from "$lib/i18n";
</script>

<section>
    <h1>💬 {$t("chat.title")}</h1>
    <p class="muted">{$t("chat.subtitle")}</p>
    <div class="chat-container">
        <ChatWindow />
    </div>
</section>

<style>
    .chat-container {
        width: 100%;
        min-width: 320px;
        max-width: 720px;
    }

    .muted {
        margin: 0;
        color: var(--color-text-secondary);
    }
</style>
