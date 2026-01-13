<script lang="ts">
    import { t } from "$lib/i18n";

    const highlights = [
        { icon: "⚡", text: () => $t("intro.fastApi") },
        { icon: "🧮", text: () => $t("intro.rules") },
        { icon: "🛰️", text: () => $t("intro.data") },
        { icon: "📊", text: () => $t("intro.ui") },
    ];

    const steps = [
        () => $t("how.step1"),
        () => $t("how.step2"),
        () => $t("how.step3"),
        () => $t("how.step4"),
    ];
</script>

<section class="hero">
    <div>
        <p class="pill">{$t("hero.name")}</p>
        <h1>{$t("hero.title")}</h1>
        <p class="muted">{$t("hero.subtitle")}</p>
        <div class="cta-row">
            <a class="button primary" href="/stocks">{$t("hero.ctaStocks")}</a>
        </div>
    </div>
    <div class="card">
        <h3>{$t("intro.overview")}</h3>
        <p class="muted">{$t("intro.description")}</p>
        <ul class="list-inline">
            {#each highlights as item}
                <li><span>{item.icon}</span><span>{item.text()}</span></li>
            {/each}
        </ul>
    </div>
</section>

<section class="section">
    <h2>{$t("how.title")}</h2>
    <p class="lead">{$t("intro.highlights")}</p>
    <div class="card-grid">
        {#each steps as step, i}
            <div class="card">
                <p class="pill">{i + 1}</p>
                <p>{step()}</p>
            </div>
        {/each}
    </div>
</section>

<section class="section">
    <p class="muted">{$t("disclaimer")}</p>
</section>
