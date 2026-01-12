import type {
	StockApiResponse,
	StockDetailApiResponse,
	AnalysisApiResponse,
	AnalysisDetailApiResponse
} from './types';

const API_BASE_URL = '/api';

async function fetchApi<T>(endpoint: string): Promise<T> {
	const response = await fetch(`${API_BASE_URL}${endpoint}`);
	if (!response.ok) {
		throw new Error(`API error: ${response.status} ${response.statusText}`);
	}
	return response.json();
}

export interface GetStocksParams {
	page?: number;
	size?: number;
	classification?: string;
	industry?: string;
}

export async function getStocks(params: GetStocksParams = {}): Promise<StockApiResponse> {
	const searchParams = new URLSearchParams();
	if (params.page) searchParams.set('page', params.page.toString());
	if (params.size) searchParams.set('size', params.size.toString());
	if (params.classification) searchParams.set('classification', params.classification);
	if (params.industry) searchParams.set('industry', params.industry);

	const query = searchParams.toString();
	return fetchApi<StockApiResponse>(`/stocks${query ? `?${query}` : ''}`);
}

export async function getStockDetails(stockCode: string): Promise<StockDetailApiResponse> {
	return fetchApi<StockDetailApiResponse>(`/stocks/${stockCode}`);
}

export interface GetAnalysisParams {
	page?: number;
	size?: number;
}

export async function getAnalysis(params: GetAnalysisParams = {}): Promise<AnalysisApiResponse> {
	const searchParams = new URLSearchParams();
	if (params.page) searchParams.set('page', params.page.toString());
	if (params.size) searchParams.set('size', params.size.toString());

	const query = searchParams.toString();
	return fetchApi<AnalysisApiResponse>(`/analysis${query ? `?${query}` : ''}`);
}

export async function getAnalysisDetails(stockCode: string): Promise<AnalysisDetailApiResponse> {
	return fetchApi<AnalysisDetailApiResponse>(`/analysis/${stockCode}`);
}
