/**
 * ============================================================================
 * API SERVICE LAYER - Backend Integration with Type Safety
 * ============================================================================
 * 
 * Purpose: Centralized, type-safe API communication with Lambda.hu backend
 * 
 * Features:
 * - Full TypeScript type safety with strict typing
 * - Comprehensive error handling with custom error types
 * - Request/response interceptors
 * - Automatic retry logic with exponential backoff
 * - Request cancellation support
 * - Response caching
 * - Request deduplication
 */

// ============================================================================
// CONFIGURATION
// ============================================================================

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const DEFAULT_TIMEOUT = 30000; // 30 seconds
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // Initial retry delay in ms

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

// Error types for better error handling
export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public details?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export class NetworkError extends ApiError {
  constructor(message = 'Network connection failed') {
    super(message);
    this.name = 'NetworkError';
  }
}

export class ValidationError extends ApiError {
  constructor(message = 'Validation failed', details?: any) {
    super(message, 400, details);
    this.name = 'ValidationError';
  }
}

export class AuthenticationError extends ApiError {
  constructor(message = 'Authentication failed') {
    super(message, 401);
    this.name = 'AuthenticationError';
  }
}

export class NotFoundError extends ApiError {
  constructor(message = 'Resource not found') {
    super(message, 404);
    this.name = 'NotFoundError';
  }
}

// Product related types
export interface Product {
  id: number;
  name: string;
  description?: string;
  category?: Category;
  manufacturer?: Manufacturer;
  technical_specs?: TechnicalSpecs;
  price?: number;
  images?: string[];
  datasheets?: Datasheet[];
  created_at?: string;
  updated_at?: string;
}

export interface TechnicalSpecs {
  thermal_conductivity?: string;
  fire_classification?: string;
  compressive_strength?: string;
  density?: string;
  thickness_options?: string[];
  [key: string]: any;
}

export interface Datasheet {
  id: number;
  title: string;
  url: string;
  type: 'PDF' | 'DOC' | 'XLS';
  language: string;
  size?: number;
}

export interface Manufacturer {
  id: number;
  name: string;
  website?: string;
  logo?: string;
  country?: string;
}

export interface Category {
  id: number;
  name: string;
  slug?: string;
  parent_id?: number;
  children?: Category[];
  product_count?: number;
}

// Search related types
export interface SearchQuery {
  query: string;
  limit?: number;
  offset?: number;
  filters?: SearchFilters;
}

export interface SearchFilters {
  category_ids?: number[];
  manufacturer_ids?: number[];
  min_price?: number;
  max_price?: number;
  technical_specs?: Record<string, any>;
}

export interface SearchResult {
  id: string;
  product_id?: number;
  name: string;
  description: string;
  category: string;
  manufacturer?: string;
  similarity_score: number;
  price?: number;
  thumbnail?: string;
  metadata?: Record<string, any>;
}

export interface SearchResponse {
  query: string;
  total_results: number;
  results: SearchResult[];
  facets?: SearchFacets;
  took_ms?: number;
}

export interface SearchFacets {
  categories: FacetBucket[];
  manufacturers: FacetBucket[];
  price_ranges: FacetBucket[];
}

export interface FacetBucket {
  key: string;
  doc_count: number;
  label?: string;
}

// System monitoring types
export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  message: string;
  timestamp: string;
  services?: ServiceHealth[];
}

export interface ServiceHealth {
  name: string;
  status: 'up' | 'down';
  latency_ms?: number;
  error?: string;
}

export interface SystemMetrics {
  health: SystemHealth;
  database: DatabaseMetrics;
  performance: PerformanceMetrics;
  resources: ResourceMetrics;
}

export interface DatabaseMetrics {
  total_products: number;
  total_manufacturers: number;
  total_categories: number;
  processed_files: number;
  last_updated: string;
  database_status: string;
  products_by_manufacturer: Array<{
    manufacturer: string;
    count: number;
  }>;
}

export interface PerformanceMetrics {
  api_response_time_ms: number;
  search_accuracy: number;
  active_connections: number;
  uptime_seconds: number;
  requests_per_minute: number;
  error_rate: number;
}

export interface ResourceMetrics {
  memory_usage_percent: number;
  cpu_usage_percent: number;
  disk_usage_percent: number;
  memory_total_mb: number;
  memory_used_mb: number;
}

// AI Chat types
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  context?: Record<string, any>;
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
  sources?: ChatSource[];
  suggested_actions?: string[];
}

export interface ChatSource {
  type: 'product' | 'document' | 'web';
  title: string;
  url?: string;
  snippet?: string;
}

// Admin types
export interface ScrapingTask {
  task_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  scraper_type: string;
  started_at?: string;
  completed_at?: string;
  items_scraped?: number;
  errors?: string[];
}

// Pagination types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface PaginationParams {
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

// ============================================================================
// REQUEST INTERCEPTOR & HELPERS
// ============================================================================

type RequestInterceptor = (config: RequestConfig) => RequestConfig | Promise<RequestConfig>;
type ResponseInterceptor<T = any> = (response: T) => T | Promise<T>;
type ErrorInterceptor = (error: ApiError) => Promise<never>;

interface RequestConfig extends RequestInit {
  url?: string;
  timeout?: number;
  retries?: number;
  cache?: boolean;
  dedupe?: boolean;
}

// Request deduplication cache
const pendingRequests = new Map<string, Promise<any>>();

// Response cache
interface CacheEntry {
  data: any;
  timestamp: number;
  ttl: number;
}

const responseCache = new Map<string, CacheEntry>();

// ============================================================================
// API SERVICE CLASS
// ============================================================================

export class ApiService {
  private baseUrl: string;
  private defaultHeaders: HeadersInit;
  private requestInterceptors: RequestInterceptor[] = [];
  private responseInterceptors: ResponseInterceptor[] = [];
  private errorInterceptors: ErrorInterceptor[] = [];
  private abortControllers = new Map<string, AbortController>();

  constructor(baseUrl = API_BASE_URL) {
    this.baseUrl = baseUrl;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
  }

  /**
   * Add request interceptor
   */
  addRequestInterceptor(interceptor: RequestInterceptor): void {
    this.requestInterceptors.push(interceptor);
  }

  /**
   * Add response interceptor
   */
  addResponseInterceptor(interceptor: ResponseInterceptor): void {
    this.responseInterceptors.push(interceptor);
  }

  /**
   * Add error interceptor
   */
  addErrorInterceptor(interceptor: ErrorInterceptor): void {
    this.errorInterceptors.push(interceptor);
  }

  /**
   * Create a unique request key for deduplication
   */
  private createRequestKey(endpoint: string, options?: RequestConfig): string {
    return `${options?.method || 'GET'}-${endpoint}-${JSON.stringify(options?.body || {})}`;
  }

  /**
   * Check and get cached response
   */
  private getCachedResponse(key: string): any | null {
    const cached = responseCache.get(key);
    if (cached && Date.now() - cached.timestamp < cached.ttl) {
      return cached.data;
    }
    responseCache.delete(key);
    return null;
  }

  /**
   * Cache response
   */
  private cacheResponse(key: string, data: any, ttl = 60000): void {
    responseCache.set(key, {
      data,
      timestamp: Date.now(),
      ttl,
    });
  }

  /**
   * Core request method with error handling, retries, and caching
   */
  private async request<T>(
    endpoint: string,
    options: RequestConfig = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const requestKey = this.createRequestKey(endpoint, options);

    // Check for request deduplication
    if (options.dedupe !== false && pendingRequests.has(requestKey)) {
      return pendingRequests.get(requestKey);
    }

    // Check cache
    if (options.cache && options.method === 'GET') {
      const cached = this.getCachedResponse(requestKey);
      if (cached) {
        return cached;
      }
    }

    // Create abort controller for this request
    const abortController = new AbortController();
    const requestId = `${Date.now()}-${Math.random()}`;
    this.abortControllers.set(requestId, abortController);

    // Prepare request config
    let config: RequestConfig = {
      ...options,
      url,
      headers: {
        ...this.defaultHeaders,
        ...options.headers,
      },
      signal: abortController.signal,
    };

    // Apply request interceptors
    for (const interceptor of this.requestInterceptors) {
      config = await interceptor(config);
    }

    // Create the request promise
    const requestPromise = this.executeRequest<T>(config, requestId);

    // Store for deduplication
    if (options.dedupe !== false) {
      pendingRequests.set(requestKey, requestPromise);
      requestPromise.finally(() => {
        pendingRequests.delete(requestKey);
      });
    }

    try {
      const response = await requestPromise;

      // Cache successful GET responses
      if (options.cache && options.method === 'GET') {
        this.cacheResponse(requestKey, response);
      }

      return response;
    } finally {
      this.abortControllers.delete(requestId);
    }
  }

  /**
   * Execute request with timeout and retries
   */
  private async executeRequest<T>(
    config: RequestConfig,
    requestId: string,
    retryCount = 0
  ): Promise<T> {
    const timeout = config.timeout || DEFAULT_TIMEOUT;
    const maxRetries = config.retries ?? MAX_RETRIES;

    try {
      // Create timeout promise
      const timeoutPromise = new Promise<never>((_, reject) => {
        setTimeout(() => {
          const controller = this.abortControllers.get(requestId);
          controller?.abort();
          reject(new ApiError('Request timeout', 408));
        }, timeout);
      });

      // Create fetch promise
      const fetchPromise = fetch(config.url!, {
        ...config,
        headers: config.headers,
      });

      // Race between fetch and timeout
      const response = await Promise.race([fetchPromise, timeoutPromise]);

      // Check response status
      if (!response.ok) {
        throw await this.createApiError(response);
      }

      // Parse response
      let data: T;
      const contentType = response.headers.get('content-type');
      
      if (contentType?.includes('application/json')) {
        data = await response.json();
      } else if (contentType?.includes('text/')) {
        data = await response.text() as T;
      } else {
        data = await response.blob() as T;
      }

      // Apply response interceptors
      for (const interceptor of this.responseInterceptors) {
        data = await interceptor(data);
      }

      return data;

    } catch (error) {
      // Handle network errors
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new NetworkError('Network request failed');
      }

      // Handle aborted requests
      if (error instanceof Error && error.name === 'AbortError') {
        throw new ApiError('Request was cancelled', 499);
      }

      // Convert to ApiError if needed
      const apiError = error instanceof ApiError ? error : new ApiError(
        error instanceof Error ? error.message : 'Unknown error occurred'
      );

      // Apply error interceptors
      for (const interceptor of this.errorInterceptors) {
        try {
          await interceptor(apiError);
        } catch (interceptedError) {
          // If interceptor throws, use that error
          throw interceptedError;
        }
      }

      // Retry logic
      if (retryCount < maxRetries && this.shouldRetry(apiError)) {
        const delay = RETRY_DELAY * Math.pow(2, retryCount); // Exponential backoff
        await new Promise(resolve => setTimeout(resolve, delay));
        return this.executeRequest<T>(config, requestId, retryCount + 1);
      }

      throw apiError;
    }
  }

  /**
   * Create appropriate error from response
   */
  private async createApiError(response: Response): Promise<ApiError> {
    let message = response.statusText;
    let details: any;

    try {
      const errorData = await response.json();
      message = errorData.message || errorData.detail || message;
      details = errorData;
    } catch {
      // Ignore JSON parse errors
    }

    switch (response.status) {
      case 400:
        return new ValidationError(message, details);
      case 401:
        return new AuthenticationError(message);
      case 404:
        return new NotFoundError(message);
      default:
        return new ApiError(message, response.status, details);
    }
  }

  /**
   * Determine if request should be retried
   */
  private shouldRetry(error: ApiError): boolean {
    // Retry on network errors
    if (error instanceof NetworkError) return true;
    
    // Retry on specific status codes
    const retryableStatusCodes = [408, 429, 500, 502, 503, 504];
    return error.statusCode ? retryableStatusCodes.includes(error.statusCode) : false;
  }

  /**
   * Cancel a specific request
   */
  cancelRequest(requestId: string): void {
    const controller = this.abortControllers.get(requestId);
    if (controller) {
      controller.abort();
      this.abortControllers.delete(requestId);
    }
  }

  /**
   * Cancel all pending requests
   */
  cancelAllRequests(): void {
    this.abortControllers.forEach(controller => controller.abort());
    this.abortControllers.clear();
  }

  // ============================================================================
  // PRODUCT ENDPOINTS
  // ============================================================================

  async getProducts(params?: PaginationParams): Promise<PaginatedResponse<Product>> {
    const queryParams = new URLSearchParams({
      page: String(params?.page || 1),
      page_size: String(params?.page_size || 20),
      ...(params?.sort_by && { sort_by: params.sort_by }),
      ...(params?.sort_order && { sort_order: params.sort_order }),
    });

    return this.request<PaginatedResponse<Product>>(
      `/products?${queryParams}`,
      { cache: true }
    );
  }

  async getProduct(id: number): Promise<Product> {
    return this.request<Product>(`/products/${id}`, { cache: true });
  }

  async createProduct(product: Omit<Product, 'id' | 'created_at' | 'updated_at'>): Promise<Product> {
    return this.request<Product>('/products', {
      method: 'POST',
      body: JSON.stringify(product),
    });
  }

  async updateProduct(id: number, updates: Partial<Product>): Promise<Product> {
    return this.request<Product>(`/products/${id}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteProduct(id: number): Promise<void> {
    return this.request<void>(`/products/${id}`, {
      method: 'DELETE',
    });
  }

  // ============================================================================
  // CATEGORY ENDPOINTS
  // ============================================================================

  async getCategories(): Promise<Category[]> {
    return this.request<Category[]>('/categories', { cache: true });
  }

  async getCategory(id: number): Promise<Category> {
    return this.request<Category>(`/categories/${id}`, { cache: true });
  }

  async getCategoryProducts(
    categoryId: number,
    params?: PaginationParams
  ): Promise<PaginatedResponse<Product>> {
    const queryParams = new URLSearchParams({
      page: String(params?.page || 1),
      page_size: String(params?.page_size || 20),
    });

    return this.request<PaginatedResponse<Product>>(
      `/categories/${categoryId}/products?${queryParams}`,
      { cache: true }
    );
  }

  // ============================================================================
  // MANUFACTURER ENDPOINTS
  // ============================================================================

  async getManufacturers(): Promise<Manufacturer[]> {
    return this.request<Manufacturer[]>('/manufacturers', { cache: true });
  }

  async getManufacturer(id: number): Promise<Manufacturer> {
    return this.request<Manufacturer>(`/manufacturers/${id}`, { cache: true });
  }

  async getManufacturerProducts(
    manufacturerId: number,
    params?: PaginationParams
  ): Promise<PaginatedResponse<Product>> {
    const queryParams = new URLSearchParams({
      page: String(params?.page || 1),
      page_size: String(params?.page_size || 20),
    });

    return this.request<PaginatedResponse<Product>>(
      `/manufacturers/${manufacturerId}/products?${queryParams}`,
      { cache: true }
    );
  }

  // ============================================================================
  // SEARCH ENDPOINTS
  // ============================================================================

  async search(query: SearchQuery): Promise<SearchResponse> {
    return this.request<SearchResponse>('/search', {
      method: 'POST',
      body: JSON.stringify(query),
      cache: false, // Don't cache search results
    });
  }

  async searchRAG(query: string, limit = 10): Promise<SearchResponse> {
    return this.request<SearchResponse>('/search/rag', {
      method: 'POST',
      body: JSON.stringify({ query, limit }),
      cache: false,
    });
  }

  async getSuggestions(query: string): Promise<string[]> {
    return this.request<string[]>(`/search/suggestions?q=${encodeURIComponent(query)}`, {
      cache: true,
      dedupe: true,
    });
  }

  // ============================================================================
  // AI CHAT ENDPOINTS
  // ============================================================================

  async sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
    return this.request<ChatResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getChatHistory(conversationId: string): Promise<ChatMessage[]> {
    return this.request<ChatMessage[]>(`/chat/history/${conversationId}`);
  }

  // ============================================================================
  // SYSTEM MONITORING ENDPOINTS
  // ============================================================================

  async getSystemHealth(): Promise<SystemHealth> {
    return this.request<SystemHealth>('/health', {
      cache: false,
      retries: 1,
      timeout: 5000,
    });
  }

  async getSystemMetrics(): Promise<SystemMetrics> {
    return this.request<SystemMetrics>('/metrics', {
      cache: false,
    });
  }

  async getPerformanceMetrics(): Promise<PerformanceMetrics> {
    return this.request<PerformanceMetrics>('/api/performance', {
      cache: false,
    });
  }

  // ============================================================================
  // ADMIN ENDPOINTS
  // ============================================================================

  async triggerScraping(scraperType: string): Promise<ScrapingTask> {
    return this.request<ScrapingTask>('/admin/scraping/trigger', {
      method: 'POST',
      body: JSON.stringify({ scraper_type: scraperType }),
    });
  }

  async getScrapingStatus(taskId: string): Promise<ScrapingTask> {
    return this.request<ScrapingTask>(`/admin/scraping/status/${taskId}`);
  }

  async getScrapingTasks(): Promise<ScrapingTask[]> {
    return this.request<ScrapingTask[]>('/admin/scraping/tasks');
  }

  // ============================================================================
  // FILE UPLOAD ENDPOINTS
  // ============================================================================

  async uploadFile(file: File, onProgress?: (progress: number) => void): Promise<{ url: string }> {
    const formData = new FormData();
    formData.append('file', file);

    // Note: Don't set Content-Type header for FormData
    const headers = { ...this.defaultHeaders };
    delete headers['Content-Type'];

    return this.request<{ url: string }>('/upload', {
      method: 'POST',
      body: formData,
      headers,
    });
  }

  async uploadDatasheet(productId: number, file: File): Promise<Datasheet> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('product_id', String(productId));

    const headers = { ...this.defaultHeaders };
    delete headers['Content-Type'];

    return this.request<Datasheet>('/products/datasheets', {
      method: 'POST',
      body: formData,
      headers,
    });
  }
}

// ============================================================================
// DEFAULT API INSTANCE WITH INTERCEPTORS
// ============================================================================

export const api = new ApiService();

// Add authentication interceptor
api.addRequestInterceptor((config) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  if (token) {
    config.headers = {
      ...config.headers,
      'Authorization': `Bearer ${token}`,
    };
  }
  return config;
});

// Add logging interceptor (development only)
if (process.env.NODE_ENV === 'development') {
  api.addRequestInterceptor((config) => {
    console.log(`[API Request] ${config.method || 'GET'} ${config.url}`);
    return config;
  });

  api.addResponseInterceptor((response) => {
    console.log('[API Response]', response);
    return response;
  });

  api.addErrorInterceptor(async (error) => {
    console.error('[API Error]', error);
    throw error;
  });
}

// ============================================================================
// REACT HOOKS (if using React)
// ============================================================================

export function useApi() {
  return api;
}

// ============================================================================
// EXPORT ALL TYPES
// ============================================================================

export * from './api';