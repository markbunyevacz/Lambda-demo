/**
 * API Service Tests
 */

import { ApiService, ApiError, NetworkError, ValidationError } from '../lib/api';

// Mock fetch
global.fetch = jest.fn();

describe('ApiService', () => {
  let api: ApiService;

  beforeEach(() => {
    api = new ApiService('http://localhost:8000');
    jest.clearAllMocks();
  });

  describe('request method', () => {
    it('should make successful GET request', async () => {
      const mockData = { id: 1, name: 'Test Product' };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      const result = await api.getProduct(1);

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/products/1',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
      expect(result).toEqual(mockData);
    });

    it('should handle network errors', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(
        new TypeError('Failed to fetch')
      );

      await expect(api.getProduct(1)).rejects.toThrow(NetworkError);
    });

    it('should handle 404 errors', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: async () => ({ message: 'Product not found' }),
      });

      await expect(api.getProduct(1)).rejects.toThrow('Product not found');
    });

    it('should handle validation errors', async () => {
      const validationDetails = {
        fields: {
          name: 'Required field',
        },
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        json: async () => ({
          message: 'Validation failed',
          ...validationDetails,
        }),
      });

      try {
        await api.createProduct({} as any);
      } catch (error) {
        expect(error).toBeInstanceOf(ValidationError);
        expect((error as ValidationError).details).toMatchObject(validationDetails);
      }
    });

    it('should retry on transient errors', async () => {
      let callCount = 0;
      (global.fetch as jest.Mock).mockImplementation(() => {
        callCount++;
        if (callCount < 3) {
          return Promise.resolve({
            ok: false,
            status: 503,
            statusText: 'Service Unavailable',
            json: async () => ({ message: 'Service temporarily unavailable' }),
          });
        }
        return Promise.resolve({
          ok: true,
          json: async () => ({ id: 1 }),
          headers: new Headers({ 'content-type': 'application/json' }),
        });
      });

      const result = await api.getProduct(1);

      expect(callCount).toBe(3);
      expect(result).toEqual({ id: 1 });
    });

    it('should cache GET requests', async () => {
      const mockData = { id: 1, name: 'Test Product' };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      // First call
      const result1 = await api.getProduct(1);
      // Second call (should use cache)
      const result2 = await api.getProduct(1);

      expect(global.fetch).toHaveBeenCalledTimes(1);
      expect(result1).toEqual(mockData);
      expect(result2).toEqual(mockData);
    });

    it('should deduplicate concurrent requests', async () => {
      const mockData = { id: 1, name: 'Test Product' };
      let resolvePromise: (value: any) => void;
      const fetchPromise = new Promise((resolve) => {
        resolvePromise = resolve;
      });

      (global.fetch as jest.Mock).mockReturnValueOnce(fetchPromise);

      // Make concurrent requests
      const promise1 = api.getProduct(1);
      const promise2 = api.getProduct(1);

      // Resolve the fetch
      resolvePromise!({
        ok: true,
        json: async () => mockData,
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      const [result1, result2] = await Promise.all([promise1, promise2]);

      expect(global.fetch).toHaveBeenCalledTimes(1);
      expect(result1).toEqual(mockData);
      expect(result2).toEqual(mockData);
    });
  });

  describe('product endpoints', () => {
    it('should get products with pagination', async () => {
      const mockResponse = {
        items: [{ id: 1 }, { id: 2 }],
        total: 100,
        page: 1,
        page_size: 20,
        total_pages: 5,
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      const result = await api.getProducts({ page: 1, page_size: 20 });

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/products?page=1&page_size=20',
        expect.any(Object)
      );
      expect(result).toEqual(mockResponse);
    });

    it('should create a product', async () => {
      const newProduct = {
        name: 'New Product',
        description: 'Test description',
      };

      const mockResponse = {
        id: 1,
        ...newProduct,
        created_at: '2024-01-01T00:00:00Z',
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      const result = await api.createProduct(newProduct);

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/products',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(newProduct),
        })
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('search endpoints', () => {
    it('should perform RAG search', async () => {
      const mockResponse = {
        query: 'hőszigetelés',
        total_results: 5,
        results: [
          {
            id: '1',
            name: 'ROCKWOOL Frontrock',
            similarity_score: 0.95,
          },
        ],
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      const result = await api.searchRAG('hőszigetelés', 10);

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/search/rag',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ query: 'hőszigetelés', limit: 10 }),
        })
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('interceptors', () => {
    it('should apply request interceptor', async () => {
      const interceptor = jest.fn((config) => ({
        ...config,
        headers: {
          ...config.headers,
          'X-Custom-Header': 'test',
        },
      }));

      api.addRequestInterceptor(interceptor);

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: 1 }),
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      await api.getProduct(1);

      expect(interceptor).toHaveBeenCalled();
      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'X-Custom-Header': 'test',
          }),
        })
      );
    });

    it('should apply response interceptor', async () => {
      const interceptor = jest.fn((response) => ({
        ...response,
        modified: true,
      }));

      api.addResponseInterceptor(interceptor);

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: 1 }),
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      const result = await api.getProduct(1);

      expect(interceptor).toHaveBeenCalled();
      expect(result).toHaveProperty('modified', true);
    });

    it('should apply error interceptor', async () => {
      const interceptor = jest.fn(async (error) => {
        throw new Error('Intercepted: ' + error.message);
      });

      api.addErrorInterceptor(interceptor);

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: async () => ({ message: 'Server error' }),
      });

      await expect(api.getProduct(1)).rejects.toThrow('Intercepted: Server error');
      expect(interceptor).toHaveBeenCalled();
    });
  });

  describe('request cancellation', () => {
    it('should cancel all requests', () => {
      const abortSpy = jest.spyOn(AbortController.prototype, 'abort');

      // Start a request (don't await)
      api.getProduct(1);

      // Cancel all requests
      api.cancelAllRequests();

      expect(abortSpy).toHaveBeenCalled();
    });
  });
});