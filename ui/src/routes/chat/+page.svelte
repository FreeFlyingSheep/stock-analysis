<script lang="ts">
    import ChatWindow from "$lib/components/ChatWindow.svelte";
    import { t } from "$lib/i18n";
</script>

<section>
    <h1>💬 {$t("chat.title")}</h1>
    <p class="muted">{$t("chat.subtitle")}</p>
    <div class="card">
        <ChatWindow />
    </div>
</section>
