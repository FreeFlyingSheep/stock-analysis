<script lang="ts">
  import favicon from "$lib/assets/favicon.ico";
  import "../app.css";

  let { children } = $props();
</script>

<svelte:head>
  <link rel="icon" href={favicon} />
  <title>Stock Analysis</title>
</svelte:head>

<div class="app">
  <header>
    <nav>
      <a href="/" class="logo">📈 Stock Analysis</a>
      <ul>
        <li><a href="/stocks">Stocks</a></li>
        <li><a href="/chat">Chat</a></li>
      </ul>
    </nav>
  </header>

  <main>
    {@render children()}
  </main>

  <footer>
    <p>Stock Analysis Tool - For reference and educational purposes only.</p>
  </footer>
</div>

<style>
  .app {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
  }

  header {
    background: var(--color-primary);
    color: white;
    padding: 0 1rem;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: var(--shadow);
  }

  nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    max-width: 1400px;
    margin: 0 auto;
    padding: 0.75rem 0;
  }

  .logo {
    font-size: 1.25rem;
    font-weight: bold;
    color: white;
    text-decoration: none;
  }

  nav ul {
    display: flex;
    gap: 2rem;
    list-style: none;
    margin: 0;
    padding: 0;
  }

  nav ul a {
    color: rgba(255, 255, 255, 0.85);
    text-decoration: none;
    font-weight: 500;
    padding: 0.5rem 0;
    transition: color 0.2s;
  }

  nav ul a:hover {
    color: white;
  }

  main {
    flex: 1;
    max-width: 1400px;
    margin: 0 auto;
    padding: 1.5rem 1rem;
    width: 100%;
  }

  footer {
    background: var(--color-bg-secondary);
    padding: 1rem;
    text-align: center;
    font-size: 0.875rem;
    color: var(--color-text-secondary);
    border-top: 1px solid var(--color-border);
  }
</style>
