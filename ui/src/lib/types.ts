// TypeScript types matching FastAPI backend schemas

export interface StockOut {
    stockCode: string;
    companyName: string;
    classification: string;
    industry: string;
    createdAt: string;
    updatedAt: string;
}

export interface StockPage {
    total: number;
    pageNum: number;
    pageSize: number;
    data: StockOut[];
}

export interface StockListData {
    industries: string[];
    classifications: string[];
    stockPage: StockPage;
}

export interface StockApiResponse {
    data: StockListData;
}

export interface CNInfoAPIResponseOut {
    id: number;
    endpoint: string;
    stockId: number;
    params: Record<string, number | string>;
    responseCode: number;
    rawJson: Record<string, unknown>;
    createdAt: string;
    updatedAt: string;
}

export interface YahooFinanceAPIResponseOut {
    id: number;
    stockId: number;
    params: Record<string, number | string>;
    rawJson: string;
    createdAt: string;
    updatedAt: string;
}

export interface StockDetailApiResponse {
    cninfoData: CNInfoAPIResponseOut[];
    yahooData: YahooFinanceAPIResponseOut[];
}

export interface AnalysisOut {
    stockId: number;
    metrics: Record<string, number>;
    score: number;
    createdAt: string;
    updatedAt: string;
}

export interface AnalysisPage {
    total: number;
    pageNum: number;
    pageSize: number;
    data: AnalysisOut[];
}

export interface AnalysisApiResponse {
    data: AnalysisPage;
}

export interface AnalysisDetailApiResponse {
    data: AnalysisOut[];
}

export interface ChatStartIn {
    threadId: string;
    messageId: string;
    message: string;
    locale: string;
    stockCode?: string | null;
}

export interface ChatStartOut {
    streamUrl: string;
}

export interface StreamEvent {
    id: string;
    event: "token" | "done" | "error" | "ping";
    data: string;
}

export interface ChatThreadOutApi {
    threadId: string;
    title: string;
    status: "active" | "deleted";
    createdAt: string;
    updatedAt: string;
}

export interface ChatThreadsResponse {
    data: ChatThreadOutApi[];
}

export interface ChatMessageOutApi {
    role: "human" | "ai";
    content: string;
}

export interface ChatThreadDetailResponse {
    data: ChatMessageOutApi[];
}

export interface ChatThreadCreateIn {
    threadId?: string;
    title?: string;
    status?: "active" | "deleted";
}

export interface ChatThreadUpdateIn {
    title?: string;
    status?: "active" | "deleted";
}

export interface ChatMessage {
    role: "user" | "assistant";
    content: string;
}

export interface ChatThread {
    id: string;
    title: string;
    messages: ChatMessage[];
    stockCode?: string;
    createdAt: string;
    updatedAt: string;
}
