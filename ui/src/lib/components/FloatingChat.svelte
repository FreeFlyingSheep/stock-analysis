<script lang="ts">
  import ChatWindow from "$lib/components/ChatWindow.svelte";
  import { t } from "$lib/i18n";

  let isOpen = $state(false);
</script>

<div class="floating-chat-shell">
  {#if isOpen}
    <div class="chat-overlay" role="button" tabindex="0" onclick={() => (isOpen = false)} onkeydown={(e) => e.key === "Enter" && (isOpen = false)}></div>
    <div class="chat-float" role="dialog" aria-label={$t("chat.title")}>
      <ChatWindow floating onClose={() => (isOpen = false)} />
    </div>
  {/if}

  <button class="chat-trigger" onclick={() => (isOpen = !isOpen)}>
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
</style>
