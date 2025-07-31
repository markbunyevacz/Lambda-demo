/**
 * ============================================================================
 * API SERVICE LAYER - Backend Integration
 * ============================================================================
 * 
 * Célja: Centralizált API kommunikáció a Lambda.hu backend-del
 * 
 * Architekturális szerepe:
 * - Type-safe API calls TypeScript interface-ekkel
 * - Centralizált error handling és request configuration
 * - Backend endpoint abstraction (clean API surface)
 * - Request/response transformation layer
 * 
 * Backend integráció:
 * - FastAPI server (http://localhost:8000)
 * - PostgreSQL adatbázis (termékek, gyártók, kategóriák)
 * - ChromaDB RAG search (természetes nyelvű keresés)
 * - Admin endpoints (scraping, monitoring)
 * 
 * Type safety:
 * - Backend schema mapping TypeScript interface-ekhez
 * - Generic request method type parameterekkel
 * - Compile-time type checking API call-oknál
 * 
 * Error handling strategy:
 * - Network error graceful handling
 * - HTTP status code validation
 * - JSON parsing error protection
 * - User-friendly error messages
 * 
 * Performance optimizations:
 * - Single API instance (singleton pattern)
 * - Request deduplication capability (future enhancement)
 * - Response caching support (future enhancement)
 */

// Environment configuration
// Default to an absolute URL for client-side requests, can be overridden for server-side
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * ============================================================================
 * TYPE DEFINITIONS - Backend Schema Mapping
 * ============================================================================
 * 
 * Ezek a típusok a backend Pydantic schema-kkal kompatibilisek
 * Minden interface a backend schemas.py fájlban definiált modelleket tükrözi
 */

// Termék adatstruktúra (backend Product schema)
export interface Product {
  id: number;
  name: string;
  description?: string;
  category?: Category;
  manufacturer?: Manufacturer;
  technical_specs?: Record<string, any>;
  price?: number;
  created_at?: string;
}

export interface Manufacturer {
  id: number;
  name: string;
  website?: string;
}

export interface Category {
  id: number;
  name: string;
  parent_id?: number;
}

export interface SearchResult {
  id: string;
  name: string;
  description: string;
  category: string;
  similarity_score: number;
  metadata: {
    product_id?: number;
    manufacturer?: string;
    price?: number;
    confidence?: number;
  };
}

export interface SearchResponse {
  query: string;
  total_results: number;
  results: SearchResult[];
}

export interface SystemStats {
  totalProducts: number;
  totalManufacturers: number;
  lastUpdated: string | null;
}

export interface HealthStatus {
  status: string;
  message: string;
  timestamp?: string;
}

export interface DatabaseOverview {
  success: boolean;
  data: {
    manufacturers: number;
    categories: number;
    products: number;
    processed_files: number;
    last_updated: string;
    database_status: string;
    products_by_manufacturer: Array<{
      manufacturer: string;
      count: number;
    }>;
  };
}

export interface SystemMetrics {
  health: HealthStatus;
  database: DatabaseOverview;
  performance: {
    api_response_time?: number;
    search_accuracy?: number;
    active_connections?: number;
    uptime?: string;
  };
  resources: {
    memory_usage?: number;
    cpu_usage?: number;
    disk_space?: number;
  };
}

/**
 * ============================================================================
 * API SERVICE CLASS - Centralizált Backend Kommunikáció
 * ============================================================================
 */
export class ApiService {
  private baseUrl: string;

  /**
   * Constructor - API service inicializálás
   * @param baseUrl - Backend server URL (alapértelmezett: localhost:8000)
   */
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  /**
   * ============================================================================
   * PRIVATE REQUEST METHOD - Centralizált HTTP Communication
   * ============================================================================
   * 
   * Generic request method minden API call-hoz
   * Centralizált error handling és response transformation
   * 
   * @param endpoint - API endpoint relative path
   * @param options - Fetch RequestInit options
   * @returns Promise<T> - Type-safe response
   * 
   * Error handling:
   * - Network errors (connection failed)
   * - HTTP errors (4xx, 5xx status codes)
   * - JSON parsing errors
   * - Timeout handling (future enhancement)
   */
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      });

      // HTTP status validation
      if (!response.ok) {
        throw new Error(`API request failed: ${response.statusText}`);
      }

      // JSON parsing with error protection
      return response.json();
      
    } catch (error) {
      // Enhanced error handling for different error types
      if (error instanceof TypeError) {
        // Network error (connection failed)
        throw new Error('Hálózati hiba: Nem lehet kapcsolódni a szerverhez');
      } else if (error instanceof SyntaxError) {
        // JSON parsing error
        throw new Error('Szerver válasz feldolgozási hiba');
      } else {
        // Re-throw API errors with original message
        throw error;
      }
    }
  }

  /**
   * ============================================================================
   * PRODUCT ENDPOINTS - Termék adatok kezelése
   * ============================================================================
   */

  /**
   * Termékek lekérdezése lapozással
   * 
   * @param limit - Termékek száma (alapértelmezett: 100)
   * @param offset - Eltolás (lapozáshoz)
   * @returns Promise<Product[]> - Termékek listája
   * 
   * Backend endpoint: GET /products?limit={limit}&offset={offset}
   */
  async getProducts(limit = 100, offset = 0): Promise<Product[]> {
    return this.request<Product[]>(`/products?limit=${limit}&offset=${offset}`);
  }

  /**
   * Egyedi termék lekérdezése ID alapján
   * 
   * @param id - Termék ID
   * @returns Promise<Product> - Termék adatok
   * 
   * Backend endpoint: GET /products/{id}
   */
  async getProduct(id: number): Promise<Product> {
    return this.request<Product>(`/products/${id}`);
  }

  /**
   * ============================================================================
   * CATEGORY ENDPOINTS - Kategória adatok kezelése
   * ============================================================================
   */

  /**
   * Összes kategória lekérdezése hierarchikus struktúrával
   * 
   * @returns Promise<Category[]> - Kategóriák listája
   * 
   * Backend endpoint: GET /categories
   * Hierarchikus adatstruktúra: parent-child kapcsolatok
   */
  async getCategories(): Promise<Category[]> {
    return this.request<Category[]>('/categories');
  }

  /**
   * ============================================================================
   * MANUFACTURER ENDPOINTS - Gyártó adatok kezelése
   * ============================================================================
   */

  /**
   * Összes gyártó lekérdezése
   * 
   * @returns Promise<Manufacturer[]> - Gyártók listája
   * 
   * Backend endpoint: GET /manufacturers
   * Gyártók: ROCKWOOL, Leier, Baumit
   */
  async getManufacturers(): Promise<Manufacturer[]> {
    return this.request<Manufacturer[]>('/manufacturers');
  }

  /**
   * ============================================================================
   * SEARCH ENDPOINTS - RAG-alapú Intelligens Keresés
   * ============================================================================
   */

  /**
   * RAG (Retrieval-Augmented Generation) alapú természetes nyelvű keresés
   * 
   * @param query - Természetes nyelvű keresési kifejezés
   * @param limit - Találatok maximális száma (alapértelmezett: 10)
   * @returns Promise<SearchResponse> - Keresési eredmények
   * 
   * Backend flow:
   * 1. Query vektorizálása (embeddings)
   * 2. ChromaDB similarity search
   * 3. PostgreSQL termékadatok kiegészítés
   * 4. Ranked results visszaadása
   * 
   * Backend endpoint: POST /search/rag
   */
  async searchRAG(query: string, limit = 10): Promise<SearchResponse> {
    return this.request<SearchResponse>('/search/rag', {
      method: 'POST',
      body: JSON.stringify({ query, limit }),
    });
  }

  /**
   * ============================================================================
   * SYSTEM ENDPOINTS - Rendszer státusz és monitoring
   * ============================================================================
   */

  /**
   * Rendszer egészség ellenőrzése
   * 
   * @returns Promise<{ status: string }> - Rendszer státusz
   * 
   * Backend endpoint: GET /health
   * Ellenőrzi: PostgreSQL, ChromaDB, API elérhetőség
   */
  async healthCheck(): Promise<{ status: string }> {
    return this.request<{ status: string }>('/health');
  }

  async getSystemMetrics(): Promise<SystemMetrics> {
    const startTime = Date.now();

    try {
      // VALÓDI API HÍVÁS a mock adatok helyett
      const overview = await this.request<DatabaseOverview>('/admin/database/overview');
      const apiResponseTime = Date.now() - startTime;

      if (!overview.success) {
        throw new Error('A szerver hibát jelzett az adatbázis áttekintésénél.');
      }

      // A kapott valós adatokat kombináljuk a még nem implementált,
      // de a UI által igényelt "mock" adatokkal.
      return {
        health: {
          status: 'healthy',
          message: 'All systems operational',
          timestamp: new Date().toISOString()
        },
        database: overview, // Itt használjuk a VALÓDI backend adatot
        performance: {
          api_response_time: apiResponseTime,
          search_accuracy: 0.94, // Placeholder
          active_connections: Math.floor(Math.random() * 50) + 10, // Placeholder
          uptime: '2 nap, 14 óra' // Placeholder
        },
        resources: {
          memory_usage: Math.floor(Math.random() * 1000) + 500, // Placeholder
          cpu_usage: Math.floor(Math.random() * 30) + 10, // Placeholder
          disk_space: Math.floor(Math.random() * 20) + 60 // Placeholder
        }
      };
    } catch (error) {
      console.error('getSystemMetrics hiba:', error);
      // Hibakezelés, ha az API hívás sikertelen
      return {
        health: {
          status: 'unhealthy',
          message: error instanceof Error ? error.message : 'Ismeretlen hiba a backend szolgáltatásokkal.',
          timestamp: new Date().toISOString()
        },
        database: {
          success: false,
          data: {
            manufacturers: 0,
            categories: 0,
            products: 0,
            processed_files: 0,
            last_updated: new Date().toISOString(),
            database_status: 'disconnected',
            products_by_manufacturer: []
          }
        },
        performance: {
          api_response_time: 0,
          search_accuracy: 0,
          active_connections: 0,
          uptime: 'Unknown'
        },
        resources: {
          memory_usage: 0,
          cpu_usage: 0,
          disk_space: 0
        }
      };
    }
  }

  /**
   * ============================================================================
   * ADMIN ENDPOINTS - Adminisztrációs funkciók
   * ============================================================================
   */

  async getExtractionComparisonReport(): Promise<{ success: boolean; data: any[] }> {
    return this.request<{ success: boolean; data: any[] }>('/admin/analysis/extraction-comparison');
  }

  /**
   * Scraping folyamat indítása (admin funkció)
   * 
   * @param scraperType - Scraper típusa ('datasheet' | 'brochure')
   * @returns Promise<{task_id: string}> - Background task ID
   * 
   * Backend endpoint: POST /api/v1/scrape
   * Background processing: Celery task queue
   */
  async triggerScraping(scraperType: 'datasheet' | 'brochure'): Promise<{ task_id: string }> {
    return this.request<{ task_id: string }>('/api/v1/scrape', {
      method: 'POST',
      body: JSON.stringify({ scraper_type: scraperType }),
    });
  }

  // AI Configuration endpoints
  async getAIConfig(): Promise<any> {
    return this.request<any>('/api/ai-config/config');
  }

  async updateAIConfig(config: any): Promise<any> {
    return this.request<any>('/api/ai-config/config', {
      method: 'PUT',
      body: JSON.stringify(config),
    });
  }

  async getAIProviders(): Promise<any> {
    return this.request<any>('/api/ai-config/providers');
  }

  async testAIConfig(): Promise<any> {
    return this.request<any>('/api/ai-config/test', {
      method: 'POST',
    });
  }

  async getUsageStats(): Promise<any> {
    return this.request<any>('/api/ai-config/usage');
  }
}

/**
 * ============================================================================
 * DEFAULT API INSTANCE - Singleton Pattern
 * ============================================================================
 * 
 * Egyetlen API service instance az egész alkalmazáshoz
 * Előnyök:
 * - Configuration consistency
 * - Memory efficiency
 * - Easy mocking for tests
 * - Shared connection pooling (future enhancement)
 */
export const api = new ApiService();

/**
 * ============================================================================
 * USAGE EXAMPLES
 * ============================================================================
 * 
 * // Termékek lekérdezése
 * const products = await api.getProducts(50, 0);
 * 
 * // RAG keresés
 * const searchResults = await api.searchRAG("hőszigetelés családi házhoz", 5);
 * 
 * // System monitoring
 * const metrics = await api.getSystemMetrics();
 * 
 * // Error handling
 * try {
 *   const product = await api.getProduct(123);
 * } catch (error) {
 *   console.error('Termék betöltési hiba:', error.message);
 * }
 * 
 * // Component integration
 * useEffect(() => {
 *   api.getManufacturers()
 *     .then(setManufacturers)
 *     .catch(handleError);
 * }, []);
 * 
 * ============================================================================
 * FUTURE ENHANCEMENTS
 * ============================================================================
 * 
 * Request Caching:
 * - React Query integration
 * - Local storage caching
 * - Cache invalidation strategies
 * 
 * Request Optimization:
 * - Request deduplication
 * - Batch API calls
 * - GraphQL migration consideration
 * 
 * Error Enhancement:
 * - Retry mechanisms
 * - Circuit breaker pattern
 * - User notification integration
 * 
 * Performance:
 * - Request/response compression
 * - Connection pooling
 * - Request timeout configuration
 * 
 * ============================================================================
 */ 