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
// Default localhost development, production URL via environment variable
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
  id: number;                                    // Primary key
  name: string;                                  // Termék neve
  description?: string;                          // Leírás (opcionális)
  price?: number;                                // Ár HUF-ban (opcionális)
  technical_specs?: Record<string, any>;        // Műszaki adatok JSONB
  raw_specs?: Record<string, any>;              // Nyers scraped adatok JSONB
  full_text_content?: string;                   // Teljes szöveges tartalom (kereséshez)
  category_id?: number;                         // Kategória hivatkozás
  manufacturer_id?: number;                     // Gyártó hivatkozás
  manufacturer?: Manufacturer;                  // Gyártó objektum (joined)
  category?: Category;                          // Kategória objektum (joined)
  created_at: string;                          // Létrehozás időpontja (ISO string)
  updated_at?: string;                         // Módosítás időpontja (opcionális)
}

// Gyártó adatstruktúra (backend Manufacturer schema)
export interface Manufacturer {
  id: number;                                  // Primary key
  name: string;                                // Gyártó neve (pl. "ROCKWOOL")
  description?: string;                        // Gyártó leírása
  website?: string;                           // Hivatalos weboldal URL
  country?: string;                           // Származási ország
}

// Kategória adatstruktúra (backend Category schema)
export interface Category {
  id: number;                                 // Primary key
  name: string;                               // Kategória neve (pl. "Hőszigetelés")
  description?: string;                       // Kategória leírása
  parent_id?: number;                        // Szülő kategória (hierarchikus struktúra)
  children: Category[];                      // Gyermek kategóriák listája
}

// RAG keresési kérés (backend SearchRequest schema)
export interface SearchRequest {
  query: string;                             // Természetes nyelvű keresési kifejezés
  limit?: number;                           // Találatok száma (alapértelmezett: 10)
}

// RAG keresési eredmény (backend search response)
export interface SearchResult {
  rank: number;                             // Találat rangsor
  name: string;                             // Termék neve
  category: string;                         // Kategória neve
  description: string;                      // Termék leírása
  full_content: string;                     // Teljes indexelt tartalom
  metadata: Record<string, any>;           // További metaadatok (product_id, stb.)
  similarity_score: number;                // Hasonlósági pontszám (0-1)
}

// RAG keresési válasz (backend search response wrapper)
export interface SearchResponse {
  query: string;                           // Eredeti keresési kifejezés
  total_results: number;                   // Összes találat száma
  collection_size: number;                 // ChromaDB collection mérete
  results: SearchResult[];                 // Találatok listája
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
  constructor(baseUrl: string = API_BASE_URL) {
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
   * @returns Promise<{status: string}> - Rendszer státusz
   * 
   * Backend endpoint: GET /health
   * Ellenőrzi: PostgreSQL, ChromaDB, API elérhetőség
   */
  async healthCheck(): Promise<{ status: string }> {
    return this.request<{ status: string }>('/health');
  }

  /**
   * ============================================================================
   * ADMIN ENDPOINTS - Adminisztrációs funkciók
   * ============================================================================
   */

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