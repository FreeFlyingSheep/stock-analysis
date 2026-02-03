<script lang="ts">
    import { t } from "$lib/i18n";

    export interface TableData {
        title: string;
        path: string;
        rows: Record<string, unknown>[];
    }

    let { table }: { table: TableData } = $props();

    const columns = $derived.by(() => {
        const keys = new Set<string>();
        table.rows.forEach((row) => {
            Object.keys(row || {}).forEach((k) => keys.add(k));
        });
        return Array.from(keys);
    });

    function formatCell(value: unknown): string {
        if (value === null || value === undefined) return "";
        if (typeof value === "object") return JSON.stringify(value);
        return String(value);
    }
</script>

<section class="data-card">
    <header class="data-card__header">
        <div>
            <p class="overline">{$t("data.tableFrom")}</p>
            <strong>{table.path}</strong>
        </div>
        <span class="badge">{table.rows.length} {$t("data.rows")}</span>
    </header>

    {#if !table.rows.length}
        <p class="muted">{$t("data.none")}</p>
    {:else}
        <div class="table-scroll">
            <table>
                <thead>
                    <tr>
                        {#each columns as col}
                            <th>{col}</th>
                        {/each}
                    </tr>
                </thead>
                <tbody>
                    {#each table.rows as row}
                        <tr>
                            {#each columns as col}
                                <td>{formatCell(row[col])}</td>
                            {/each}
                        </tr>
                    {/each}
                </tbody>
            </table>
        </div>
    {/if}
</section>

<style>
    .data-card {
        background: var(--color-panel);
        border: 1px solid var(--color-border);
        border-radius: 16px;
        padding: 1rem;
        box-shadow: var(--shadow-sm);
    }

    .data-card__header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }

    .overline {
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-size: 0.75rem;
        color: var(--color-text-secondary);
        margin: 0 0 0.25rem;
    }

    .badge {
        padding: 0.25rem 0.5rem;
        border-radius: 10px;
        background: var(--color-surface);
        border: 1px solid var(--color-border);
        font-size: 0.85rem;
    }

    .table-scroll {
        overflow: auto;
    }

    table {
        width: 100%;
        border-collapse: collapse;
        min-width: 400px;
    }

    th,
    td {
        padding: 0.65rem 0.5rem;
        border-bottom: 1px solid var(--color-border);
        text-align: left;
    }

    th {
        font-weight: 600;
        color: var(--color-text-secondary);
        font-size: 0.9rem;
    }
</style>
