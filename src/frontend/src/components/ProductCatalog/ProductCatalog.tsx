'use client';

import { useState, useEffect } from 'react';
import { api, Product, Manufacturer, Category } from '@/lib/api';

// Helper function for className joining
function cn(...classes: (string | boolean | undefined)[]): string {
  return classes.filter(Boolean).join(' ');
}

// Icons
const IconFilter = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.207A1 1 0 013 6.5V4z" />
  </svg>
);

const IconChevronUp = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
  </svg>
);

const IconChevronDown = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
  </svg>
);

const IconEye = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
  </svg>
);

const IconRefresh = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
  </svg>
);

interface ProductFilters {
  manufacturer: string;
  category: string;
  hasPrice: boolean | null;
  search: string;
}

type SortField = 'name' | 'manufacturer' | 'category' | 'price' | 'created_at';
type SortDirection = 'asc' | 'desc';

interface ProductCatalogProps {
  onProductSelect?: (product: Product) => void;
}

export default function ProductCatalog({ onProductSelect }: ProductCatalogProps) {
  const [products, setProducts] = useState<Product[]>([]);
  const [filteredProducts, setFilteredProducts] = useState<Product[]>([]);
  const [manufacturers, setManufacturers] = useState<Manufacturer[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(25);
  
  // Sorting state
  const [sortField, setSortField] = useState<SortField>('name');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  
  // Filter state
  const [filters, setFilters] = useState<ProductFilters>({
    manufacturer: '',
    category: '',
    hasPrice: null,
    search: ''
  });

  // Load data
  const loadData = async (refresh = false) => {
    if (refresh) setIsRefreshing(true);
    else setIsLoading(true);
    
    try {
      const [productsData, manufacturersData, categoriesData] = await Promise.all([
        api.getProducts(1000, 0), // Load more products for filtering
        api.getManufacturers(),
        api.getCategories()
      ]);
      
      setProducts(productsData);
      setFilteredProducts(productsData);
      setManufacturers(manufacturersData);
      setCategories(categoriesData);
    } catch (error) {
      console.error('Failed to load catalog data:', error);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Apply filters and sorting
  useEffect(() => {
    let filtered = [...products];
    
    // Apply search filter
    if (filters.search.trim()) {
      const searchTerm = filters.search.toLowerCase();
      filtered = filtered.filter(product => 
        product.name.toLowerCase().includes(searchTerm) ||
        product.description?.toLowerCase().includes(searchTerm) ||
        product.manufacturer?.name.toLowerCase().includes(searchTerm)
      );
    }
    
    // Apply manufacturer filter
    if (filters.manufacturer) {
      filtered = filtered.filter(product => 
        product.manufacturer?.name === filters.manufacturer
      );
    }
    
    // Apply category filter
    if (filters.category) {
      filtered = filtered.filter(product => 
        product.category?.name === filters.category
      );
    }
    
    // Apply price filter
    if (filters.hasPrice !== null) {
      filtered = filtered.filter(product => 
        filters.hasPrice ? product.price !== null : product.price === null
      );
    }
    
    // Apply sorting
    filtered.sort((a, b) => {
      let aValue, bValue;
      
      switch (sortField) {
        case 'name':
          aValue = a.name;
          bValue = b.name;
          break;
        case 'manufacturer':
          aValue = a.manufacturer?.name || '';
          bValue = b.manufacturer?.name || '';
          break;
        case 'category':
          aValue = a.category?.name || '';
          bValue = b.category?.name || '';
          break;
        case 'price':
          aValue = a.price || 0;
          bValue = b.price || 0;
          break;
        case 'created_at':
          aValue = a.created_at;
          bValue = b.created_at;
          break;
        default:
          return 0;
      }
      
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortDirection === 'asc' 
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      } else {
        return sortDirection === 'asc' 
          ? (aValue as number) - (bValue as number)
          : (bValue as number) - (aValue as number);
      }
    });
    
    setFilteredProducts(filtered);
    setCurrentPage(1); // Reset to first page when filters change
  }, [products, filters, sortField, sortDirection]);

  // Pagination calculations
  const totalPages = Math.ceil(filteredProducts.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentProducts = filteredProducts.slice(startIndex, endIndex);

  // Handle sorting
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  // Handle filter changes
  const handleFilterChange = (key: keyof ProductFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  // Clear filters
  const clearFilters = () => {
    setFilters({
      manufacturer: '',
      category: '',
      hasPrice: null,
      search: ''
    });
  };

  // Statistics
  const stats = {
    total: products.length,
    filtered: filteredProducts.length,
    byManufacturer: manufacturers.map(mfr => ({
      name: mfr.name,
      count: products.filter(p => p.manufacturer?.name === mfr.name).length
    })),
    withPrices: products.filter(p => p.price !== null).length,
    withoutPrices: products.filter(p => p.price === null).length
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-neutral-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-neutral-200 rounded w-1/4 mb-6"></div>
            <div className="bg-white rounded-2xl shadow-soft p-6">
              <div className="h-4 bg-neutral-200 rounded w-1/3 mb-4"></div>
              <div className="space-y-3">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="h-4 bg-neutral-200 rounded"></div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-neutral-800">Termék Katalógus</h1>
          <button
            onClick={() => loadData(true)}
            disabled={isRefreshing}
            className="flex items-center px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50"
          >
            <IconRefresh className={cn("mr-2", isRefreshing && "animate-spin")} />
            {isRefreshing ? 'Frissítés...' : 'Frissítés'}
          </button>
        </div>

        {/* Statistics Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-white p-4 rounded-xl shadow-soft">
            <div className="text-2xl font-bold text-neutral-800">{stats.total}</div>
            <div className="text-sm text-neutral-600">Összes termék</div>
          </div>
          <div className="bg-white p-4 rounded-xl shadow-soft">
            <div className="text-2xl font-bold text-neutral-800">{stats.filtered}</div>
            <div className="text-sm text-neutral-600">Szűrt eredmény</div>
          </div>
          <div className="bg-white p-4 rounded-xl shadow-soft">
            <div className="text-2xl font-bold text-neutral-800">{stats.withPrices}</div>
            <div className="text-sm text-neutral-600">Árral rendelkező</div>
          </div>
          <div className="bg-white p-4 rounded-xl shadow-soft">
            <div className="text-2xl font-bold text-neutral-800">{manufacturers.length}</div>
            <div className="text-sm text-neutral-600">Gyártó</div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white p-6 rounded-2xl shadow-soft mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-neutral-800 flex items-center">
              <IconFilter className="mr-2" />
              Szűrők és Keresés
            </h2>
            <button
              onClick={clearFilters}
              className="text-sm text-primary-600 hover:text-primary-700"
            >
              Szűrők törlése
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {/* Search */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">
                Keresés
              </label>
              <input
                type="text"
                value={filters.search}
                onChange={(e) => handleFilterChange('search', e.target.value)}
                placeholder="Termék neve, gyártó..."
                className="w-full px-3 py-2 border border-neutral-200 rounded-lg focus:outline-none focus:border-primary-400"
              />
            </div>
            
            {/* Manufacturer */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">
                Gyártó
              </label>
              <select
                value={filters.manufacturer}
                onChange={(e) => handleFilterChange('manufacturer', e.target.value)}
                className="w-full px-3 py-2 border border-neutral-200 rounded-lg focus:outline-none focus:border-primary-400"
              >
                <option value="">Összes gyártó</option>
                {manufacturers.map(mfr => (
                  <option key={mfr.id} value={mfr.name}>
                    {mfr.name} ({stats.byManufacturer.find(s => s.name === mfr.name)?.count || 0})
                  </option>
                ))}
              </select>
            </div>
            
            {/* Category */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">
                Kategória
              </label>
              <select
                value={filters.category}
                onChange={(e) => handleFilterChange('category', e.target.value)}
                className="w-full px-3 py-2 border border-neutral-200 rounded-lg focus:outline-none focus:border-primary-400"
              >
                <option value="">Összes kategória</option>
                {categories.map(cat => (
                  <option key={cat.id} value={cat.name}>{cat.name}</option>
                ))}
              </select>
            </div>
            
            {/* Price Filter */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">
                Ár státusz
              </label>
              <select
                value={filters.hasPrice === null ? '' : filters.hasPrice.toString()}
                onChange={(e) => handleFilterChange('hasPrice', e.target.value === '' ? null : e.target.value === 'true')}
                className="w-full px-3 py-2 border border-neutral-200 rounded-lg focus:outline-none focus:border-primary-400"
              >
                <option value="">Mindegyik</option>
                <option value="true">Árral rendelkező</option>
                <option value="false">Ár nélküli</option>
              </select>
            </div>
            
            {/* Items per page */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">
                Oldalanként
              </label>
              <select
                value={itemsPerPage}
                onChange={(e) => setItemsPerPage(Number(e.target.value))}
                className="w-full px-3 py-2 border border-neutral-200 rounded-lg focus:outline-none focus:border-primary-400"
              >
                <option value={10}>10</option>
                <option value={25}>25</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
              </select>
            </div>
          </div>
        </div>

        {/* Table */}
        <div className="bg-white rounded-2xl shadow-soft overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-neutral-50 border-b border-neutral-200">
                <tr>
                  <th className="px-6 py-4 text-left">
                    <button
                      onClick={() => handleSort('name')}
                      className="flex items-center text-sm font-medium text-neutral-700 hover:text-neutral-900"
                    >
                      Termék neve
                      {sortField === 'name' && (
                        sortDirection === 'asc' ? <IconChevronUp className="ml-1" /> : <IconChevronDown className="ml-1" />
                      )}
                    </button>
                  </th>
                  <th className="px-6 py-4 text-left">
                    <button
                      onClick={() => handleSort('manufacturer')}
                      className="flex items-center text-sm font-medium text-neutral-700 hover:text-neutral-900"
                    >
                      Gyártó
                      {sortField === 'manufacturer' && (
                        sortDirection === 'asc' ? <IconChevronUp className="ml-1" /> : <IconChevronDown className="ml-1" />
                      )}
                    </button>
                  </th>
                  <th className="px-6 py-4 text-left">
                    <button
                      onClick={() => handleSort('category')}
                      className="flex items-center text-sm font-medium text-neutral-700 hover:text-neutral-900"
                    >
                      Kategória
                      {sortField === 'category' && (
                        sortDirection === 'asc' ? <IconChevronUp className="ml-1" /> : <IconChevronDown className="ml-1" />
                      )}
                    </button>
                  </th>
                  <th className="px-6 py-4 text-left">
                    <button
                      onClick={() => handleSort('price')}
                      className="flex items-center text-sm font-medium text-neutral-700 hover:text-neutral-900"
                    >
                      Ár
                      {sortField === 'price' && (
                        sortDirection === 'asc' ? <IconChevronUp className="ml-1" /> : <IconChevronDown className="ml-1" />
                      )}
                    </button>
                  </th>
                  <th className="px-6 py-4 text-left">
                    <span className="text-sm font-medium text-neutral-700">
                      Műszaki adatok
                    </span>
                  </th>
                  <th className="px-6 py-4 text-left">
                    <button
                      onClick={() => handleSort('created_at')}
                      className="flex items-center text-sm font-medium text-neutral-700 hover:text-neutral-900"
                    >
                      Létrehozva
                      {sortField === 'created_at' && (
                        sortDirection === 'asc' ? <IconChevronUp className="ml-1" /> : <IconChevronDown className="ml-1" />
                      )}
                    </button>
                  </th>
                  <th className="px-6 py-4 text-center">
                    <span className="text-sm font-medium text-neutral-700">
                      Műveletek
                    </span>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-200">
                {currentProducts.map((product) => (
                  <tr key={product.id} className="hover:bg-neutral-50">
                    <td className="px-6 py-4">
                      <div className="flex flex-col">
                        <div className="font-medium text-neutral-900 line-clamp-2">
                          {product.name}
                        </div>
                        {product.description && (
                          <div className="text-sm text-neutral-500 line-clamp-1 mt-1">
                            {product.description}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      {product.manufacturer ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
                          {product.manufacturer.name}
                        </span>
                      ) : (
                        <span className="text-sm text-neutral-400">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      {product.category ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-secondary-100 text-secondary-800">
                          {product.category.name}
                        </span>
                      ) : (
                        <span className="text-sm text-neutral-400">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      {product.price ? (
                        <span className="text-sm font-medium text-neutral-900">
                          {product.price.toLocaleString()} Ft
                        </span>
                      ) : (
                        <span className="text-sm text-neutral-400">Nincs ár</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      {product.technical_specs && Object.keys(product.technical_specs).length > 0 ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-accent-100 text-accent-800">
                          {Object.keys(product.technical_specs).length} paraméter
                        </span>
                      ) : (
                        <span className="text-sm text-neutral-400">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm text-neutral-500">
                      {new Date(product.created_at).toLocaleDateString('hu-HU')}
                    </td>
                    <td className="px-6 py-4 text-center">
                      <button
                        onClick={() => window.open(`http://localhost:8000/products/${product.id}/view`, '_blank')}
                        className="inline-flex items-center p-1 text-neutral-400 hover:text-primary-500"
                        title="Termék részletek"
                      >
                        <IconEye />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {/* Pagination */}
          {totalPages > 1 && (
            <div className="px-6 py-4 border-t border-neutral-200 flex items-center justify-between">
              <div className="text-sm text-neutral-700">
                {startIndex + 1}-{Math.min(endIndex, filteredProducts.length)} / {filteredProducts.length} termék
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                  disabled={currentPage === 1}
                  className="px-3 py-1 text-sm border border-neutral-300 rounded hover:bg-neutral-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Előző
                </button>
                <span className="text-sm text-neutral-600">
                  {currentPage} / {totalPages}
                </span>
                <button
                  onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                  disabled={currentPage === totalPages}
                  className="px-3 py-1 text-sm border border-neutral-300 rounded hover:bg-neutral-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Következő
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 