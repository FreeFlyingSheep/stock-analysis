<script lang="ts">
    import { page } from "$app/stores";
    import { getStockDetails, getStocks, getAnalysisDetails } from "$lib/api";
    import { t } from "$lib/i18n";
    import type {
        StockDetailApiResponse,
        StockOut,
        AnalysisDetailApiResponse,
        AnalysisOut,
    } from "$lib/types";

    const stockCode = $derived($page.params.code);

    let loading = $state(true);
    let error = $state<string | null>(null);
    let stockDetails = $state<StockDetailApiResponse | null>(null);
    let analysisDetails = $state<AnalysisDetailApiResponse | null>(null);
    let stockInfo = $state<StockOut | null>(null);
    let activeTab = $state<"analysis" | "cninfo" | "yahoo">("analysis");

    async function loadData() {
        if (!stockCode) return;
        loading = true;
        error = null;
        try {
            const [stockRes, analysisRes, stocksRes] = await Promise.all([
                getStockDetails(stockCode),
                getAnalysisDetails(stockCode),
                getStocks({ size: 200 }),
            ]);
            stockDetails = stockRes;
            analysisDetails = analysisRes;
            stockInfo =
                stocksRes.data.stockPage.data.find(
                    (s) => s.stockCode === stockCode
                ) || null;
        } catch (e) {
            error =
                e instanceof Error ? e.message : "Failed to load stock details";
        } finally {
            loading = false;
        }
    }

    $effect(() => {
        if (stockCode) {
            loadData();
        }
    });

    function formatDate(dateString: string): string {
        return new Date(dateString).toLocaleDateString("en-US", {
            year: "numeric",
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        });
    }

    function formatEndpoint(endpoint: string): string {
        return endpoint
            .split("_")
            .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
            .join(" ");
    }

    function formatJson(data: unknown): string {
        return JSON.stringify(data, null, 2);
    }

    function formatMetricName(name: string): string {
        return name
            .split("_")
            .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
            .join(" ");
    }

    function formatMetricValue(value: number): string {
        if (Math.abs(value) >= 1000000) {
            return (value / 1000000).toFixed(2) + "M";
        }
        if (Math.abs(value) >= 1000) {
            return (value / 1000).toFixed(2) + "K";
        }
        return value.toFixed(2);
    }

    function getScoreClass(score: number): string {
        if (score >= 70) return "score-high";
        if (score >= 40) return "score-medium";
        return "score-low";
    }

    function getLatestAnalysis(): AnalysisOut | null {
        if (!analysisDetails || analysisDetails.data.length === 0) return null;
        return analysisDetails.data.reduce((latest, current) =>
            new Date(current.updatedAt) > new Date(latest.updatedAt)
                ? current
                : latest
        );
    }

    const latestAnalysis = $derived(getLatestAnalysis());
</script>

<a href="/stocks" class="back-link">← {$t("stock.back")}</a>

{#if loading}
    <div class="loading">{$t("loading")}</div>
{:else if error}
    <div class="error">{error}</div>
{:else}
    <div class="detail-header">
        <div class="header-main">
            <h1>{stockCode}</h1>
            {#if stockInfo}
                <p class="company-name">{stockInfo.companyName}</p>
                <div class="badges">
                    <span class="badge">{stockInfo.classification}</span>
                    <span class="badge">{stockInfo.industry}</span>
                </div>
            {/if}
        </div>
        {#if latestAnalysis}
            <div class="score-display {getScoreClass(latestAnalysis.score)}">
                <span class="score-label">{$t("stock.score")}</span>
                <span class="score-value"
                    >{latestAnalysis.score.toFixed(1)}</span
                >
            </div>
        {/if}
    </div>

    <div class="tabs">
        <button
            class="tab"
            class:active={activeTab === "analysis"}
            onclick={() => (activeTab = "analysis")}
        >
            📊 {$t("stock.tabs.analysis")}
        </button>
        <button
            class="tab"
            class:active={activeTab === "cninfo"}
            onclick={() => (activeTab = "cninfo")}
        >
            📋 {$t("stock.tabs.cninfo")} ({stockDetails?.cninfoData.length ||
                0})
        </button>
        <button
            class="tab"
            class:active={activeTab === "yahoo"}
            onclick={() => (activeTab = "yahoo")}
        >
            📈 {$t("stock.tabs.yahoo")} ({stockDetails?.yahooData.length || 0})
        </button>
    </div>

    <div class="tab-content">
        {#if activeTab === "analysis"}
            {#if !analysisDetails || analysisDetails.data.length === 0}
                <div class="empty">
                    <p>{$t("stock.noAnalysis")}</p>
                    <p class="hint">{$t("stock.analysisHint")}</p>
                </div>
            {:else if latestAnalysis}
                <div class="analysis-content">
                    <div class="metrics-section">
                        <h3>{$t("stock.metrics")}</h3>
                        <div class="metrics-grid">
                            {#each Object.entries(latestAnalysis.metrics) as [name, value]}
                                <div class="metric-card">
                                    <span class="metric-name"
                                        >{formatMetricName(name)}</span
                                    >
                                    <span class="metric-value"
                                        >{formatMetricValue(value)}</span
                                    >
                                </div>
                            {/each}
                        </div>
                    </div>

                    {#if analysisDetails.data.length > 1}
                        <div class="history-section">
                            <h3>{$t("stock.history")}</h3>
                            <table>
                                <thead>
                                    <tr>
                                        <th>{$t("stock.date")}</th>
                                        <th>{$t("stock.score")}</th>
                                        <th>{$t("stock.metricsCount")}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {#each analysisDetails.data.sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()) as analysis}
                                        <tr>
                                            <td
                                                >{formatDate(
                                                    analysis.updatedAt
                                                )}</td
                                            >
                                            <td>
                                                <span
                                                    class="badge {analysis.score >=
                                                    70
                                                        ? 'badge-success'
                                                        : analysis.score >= 40
                                                          ? 'badge-warning'
                                                          : 'badge-danger'}"
                                                >
                                                    {analysis.score.toFixed(2)}
                                                </span>
                                            </td>
                                            <td
                                                >{Object.keys(analysis.metrics)
                                                    .length}</td
                                            >
                                        </tr>
                                    {/each}
                                </tbody>
                            </table>
                        </div>
                    {/if}

                    <p class="update-info">
                        {$t("stock.lastUpdated")}: {formatDate(
                            latestAnalysis.updatedAt
                        )}
                    </p>
                </div>
            {/if}
        {:else if activeTab === "cninfo"}
            {#if !stockDetails || stockDetails.cninfoData.length === 0}
                <div class="empty">
                    <p>{$t("stock.noDataCninfo")}</p>
                    <p class="hint">{$t("stock.dataHint")}</p>
                </div>
            {:else}
                <div class="data-list">
                    {#each stockDetails.cninfoData as item}
                        <details class="card data-item">
                            <summary>
                                <span class="endpoint"
                                    >{formatEndpoint(item.endpoint)}</span
                                >
                                <span
                                    class="badge"
                                    class:badge-success={item.responseCode ===
                                        200}
                                    class:badge-danger={item.responseCode !==
                                        200}
                                >
                                    {item.responseCode}
                                </span>
                                <span class="updated"
                                    >{formatDate(item.updatedAt)}</span
                                >
                            </summary>
                            <div class="data-content">
                                <h4>{$t("stock.requestParams")}</h4>
                                <pre><code>{formatJson(item.params)}</code
                                    ></pre>
                                <h4>{$t("stock.responseData")}</h4>
                                <pre><code>{formatJson(item.rawJson)}</code
                                    ></pre>
                            </div>
                        </details>
                    {/each}
                </div>
            {/if}
        {:else if activeTab === "yahoo"}
            {#if !stockDetails || stockDetails.yahooData.length === 0}
                <div class="empty">
                    <p>{$t("stock.noDataYahoo")}</p>
                    <p class="hint">{$t("stock.dataHint")}</p>
                </div>
            {:else}
                <div class="data-list">
                    {#each stockDetails.yahooData as item}
                        <details class="card data-item">
                            <summary>
                                <span class="endpoint"
                                    >Historical Price Data</span
                                >
                                <span class="updated"
                                    >{formatDate(item.updatedAt)}</span
                                >
                            </summary>
                            <div class="data-content">
                                <h4>{$t("stock.requestParams")}</h4>
                                <pre><code>{formatJson(item.params)}</code
                                    ></pre>
                                <h4>{$t("stock.responseData")}</h4>
                                <pre><code>{item.rawJson}</code></pre>
                            </div>
                        </details>
                    {/each}
                </div>
            {/if}
        {/if}
    </div>
{/if}

<style>
    .detail-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 2rem;
        margin-bottom: 1.5rem;
        padding-bottom: 1.5rem;
        border-bottom: 1px solid var(--color-border);
    }

    .header-main h1 {
        margin-bottom: 0.25rem;
        font-size: 2rem;
    }

    .company-name {
        font-size: 1.125rem;
        color: var(--color-text-secondary);
        margin: 0 0 0.75rem;
    }

    .badges {
        display: flex;
        gap: 0.5rem;
    }

    .score-display {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 1rem 1.5rem;
        border-radius: var(--radius);
        min-width: 100px;
    }

    .score-display.score-high {
        background: #dcfce7;
        color: #166534;
    }

    .score-display.score-medium {
        background: #fef3c7;
        color: #92400e;
    }

    .score-display.score-low {
        background: #fee2e2;
        color: #991b1b;
    }

    .score-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        opacity: 0.8;
    }

    .score-value {
        font-size: 2.5rem;
        font-weight: 700;
        line-height: 1;
    }

    .tabs {
        display: flex;
        gap: 0;
        border-bottom: 2px solid var(--color-border);
        margin-bottom: 1.5rem;
    }

    .tab {
        padding: 0.75rem 1.25rem;
        background: none;
        border: none;
        border-bottom: 2px solid transparent;
        margin-bottom: -2px;
        color: var(--color-text-secondary);
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
    }

    .tab:hover {
        color: var(--color-text);
        background: var(--color-bg-secondary);
    }

    .tab.active {
        color: var(--color-primary);
        border-bottom-color: var(--color-primary);
    }

    .tab-content {
        min-height: 300px;
    }

    .hint {
        font-size: 0.875rem;
        color: var(--color-text-secondary);
    }

    .analysis-content h3 {
        font-size: 1rem;
        margin-bottom: 1rem;
        color: var(--color-text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .metrics-section {
        margin-bottom: 2rem;
    }

    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
        gap: 0.75rem;
    }

    .metric-card {
        background: var(--color-bg-secondary);
        border: 1px solid var(--color-border);
        border-radius: var(--radius);
        padding: 0.875rem 1rem;
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }

    .metric-name {
        font-size: 0.75rem;
        color: var(--color-text-secondary);
    }

    .metric-value {
        font-size: 1.25rem;
        font-weight: 600;
    }

    .history-section {
        margin-bottom: 1.5rem;
    }

    .update-info {
        font-size: 0.875rem;
        color: var(--color-text-secondary);
        margin-top: 1rem;
    }

    .data-list {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }

    .data-item summary {
        display: flex;
        align-items: center;
        gap: 1rem;
        cursor: pointer;
        list-style: none;
    }

    .data-item summary::-webkit-details-marker {
        display: none;
    }

    .data-item summary::before {
        content: "▶";
        font-size: 0.75rem;
        transition: transform 0.2s;
    }

    .data-item[open] summary::before {
        transform: rotate(90deg);
    }

    .endpoint {
        font-weight: 600;
        flex: 1;
    }

    .updated {
        font-size: 0.875rem;
        color: var(--color-text-secondary);
    }

    .data-content {
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid var(--color-border);
    }

    .data-content h4 {
        font-size: 0.875rem;
        color: var(--color-text-secondary);
        margin-bottom: 0.5rem;
    }

    .data-content pre {
        max-height: 400px;
        overflow: auto;
    }
</style>
