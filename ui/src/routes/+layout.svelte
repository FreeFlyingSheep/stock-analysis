<script lang="ts">
  import favicon from "$lib/assets/favicon.ico";
  import FloatingChat from "$lib/components/FloatingChat.svelte";
  import { locales, locale, setLocale, t } from "$lib/i18n";
  import { page } from "$app/stores";
  import "../app.css";

  let { children } = $props();

  const links = [
    { href: "/", label: () => $t("nav.home") },
    { href: "/stocks", label: () => $t("nav.stocks") },
    { href: "/chat", label: () => $t("nav.chat") },
  ];

  const currentPath = $derived($page.url.pathname);
</script>

<svelte:head>
  <link rel="icon" href={favicon} />
  <title>Stock Analysis</title>
</svelte:head>

<div class="app-shell">
  <header class="topbar">
    <div class="topbar__inner page-shell">
      <a href="/" class="brand">📈 Stock Analysis</a>
      <nav class="nav">
        {#each links as link}
          <a
            class:active={currentPath === link.href || currentPath.startsWith(`${link.href}/`)}
            href={link.href}
          >
            {link.label()}
          </a>
        {/each}
      </nav>
      <div class="lang-switch">
        {#each locales as item}
          <button
            class:item-active={$locale === item.code}
            onclick={() => setLocale(item.code)}
            aria-label={`Switch to ${item.label}`}
          >
            {item.label}
          </button>
        {/each}
      </div>
    </div>
  </header>

  <main class="page-shell">
    {@render children()}
  </main>

  <footer class="footer">
    <p>{$t("footer")}</p>
  </footer>

  <FloatingChat />
</div>

<style>
  .app-shell {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  .topbar {
    position: sticky;
    top: 0;
    z-index: 50;
    backdrop-filter: blur(6px);
    background: rgba(5, 11, 19, 0.9);
    border-bottom: 1px solid var(--color-border);
  }

  .topbar__inner {
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: center;
    gap: 1rem;
  }

  .brand {
    font-weight: 800;
    letter-spacing: 0.02em;
    color: #fff;
  }

  .nav {
    display: flex;
    gap: 1rem;
    justify-content: center;
  }

  .nav a {
    padding: 0.65rem 0.9rem;
    border-radius: 12px;
    color: var(--color-text-secondary);
    border: 1px solid transparent;
  }

  .nav a.active {
    color: #fff;
    border-color: var(--color-border);
    background: rgba(255, 255, 255, 0.03);
  }

  .lang-switch {
    display: inline-flex;
    gap: 0.4rem;
    padding: 0.25rem;
    border-radius: 999px;
    border: 1px solid var(--color-border);
    background: var(--color-panel);
  }

  .lang-switch button {
    background: transparent;
    border: none;
    color: var(--color-text-secondary);
    padding: 0.35rem 0.75rem;
    border-radius: 999px;
    cursor: pointer;
  }

  .lang-switch .item-active {
    background: var(--color-primary);
    color: #fff;
  }

  main.page-shell {
    flex: 1;
  }

  .footer {
    padding: 1rem 1.25rem 2rem;
    text-align: center;
    color: var(--color-text-secondary);
    border-top: 1px solid var(--color-border);
  }
</style>
