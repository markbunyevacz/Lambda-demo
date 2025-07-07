'use client';

import React, { useState, useEffect } from 'react';

// Helper function for className joining
function cn(...classes: (string | boolean | undefined)[]): string {
  return classes.filter(Boolean).join(' ');
}

// Icons
const IconSearch = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
  </svg>
);

const IconRefresh = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
  </svg>
);

const IconFilter = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.207A1 1 0 013 6.5V4z" />
  </svg>
);

const IconEye = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
  </svg>
);

const IconChevronLeft = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
  </svg>
);

const IconChevronRight = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
  </svg>
);

interface AdminProduct {
  id: number;
  name: string;
  sku?: string;
  price?: number;
  manufacturer?: string;
  category?: string;
  technical_specs_count: number;
  has_full_text: boolean;
  full_text_length: number;
  created_at?: string;
}

interface AdminProductsResponse {
  success: boolean;
  data: {
    products: AdminProduct[];
    pagination: {
      total: number;
      limit: number;
      offset: number;
      has_more: boolean;
    };
  };
}

// Admin API Base URL
const ADMIN_API_BASE = 'http://localhost:8000/admin';

export default function AdminProducts() {
  const [products, setProducts] = useState<AdminProduct[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(25);
  const [totalItems, setTotalItems] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  
  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [manufacturerFilter, setManufacturerFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [manufacturers, setManufacturers] = useState<string[]>([]);
  const [categories, setCategories] = useState<string[]>([]);

  // Load products from admin API
  const loadProducts = async (isRefresh = false) => {
    if (isRefresh) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }
    setError(null);

    try {
      const offset = (currentPage - 1) * itemsPerPage;
      const params = new URLSearchParams({
        limit: itemsPerPage.toString(),
        offset: offset.toString()
      });

      if (manufacturerFilter) {
        params.append('manufacturer', manufacturerFilter);
      }
      if (categoryFilter) {
        params.append('category', categoryFilter);
      }

      const response = await fetch(`${ADMIN_API_BASE}/database/products?${params}`);
      
      if (!response.ok) {
        throw new Error(`API hiba: ${response.statusText}`);
      }

      const data: AdminProductsResponse = await response.json();
      
      if (!data.success) {
        throw new Error('API válasz nem sikeres');
      }

      // Filter products locally by search term if provided
      let filteredProducts = data.data.products;
      if (searchTerm.trim()) {
        const search = searchTerm.toLowerCase();
        filteredProducts = filteredProducts.filter(product =>
          product.name.toLowerCase().includes(search) ||
          product.sku?.toLowerCase().includes(search) ||
          product.manufacturer?.toLowerCase().includes(search) ||
          product.category?.toLowerCase().includes(search)
        );
      }

      setProducts(filteredProducts);
      setTotalItems(data.data.pagination.total);
      setHasMore(data.data.pagination.has_more);

      // Extract unique manufacturers and categories for filters
      const uniqueManufacturers = [...new Set(data.data.products.map(p => p.manufacturer).filter(Boolean))];
      const uniqueCategories = [...new Set(data.data.products.map(p => p.category).filter(Boolean))];
      setManufacturers(uniqueManufacturers);
      setCategories(uniqueCategories);

    } catch (err) {
      console.error('Failed to load products:', err);
      setError(err instanceof Error ? err.message : 'Ismeretlen hiba történt');
      setProducts([]);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  // Load initial data
  useEffect(() => {
    loadProducts();
  }, [currentPage, itemsPerPage, manufacturerFilter, categoryFilter]);

  // Handle search with debounce
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (searchTerm !== '') {
        setCurrentPage(1); // Reset to first page when searching
      }
      loadProducts();
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [searchTerm]);

  // Pagination helpers
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startItem = (currentPage - 1) * itemsPerPage + 1;
  const endItem = Math.min(currentPage * itemsPerPage, totalItems);

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage);
    }
  };

  const clearFilters = () => {
    setSearchTerm('');
    setManufacturerFilter('');
    setCategoryFilter('');
    setCurrentPage(1);
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="bg-white border rounded-lg p-4">
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-4 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Termék Kezelés</h2>
          <p className="text-gray-600 mt-1">
            {totalItems} termék az adatbázisban
          </p>
        </div>
        <button
          onClick={() => loadProducts(true)}
          disabled={isRefreshing}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          <IconRefresh className={cn("mr-2", isRefreshing && "animate-spin")} />
          {isRefreshing ? 'Frissítés...' : 'Frissítés'}
        </button>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          <span>Hiba a termékek betöltésében: {error}</span>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white border rounded-lg p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-800 flex items-center">
            <IconFilter className="mr-2" />
            Szűrők és Keresés
          </h3>
          <button
            onClick={clearFilters}
            className="text-sm text-blue-600 hover:text-blue-700"
          >
            Szűrők törlése
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search */}
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <IconSearch className="text-gray-400" />
            </div>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Keresés..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Manufacturer Filter */}
          <select
            value={manufacturerFilter}
            onChange={(e) => setManufacturerFilter(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
          >
            <option value="">Összes gyártó</option>
            {manufacturers.map(mfr => (
              <option key={mfr} value={mfr}>{mfr}</option>
            ))}
          </select>

          {/* Category Filter */}
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
          >
            <option value="">Összes kategória</option>
            {categories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>

          {/* Items per page */}
          <select
            value={itemsPerPage}
            onChange={(e) => {
              setItemsPerPage(Number(e.target.value));
              setCurrentPage(1);
            }}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
          >
            <option value={10}>10 / oldal</option>
            <option value={25}>25 / oldal</option>
            <option value={50}>50 / oldal</option>
            <option value={100}>100 / oldal</option>
          </select>
        </div>
      </div>

      {/* Products Table */}
      <div className="bg-white border rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Termék
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  SKU
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Gyártó
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Kategória
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ár
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Műszaki Adatok
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Szöveges Tartalom
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Létrehozva
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Műveletek
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {products.map((product) => (
                <tr key={product.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-900 max-w-xs truncate">
                      {product.name}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-600">
                      {product.sku || '-'}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    {product.manufacturer ? (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {product.manufacturer}
                      </span>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    {product.category ? (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        {product.category}
                      </span>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-900">
                      {product.price ? `${product.price.toLocaleString()} Ft` : '-'}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    {product.technical_specs_count > 0 ? (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                        {product.technical_specs_count} paraméter
                      </span>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-600">
                      {product.has_full_text ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                          {(product.full_text_length / 1000).toFixed(1)}k karakter
                        </span>
                      ) : (
                        <span className="text-gray-400">Nincs</span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-600">
                      {product.created_at ? new Date(product.created_at).toLocaleDateString('hu-HU') : '-'}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <button
                      onClick={() => window.open(`http://localhost:8000/products/${product.id}/view`, '_blank')}
                      className="inline-flex items-center p-1 text-gray-400 hover:text-blue-500"
                      title="Termék megtekintése"
                    >
                      <IconEye />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Empty State */}
        {products.length === 0 && !isLoading && (
          <div className="text-center py-12">
            <div className="text-gray-500 mb-4">
              Nincs találat a megadott szűrőkkel.
            </div>
            <button
              onClick={clearFilters}
              className="text-blue-600 hover:text-blue-700 text-sm"
            >
              Szűrők törlése
            </button>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="bg-white px-4 py-3 border-t border-gray-200 sm:px-6">
            <div className="flex items-center justify-between">
              <div className="flex-1 flex justify-between sm:hidden">
                <button
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                  className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Előző
                </button>
                <button
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Következő
                </button>
              </div>
              <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm text-gray-700">
                    <span className="font-medium">{startItem}</span>
                    {' - '}
                    <span className="font-medium">{endItem}</span>
                    {' / '}
                    <span className="font-medium">{totalItems}</span>
                    {' találat'}
                  </p>
                </div>
                <div>
                  <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                    <button
                      onClick={() => handlePageChange(currentPage - 1)}
                      disabled={currentPage === 1}
                      className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <IconChevronLeft />
                    </button>
                    
                    {/* Page numbers */}
                    {[...Array(Math.min(5, totalPages))].map((_, index) => {
                      const pageNumber = Math.max(1, currentPage - 2) + index;
                      if (pageNumber > totalPages) return null;
                      
                      return (
                        <button
                          key={pageNumber}
                          onClick={() => handlePageChange(pageNumber)}
                          className={cn(
                            "relative inline-flex items-center px-4 py-2 border text-sm font-medium",
                            currentPage === pageNumber
                              ? "z-10 bg-blue-50 border-blue-500 text-blue-600"
                              : "bg-white border-gray-300 text-gray-500 hover:bg-gray-50"
                          )}
                        >
                          {pageNumber}
                        </button>
                      );
                    })}
                    
                    <button
                      onClick={() => handlePageChange(currentPage + 1)}
                      disabled={currentPage === totalPages}
                      className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <IconChevronRight />
                    </button>
                  </nav>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 