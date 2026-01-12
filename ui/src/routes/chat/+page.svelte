<script lang="ts">
  let messages = $state<Array<{ role: "user" | "assistant"; content: string }>>([]);
  let inputMessage = $state("");
  let isLoading = $state(false);

  async function sendMessage() {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = inputMessage.trim();
    inputMessage = "";
    messages = [...messages, { role: "user", content: userMessage }];
    isLoading = true;

    // Placeholder for future LLM integration
    await new Promise((resolve) => setTimeout(resolve, 1000));
    messages = [
      ...messages,
      {
        role: "assistant",
        content:
          "🚧 Chat functionality is coming soon! This feature will allow you to ask questions about stocks and get AI-powered insights.",
      },
    ];
    isLoading = false;
  }

  function handleKeydown(event: KeyboardEvent) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }

  function clearChat() {
    messages = [];
  }
</script>

<div class="chat-page">
  <div class="page-header">
    <h1>💬 Chat</h1>
    <p class="subtitle">Ask questions about stocks and get AI-powered insights</p>
  </div>

  <div class="chat-container">
    <div class="messages">
      {#if messages.length === 0}
        <div class="welcome">
          <div class="welcome-icon">🤖</div>
          <h2>Welcome to Stock Chat</h2>
          <p>Ask me anything about Chinese A-share stocks, market analysis, or financial data.</p>
          <div class="suggestions">
            <p class="suggestions-label">Try asking:</p>
            <button class="suggestion" onclick={() => { inputMessage = "What are the top performing stocks today?"; sendMessage(); }}>
              What are the top performing stocks today?
            </button>
            <button class="suggestion" onclick={() => { inputMessage = "Analyze stock 600519"; sendMessage(); }}>
              Analyze stock 600519
            </button>
            <button class="suggestion" onclick={() => { inputMessage = "Which industries are trending?"; sendMessage(); }}>
              Which industries are trending?
            </button>
          </div>
        </div>
      {:else}
        {#each messages as message}
          <div class="message {message.role}">
            <div class="message-avatar">
              {message.role === "user" ? "👤" : "🤖"}
            </div>
            <div class="message-content">
              {message.content}
            </div>
          </div>
        {/each}
        {#if isLoading}
          <div class="message assistant">
            <div class="message-avatar">🤖</div>
            <div class="message-content loading">
              <span class="dot"></span>
              <span class="dot"></span>
              <span class="dot"></span>
            </div>
          </div>
        {/if}
      {/if}
    </div>

    <div class="input-area">
      {#if messages.length > 0}
        <button class="clear-btn" onclick={clearChat} title="Clear chat">
          🗑️
        </button>
      {/if}
      <textarea
        bind:value={inputMessage}
        onkeydown={handleKeydown}
        placeholder="Type your message..."
        rows="1"
        disabled={isLoading}
      ></textarea>
      <button
        class="send-btn"
        onclick={sendMessage}
        disabled={!inputMessage.trim() || isLoading}
      >
        Send
      </button>
    </div>
  </div>

  <div class="notice">
    <p>⚠️ <strong>Coming Soon:</strong> This chat feature is under development. Full LLM integration will be available in a future update.</p>
  </div>
</div>

<style>
  .chat-page {
    display: flex;
    flex-direction: column;
    height: calc(100vh - 140px);
    max-height: 800px;
  }

  .page-header {
    margin-bottom: 1rem;
  }

  .page-header h1 {
    margin-bottom: 0.25rem;
  }

  .subtitle {
    color: var(--color-text-secondary);
    margin: 0;
  }

  .chat-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: var(--color-bg);
    border: 1px solid var(--color-border);
    border-radius: var(--radius);
    overflow: hidden;
  }

  .messages {
    flex: 1;
    overflow-y: auto;
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .welcome {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 2rem;
  }

  .welcome-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
  }

  .welcome h2 {
    margin-bottom: 0.5rem;
  }

  .welcome > p {
    color: var(--color-text-secondary);
    max-width: 400px;
  }

  .suggestions {
    margin-top: 2rem;
  }

  .suggestions-label {
    font-size: 0.875rem;
    color: var(--color-text-secondary);
    margin-bottom: 0.75rem;
  }

  .suggestion {
    display: block;
    width: 100%;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    background: var(--color-bg-secondary);
    border: 1px solid var(--color-border);
    border-radius: var(--radius);
    text-align: left;
    cursor: pointer;
    transition: all 0.2s;
  }

  .suggestion:hover {
    background: var(--color-bg-tertiary);
    border-color: var(--color-primary);
  }

  .message {
    display: flex;
    gap: 0.75rem;
    max-width: 80%;
  }

  .message.user {
    align-self: flex-end;
    flex-direction: row-reverse;
  }

  .message-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: var(--color-bg-secondary);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .message-content {
    padding: 0.75rem 1rem;
    border-radius: var(--radius);
    line-height: 1.5;
  }

  .message.user .message-content {
    background: var(--color-primary);
    color: white;
  }

  .message.assistant .message-content {
    background: var(--color-bg-secondary);
  }

  .message-content.loading {
    display: flex;
    gap: 0.25rem;
    padding: 1rem;
  }

  .dot {
    width: 8px;
    height: 8px;
    background: var(--color-text-secondary);
    border-radius: 50%;
    animation: bounce 1.4s infinite ease-in-out both;
  }

  .dot:nth-child(1) {
    animation-delay: -0.32s;
  }

  .dot:nth-child(2) {
    animation-delay: -0.16s;
  }

  @keyframes bounce {
    0%,
    80%,
    100% {
      transform: scale(0);
    }
    40% {
      transform: scale(1);
    }
  }

  .input-area {
    display: flex;
    gap: 0.75rem;
    padding: 1rem;
    border-top: 1px solid var(--color-border);
    background: var(--color-bg-secondary);
  }

  .clear-btn {
    padding: 0.5rem;
    background: none;
    border: 1px solid var(--color-border);
    border-radius: var(--radius);
    cursor: pointer;
    opacity: 0.6;
    transition: opacity 0.2s;
  }

  .clear-btn:hover {
    opacity: 1;
  }

  .input-area textarea {
    flex: 1;
    padding: 0.75rem 1rem;
    border: 1px solid var(--color-border);
    border-radius: var(--radius);
    resize: none;
    font-family: inherit;
    font-size: 1rem;
    min-height: 44px;
    max-height: 120px;
  }

  .input-area textarea:focus {
    outline: none;
    border-color: var(--color-primary);
  }

  .send-btn {
    padding: 0.75rem 1.5rem;
    background: var(--color-primary);
    color: white;
    border: none;
    border-radius: var(--radius);
    font-weight: 500;
    cursor: pointer;
    transition: background 0.2s;
  }

  .send-btn:hover:not(:disabled) {
    background: var(--color-primary-hover);
  }

  .send-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .notice {
    margin-top: 1rem;
    padding: 0.75rem 1rem;
    background: var(--color-bg-secondary);
    border: 1px solid var(--color-border);
    border-radius: var(--radius);
    font-size: 0.875rem;
    color: var(--color-text-secondary);
  }

  .notice p {
    margin: 0;
  }
</style>
