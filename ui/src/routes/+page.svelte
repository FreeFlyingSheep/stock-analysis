<div class="hero">
  <h1>Stock Analysis Tool</h1>
  <p class="subtitle">
    Analyze Chinese A-share stocks with fundamental scoring and data insights
  </p>

  <div class="features">
    <a href="/stocks" class="feature-card">
      <span class="icon">📊</span>
      <h3>Stocks</h3>
      <p>Browse, search, and filter stocks. View detailed analysis, metrics, and financial data.</p>
    </a>

    <a href="/chat" class="feature-card">
      <span class="icon">💬</span>
      <h3>Chat</h3>
      <p>Ask questions about stocks and get AI-powered insights and analysis.</p>
    </a>
  </div>

  <div class="disclaimer">
    <p>
      <strong>Disclaimer:</strong> This tool is for reference and educational purposes
      only. It does not provide financial advice. Investment involves risk.
    </p>
  </div>
</div>

<style>
  .hero {
    text-align: center;
    padding: 3rem 0;
  }

  .hero h1 {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
  }

  .subtitle {
    font-size: 1.125rem;
    color: var(--color-text-secondary);
    margin-bottom: 3rem;
  }

  .features {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.5rem;
    margin-bottom: 3rem;
    max-width: 700px;
    margin-left: auto;
    margin-right: auto;
  }

  .feature-card {
    display: block;
    padding: 2rem;
    background: var(--color-bg);
    border: 1px solid var(--color-border);
    border-radius: var(--radius);
    text-decoration: none;
    color: inherit;
    transition: all 0.2s;
  }

  .feature-card:hover {
    border-color: var(--color-primary);
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
    text-decoration: none;
  }

  .icon {
    font-size: 2.5rem;
    display: block;
    margin-bottom: 1rem;
  }

  .feature-card h3 {
    margin-bottom: 0.5rem;
    color: var(--color-text);
  }

  .feature-card p {
    margin: 0;
    color: var(--color-text-secondary);
    font-size: 0.875rem;
  }

  .disclaimer {
    padding: 1rem;
    background: var(--color-bg-secondary);
    border-radius: var(--radius);
    font-size: 0.875rem;
    color: var(--color-text-secondary);
    max-width: 700px;
    margin: 0 auto;
  }

  .disclaimer p {
    margin: 0;
  }
</style>
