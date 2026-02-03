<script lang="ts">
    import { onMount } from "svelte";
    import { getStocks, type GetStocksParams } from "$lib/api";
    import { t } from "$lib/i18n";
    import type { StockApiResponse } from "$lib/types";

    let loading = $state(true);
    let error = $state<string | null>(null);
    let data = $state<StockApiResponse | null>(null);

    let currentPage = $state(1);
    let classification = $state("");
    let industry = $state("");
    let searchQuery = $state("");
    let debouncedSearch = $state("");
    let debounceTimer: ReturnType<typeof setTimeout> | null = null;

    async function loadStocks() {
        loading = true;
        error = null;
        try {
            const params: GetStocksParams = { page: currentPage, size: 50 };
            if (classification) params.classification = classification;
            if (industry) params.industry = industry;
            data = await getStocks(params);
        } catch (e) {
            error =
                e instanceof Error
                    ? e.message
                    : $t("errors.failedToLoadStocks");
        } finally {
            loading = false;
        }
    }

    function handleFilterChange() {
        currentPage = 1;
        loadStocks();
    }

    function handleSearchInput() {
        if (debounceTimer) clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            debouncedSearch = searchQuery.toLowerCase().trim();
        }, 300);
    }

    function goToPage(newPage: number) {
        currentPage = newPage;
        loadStocks();
    }

    function clearFilters() {
        classification = "";
        industry = "";
        searchQuery = "";
        debouncedSearch = "";
        currentPage = 1;
        loadStocks();
    }

    onMount(() => {
        loadStocks();
    });

    const filteredStocks = $derived.by(() => {
        if (!data || !debouncedSearch) return data?.data.stockPage.data || [];
        return data.data.stockPage.data.filter(
            (stock) =>
                stock.stockCode.toLowerCase().includes(debouncedSearch) ||
                stock.companyName.toLowerCase().includes(debouncedSearch),
        );
    });

    const hasActiveFilters = $derived(
        classification !== "" || industry !== "" || searchQuery !== "",
    );

    function formatDate(dateString: string): string {
        return new Date(dateString).toLocaleDateString("en-US", {
            year: "numeric",
            month: "short",
            day: "numeric",
        });
    }
</script>

<div class="page-header">
    <h1>{$t("stocks.title")}</h1>
    <p class="muted">{$t("stocks.subtitle")}</p>
</div>

{#if loading && !data}
    <div class="loading">{$t("loading")}</div>
{:else if error}
    <div class="error">{error}</div>
{:else if data}
    <div class="toolbar">
        <div
            class="search-box"
            style="position: relative; flex: 1; min-width: 260px; max-width: 420px;"
        >
            <input
                type="text"
                placeholder={$t("stocks.searchPlaceholder")}
                bind:value={searchQuery}
                oninput={handleSearchInput}
                style="width: 100%; padding-left: 2.2rem;"
            />
            <span
                class="muted"
                style="position: absolute; left: 0.75rem; top: 50%; transform: translateY(-50%);"
                >🔍</span
            >
        </div>

        <div class="filters">
            <select
                id="classification"
                bind:value={classification}
                onchange={handleFilterChange}
            >
                <option value="">{$t("stocks.filterClassification")}</option>
                {#each data.data.classifications as c}
                    <option value={c}>{c}</option>
                {/each}
            </select>

            <select
                id="industry"
                bind:value={industry}
                onchange={handleFilterChange}
            >
                <option value="">{$t("stocks.filterIndustry")}</option>
                {#each data.data.industries as i}
                    <option value={i}>{i}</option>
                {/each}
            </select>

            {#if hasActiveFilters}
                <button class="button" onclick={clearFilters}>
                    {$t("stocks.clearFilters")}
                </button>
            {/if}
        </div>
    </div>

    {#if filteredStocks.length === 0}
        <div class="empty">{$t("stocks.noResults")}</div>
    {:else}
        <div class="muted">
            {$t("stocks.showing")}
            {filteredStocks.length}
            {#if debouncedSearch}
                {$t("stocks.matching")} "{debouncedSearch}"
            {/if}
        </div>

        <table>
            <thead>
                <tr>
                    <th>{$t("stocks.code")}</th>
                    <th>{$t("stocks.name")}</th>
                    <th>{$t("stocks.classification")}</th>
                    <th>{$t("stocks.industry")}</th>
                    <th>{$t("stocks.updated")}</th>
                    <th>{$t("stocks.actions")}</th>
                </tr>
            </thead>
            <tbody>
                {#each filteredStocks as stock}
                    <tr>
                        <td class="code-cell">
                            <strong>{stock.stockCode}</strong>
                        </td>
                        <td>{stock.companyName}</td>
                        <td
                            ><span class="badge">{stock.classification}</span
                            ></td
                        >
                        <td><span class="badge">{stock.industry}</span></td>
                        <td class="date-cell">{formatDate(stock.updatedAt)}</td>
                        <td>
                            <a
                                href="/stocks/{stock.stockCode}"
                                class="button primary"
                                style="padding: 0.45rem 0.75rem; font-size: 0.9rem;"
                            >
                                {$t("stocks.view")}
                            </a>
                        </td>
                    </tr>
                {/each}
            </tbody>
        </table>

        {#if !debouncedSearch}
            <div class="pagination">
                <button
                    class="button"
                    disabled={currentPage <= 1}
                    onclick={() => goToPage(currentPage - 1)}
                >
                    ← {$t("stocks.prev")}
                </button>
                <span class="pagination-info">
                    {$t("stocks.page")}
                    {data.data.stockPage.pageNum}
                    {$t("stocks.of")}
                    {data.data.stockPage.total}
                </span>
                <button
                    class="button"
                    disabled={currentPage >= data.data.stockPage.total}
                    onclick={() => goToPage(currentPage + 1)}
                >
                    {$t("stocks.next")}
                    →
                </button>
            </div>
        {/if}
    {/if}
{/if}
