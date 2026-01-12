<script lang="ts">
  import { onMount } from "svelte";
  import { getStocks, type GetStocksParams } from "$lib/api";
  import type { StockApiResponse, StockOut } from "$lib/types";

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
      error = e instanceof Error ? e.message : "Failed to load stocks";
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
        stock.companyName.toLowerCase().includes(debouncedSearch)
    );
  });

  const hasActiveFilters = $derived(
    classification !== "" || industry !== "" || searchQuery !== ""
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
  <h1>Stocks</h1>
  <p class="subtitle">Browse and search Chinese A-share stocks</p>
</div>

{#if loading && !data}
  <div class="loading">Loading stocks...</div>
{:else if error}
  <div class="error">{error}</div>
{:else if data}
  <div class="toolbar">
    <div class="search-box">
      <input
        type="text"
        placeholder="Search by code or company name..."
        bind:value={searchQuery}
        oninput={handleSearchInput}
      />
      <span class="search-icon">🔍</span>
    </div>

    <div class="filters">
      <select
        id="classification"
        bind:value={classification}
        onchange={handleFilterChange}
      >
        <option value="">All Classifications</option>
        {#each data.data.classifications as c}
          <option value={c}>{c}</option>
        {/each}
      </select>

      <select id="industry" bind:value={industry} onchange={handleFilterChange}>
        <option value="">All Industries</option>
        {#each data.data.industries as i}
          <option value={i}>{i}</option>
        {/each}
      </select>

      {#if hasActiveFilters}
        <button class="btn btn-secondary" onclick={clearFilters}>
          Clear Filters
        </button>
      {/if}
    </div>
  </div>

  {#if filteredStocks.length === 0}
    <div class="empty">No stocks found matching your criteria.</div>
  {:else}
    <div class="results-info">
      Showing {filteredStocks.length} stocks
      {#if debouncedSearch}
        matching "{debouncedSearch}"
      {/if}
    </div>

    <table>
      <thead>
        <tr>
          <th>Stock Code</th>
          <th>Company Name</th>
          <th>Classification</th>
          <th>Industry</th>
          <th>Updated</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {#each filteredStocks as stock}
          <tr>
            <td class="code-cell">
              <strong>{stock.stockCode}</strong>
            </td>
            <td>{stock.companyName}</td>
            <td><span class="badge">{stock.classification}</span></td>
            <td><span class="badge">{stock.industry}</span></td>
            <td class="date-cell">{formatDate(stock.updatedAt)}</td>
            <td>
              <a href="/stocks/{stock.stockCode}" class="btn btn-primary btn-sm">
                View Details
              </a>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>

    {#if !debouncedSearch}
      <div class="pagination">
        <button
          class="btn btn-secondary"
          disabled={currentPage <= 1}
          onclick={() => goToPage(currentPage - 1)}
        >
          ← Previous
        </button>
        <span class="pagination-info">
          Page {data.data.stockPage.pageNum} of {data.data.stockPage.total}
        </span>
        <button
          class="btn btn-secondary"
          disabled={currentPage >= data.data.stockPage.total}
          onclick={() => goToPage(currentPage + 1)}
        >
          Next →
        </button>
      </div>
    {/if}
  {/if}
{/if}

<style>
  .page-header {
    margin-bottom: 1.5rem;
  }

  .page-header h1 {
    margin-bottom: 0.25rem;
  }

  .subtitle {
    color: var(--color-text-secondary);
    margin: 0;
  }

  .toolbar {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    margin-bottom: 1.5rem;
    align-items: center;
  }

  .search-box {
    position: relative;
    flex: 1;
    min-width: 250px;
    max-width: 400px;
  }

  .search-box input {
    width: 100%;
    padding-left: 2.5rem;
  }

  .search-icon {
    position: absolute;
    left: 0.75rem;
    top: 50%;
    transform: translateY(-50%);
    opacity: 0.5;
  }

  .filters {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
    align-items: center;
  }

  .results-info {
    font-size: 0.875rem;
    color: var(--color-text-secondary);
    margin-bottom: 1rem;
  }

  .code-cell {
    font-family: "SF Mono", "Fira Code", monospace;
  }

  .date-cell {
    color: var(--color-text-secondary);
    font-size: 0.875rem;
  }

  .btn-sm {
    padding: 0.375rem 0.75rem;
    font-size: 0.8125rem;
  }
</style>
