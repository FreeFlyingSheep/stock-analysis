import { derived, writable } from "svelte/store";

export type Locale = "en" | "zh";

interface TranslationMap {
  [key: string]: string | TranslationMap;
}

const messages: Record<Locale, TranslationMap> = {
  en: {
    nav: {
      home: "Home",
      stocks: "Stocks",
      data: "Data Explorer",
      chat: "Chat",
    },
    hero: {
      name: "Stock Analysis",
      title: "A-share Fundamental Analysis Agent",
      subtitle: "Data ingestion, scoring rules, and a friendly UI to explore everything.",
      ctaStocks: "Browse Stocks",
      ctaData: "View Data",
    },
    intro: {
      overview: "Project Overview",
      description:
        "Stock Analysis fetches CNInfo and Yahoo Finance data, applies declarative scoring rules, and surfaces results through an API and UI.",
      highlights: "Highlights",
      fastApi: "FastAPI backend with async pipelines",
      rules: "YAML-based scoring rules and filters",
      data: "Multiple data sources with retries and rate limits",
      ui: "SvelteKit UI with charts and tables",
    },
    how: {
      title: "How It Works",
      step1: "Ingest data from CNInfo / Yahoo per configs/api",
      step2: "Normalize and store to PostgreSQL",
      step3: "Score with declarative rules under configs/rules",
      step4: "Serve via REST and visualize in this UI",
    },
    ctas: {
      more: "Get Started",
      repo: "Repository",
    },
    disclaimer: "For reference and educational purposes only; not investment advice.",
    chat: {
      title: "Chat",
      subtitle: "Ask questions about stocks and get AI-powered insights.",
      placeholder: "Type your message...",
      send: "Send",
      clear: "Clear",
      emptyTitle: "Welcome to Stock Chat",
      emptyLead: "Ask anything about Chinese A-share stocks, market analysis, or financial data.",
      suggestion1: "What are the top performing stocks today?",
      suggestion2: "Analyze stock 600519",
      suggestion3: "Which industries are trending?",
      comingSoon: "Chat integration is under development.",
      open: "Open chat",
      close: "Close chat",
    },
    stocks: {
      title: "Stocks",
      subtitle: "Browse and search Chinese A-share stocks.",
      searchPlaceholder: "Search by code or company name...",
      filterClassification: "All Classifications",
      filterIndustry: "All Industries",
      clearFilters: "Clear Filters",
      noResults: "No stocks found matching your criteria.",
      showing: "Showing",
      matching: "matching",
      code: "Stock Code",
      name: "Company Name",
      classification: "Classification",
      industry: "Industry",
      updated: "Updated",
      actions: "Actions",
      view: "View Details",
      prev: "Previous",
      next: "Next",
      page: "Page",
      of: "of",
    },
    stock: {
      back: "Back to Stocks",
      tabs: {
        analysis: "Analysis",
        cninfo: "CNInfo",
        yahoo: "Yahoo Finance",
      },
      noAnalysis: "No analysis results available yet for this stock.",
      analysisHint: "Analysis will be computed automatically. Please refresh soon.",
      metrics: "Metrics",
      history: "History",
      date: "Date",
      score: "Score",
      metricsCount: "Metrics",
      lastUpdated: "Last updated",
      noDataCninfo: "No CNInfo data available yet.",
      noDataYahoo: "No Yahoo Finance data available yet.",
      dataHint: "Data will be fetched automatically. Please refresh soon.",
      requestParams: "Request Parameters",
      responseData: "Response Data",
    },
    loading: "loading...",
    footer: "Stock Analysis Tool - For reference and educational purposes only.",
  },
  zh: {
    nav: {
      home: "主页",
      stocks: "股票",
      data: "数据浏览",
      chat: "聊天",
    },
    hero: {
      name: "股票分析",
      title: "A股基础面评分代理",
      subtitle: "抓取数据、应用规则、可视化结果，一站式探索。",
      ctaStocks: "查看股票",
      ctaData: "浏览数据",
    },
    intro: {
      overview: "项目介绍",
      description:
        "Stock Analysis 从巨潮和雅虎财经抓取数据，使用声明式规则评分，并通过 API 与 UI 展示结果。",
      highlights: "亮点",
      fastApi: "FastAPI 异步后端",
      rules: "YAML 规则驱动的评分和筛选",
      data: "多数据源抓取，带重试与限流",
      ui: "SvelteKit 前端，图表与表格展示",
    },
    how: {
      title: "工作流程",
      step1: "按 configs/api 配置抓取 CNInfo / Yahoo 数据",
      step2: "规范化并存储到 PostgreSQL",
      step3: "使用 configs/rules 中的声明式规则评分",
      step4: "通过 REST 提供并在 UI 中可视化",
    },
    ctas: {
      more: "快速开始",
      repo: "仓库",
    },
    disclaimer: "仅供参考与学习，不构成投资建议。",
    chat: {
      title: "聊天",
      subtitle: "就股票提问，获取 AI 洞察。",
      placeholder: "请输入消息...",
      send: "发送",
      clear: "清空",
      emptyTitle: "欢迎使用股票聊天助手",
      emptyLead: "可以询问 A 股、市场分析或财务数据。",
      suggestion1: "今天表现最好的股票有哪些？",
      suggestion2: "分析股票 600519",
      suggestion3: "当前哪些行业在走强？",
      comingSoon: "聊天集成开发中。",
      open: "打开聊天",
      close: "关闭聊天",
    },
    stocks: {
      title: "股票列表",
      subtitle: "浏览和搜索 A 股公司。",
      searchPlaceholder: "按代码或公司名搜索...",
      filterClassification: "全部板块",
      filterIndustry: "全部行业",
      clearFilters: "清除筛选",
      noResults: "没有匹配的结果。",
      showing: "显示",
      matching: "条结果，匹配",
      code: "代码",
      name: "公司",
      classification: "板块",
      industry: "行业",
      updated: "更新",
      actions: "操作",
      view: "详情",
      prev: "上一页",
      next: "下一页",
      page: "页",
      of: "共",
    },
    stock: {
      back: "返回股票列表",
      tabs: {
        analysis: "分析",
        cninfo: "巨潮",
        yahoo: "雅虎财经",
      },
      noAnalysis: "暂未有该股票的分析结果。",
      analysisHint: "分析将自动计算，请稍后刷新。",
      metrics: "指标",
      history: "历史",
      date: "日期",
      score: "得分",
      metricsCount: "指标项",
      lastUpdated: "最近更新",
      noDataCninfo: "暂无巨潮数据。",
      noDataYahoo: "暂无雅虎数据。",
      dataHint: "数据将自动抓取，请稍后刷新。",
      requestParams: "请求参数",
      responseData: "响应数据",
    },
    loading: "加载中……",
    footer: "Stock Analysis 工具 - 仅供参考与学习。",
  },
};

function getFromDictionary(dict: TranslationMap, path: string[]): string | TranslationMap | undefined {
  return path.reduce<TranslationMap | string | undefined>((acc, key) => {
    if (typeof acc !== "object" || acc === null) return undefined;
    return acc[key];
  }, dict);
}

export const locale = writable<Locale>("zh");

export const t = derived(locale, ($locale) => {
  return (key: string): string => {
    const path = key.split(".");
    const value = getFromDictionary(messages[$locale] ?? messages.en, path);
    if (typeof value === "string") return value;
    const fallback = getFromDictionary(messages.en, path);
    return typeof fallback === "string" ? fallback : key;
  };
});

export const locales: { code: Locale; label: string }[] = [
  { code: "en", label: "EN" },
  { code: "zh", label: "中文" },
];

export function setLocale(next: Locale) {
  locale.set(next);
}

export function toggleLocale() {
  locale.update((current) => (current === "en" ? "zh" : "en"));
}
