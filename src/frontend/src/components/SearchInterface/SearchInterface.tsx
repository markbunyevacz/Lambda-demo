'use client';

import { useState, useEffect } from 'react';
import { api, Product, Manufacturer, Category, SearchResult } from '@/lib/api';

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

const IconFilter = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.207A1 1 0 013 6.5V4z" />
  </svg>
);

const IconX = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
  </svg>
);

const IconHeart = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
  </svg>
);

const IconEye = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
  </svg>
);

interface SearchFilters {
  manufacturers: string[];
  categories: string[];
  priceRange: { min: number | null; max: number | null };
  sortBy: 'relevance' | 'price_asc' | 'price_desc' | 'name_asc' | 'name_desc';
}

interface SearchInterfaceProps {
  onProductSelect?: (product: Product) => void;
}

export default function SearchInterface({ onProductSelect }: SearchInterfaceProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [totalResults, setTotalResults] = useState(0);
  const [isFiltersOpen, setIsFiltersOpen] = useState(true);
  
  // Filter state
  const [filters, setFilters] = useState<SearchFilters>({
    manufacturers: [],
    categories: [],
    priceRange: { min: null, max: null },
    sortBy: 'relevance'
  });
  
  // Filter options from API
  const [manufacturers, setManufacturers] = useState<Manufacturer[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [isLoadingFilters, setIsLoadingFilters] = useState(true);

  // Load filter options
  useEffect(() => {
    const loadFilterOptions = async () => {
      try {
        const [mfrs, cats] = await Promise.all([
          api.getManufacturers(),
          api.getCategories()
        ]);
        setManufacturers(mfrs);
        setCategories(cats);
      } catch (error) {
        console.error('Failed to load filter options:', error);
      } finally {
        setIsLoadingFilters(false);
      }
    };
    
    loadFilterOptions();
  }, []);

  // Search function
  const handleSearch = async (query: string = searchQuery) => {
    if (!query.trim()) {
      setSearchResults([]);
      setTotalResults(0);
      return;
    }

    setIsLoading(true);
    try {
      const response = await api.searchRAG(query, 20);
      
      // Apply filters to results
      let filteredResults = response.results;
      
      // Filter by manufacturers
      if (filters.manufacturers.length > 0) {
        filteredResults = filteredResults.filter(result => 
          filters.manufacturers.some(mfr => 
            result.metadata.manufacturer?.toLowerCase().includes(mfr.toLowerCase())
          )
        );
      }
      
      // Filter by categories
      if (filters.categories.length > 0) {
        filteredResults = filteredResults.filter(result => 
          filters.categories.some(cat => 
            result.category.toLowerCase().includes(cat.toLowerCase())
          )
        );
      }
      
      // Sort results
      if (filters.sortBy === 'name_asc') {
        filteredResults.sort((a, b) => a.name.localeCompare(b.name));
      } else if (filters.sortBy === 'name_desc') {
        filteredResults.sort((a, b) => b.name.localeCompare(a.name));
      } else if (filters.sortBy === 'price_asc') {
        filteredResults.sort((a, b) => (a.metadata.price || 0) - (b.metadata.price || 0));
      } else if (filters.sortBy === 'price_desc') {
        filteredResults.sort((a, b) => (b.metadata.price || 0) - (a.metadata.price || 0));
      }
      // 'relevance' is default order from API
      
      setSearchResults(filteredResults);
      setTotalResults(filteredResults.length);
    } catch (error) {
      console.error('Search failed:', error);
      setSearchResults([]);
      setTotalResults(0);
    } finally {
      setIsLoading(false);
    }
  };

  // Filter handlers
  const handleManufacturerFilter = (manufacturer: string) => {
    setFilters(prev => ({
      ...prev,
      manufacturers: prev.manufacturers.includes(manufacturer)
        ? prev.manufacturers.filter(m => m !== manufacturer)
        : [...prev.manufacturers, manufacturer]
    }));
  };

  const handleCategoryFilter = (category: string) => {
    setFilters(prev => ({
      ...prev,
      categories: prev.categories.includes(category)
        ? prev.categories.filter(c => c !== category)
        : [...prev.categories, category]
    }));
  };

  const handleSortChange = (sortBy: SearchFilters['sortBy']) => {
    setFilters(prev => ({ ...prev, sortBy }));
  };

  const clearFilters = () => {
    setFilters({
      manufacturers: [],
      categories: [],
      priceRange: { min: null, max: null },
      sortBy: 'relevance'
    });
  };

  // Re-search when filters change
  useEffect(() => {
    if (searchQuery.trim()) {
      handleSearch();
    }
  }, [filters]);

  return (
    <div className="min-h-screen bg-neutral-50 flex">
      {/* Sidebar Filters */}
      <div className={cn(
        "w-80 bg-white border-r border-neutral-200 p-6 transition-all duration-300",
        isFiltersOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-neutral-800 flex items-center">
            <IconFilter className="mr-2" />
            Szűrők
          </h2>
          <button
            onClick={() => setIsFiltersOpen(false)}
            className="p-1 text-neutral-400 hover:text-neutral-600 lg:hidden"
          >
            <IconX />
          </button>
        </div>

        {/* Clear Filters */}
        <button
          onClick={clearFilters}
          className="w-full text-sm text-primary-600 hover:text-primary-700 mb-6 text-left"
        >
          Összes szűrő törlése
        </button>

        {/* Sort Options */}
        <div className="mb-6">
          <h3 className="text-sm font-medium text-neutral-700 mb-3">Rendezés</h3>
          <select
            value={filters.sortBy}
            onChange={(e) => handleSortChange(e.target.value as SearchFilters['sortBy'])}
            className="w-full px-3 py-2 border border-neutral-200 rounded-lg focus:outline-none focus:border-primary-400"
          >
            <option value="relevance">Relevancia</option>
            <option value="name_asc">Név (A-Z)</option>
            <option value="name_desc">Név (Z-A)</option>
            <option value="price_asc">Ár (alacsony-magas)</option>
            <option value="price_desc">Ár (magas-alacsony)</option>
          </select>
        </div>

        {/* Manufacturers Filter */}
        <div className="mb-6">
          <h3 className="text-sm font-medium text-neutral-700 mb-3">Gyártók</h3>
          {isLoadingFilters ? (
            <div className="text-sm text-neutral-500">Betöltés...</div>
          ) : (
            <div className="space-y-2">
              {manufacturers.map(manufacturer => (
                <label key={manufacturer.id} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={filters.manufacturers.includes(manufacturer.name)}
                    onChange={() => handleManufacturerFilter(manufacturer.name)}
                    className="mr-2 text-primary-600 focus:ring-primary-400"
                  />
                  <span className="text-sm text-neutral-700">{manufacturer.name}</span>
                </label>
              ))}
            </div>
          )}
        </div>

        {/* Categories Filter */}
        <div className="mb-6">
          <h3 className="text-sm font-medium text-neutral-700 mb-3">Kategóriák</h3>
          {isLoadingFilters ? (
            <div className="text-sm text-neutral-500">Betöltés...</div>
          ) : (
            <div className="space-y-2">
              {categories.map(category => (
                <label key={category.id} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={filters.categories.includes(category.name)}
                    onChange={() => handleCategoryFilter(category.name)}
                    className="mr-2 text-primary-600 focus:ring-primary-400"
                  />
                  <span className="text-sm text-neutral-700">{category.name}</span>
                </label>
              ))}
            </div>
          )}
        </div>

        {/* Active Filters */}
        {(filters.manufacturers.length > 0 || filters.categories.length > 0) && (
          <div className="border-t border-neutral-200 pt-4">
            <h3 className="text-sm font-medium text-neutral-700 mb-3">Aktív szűrők</h3>
            <div className="space-y-1">
              {filters.manufacturers.map(mfr => (
                <div key={mfr} className="flex items-center justify-between bg-primary-50 px-2 py-1 rounded text-sm">
                  <span className="text-primary-700">{mfr}</span>
                  <button
                    onClick={() => handleManufacturerFilter(mfr)}
                    className="text-primary-600 hover:text-primary-700"
                  >
                    <IconX />
                  </button>
                </div>
              ))}
              {filters.categories.map(cat => (
                <div key={cat} className="flex items-center justify-between bg-secondary-50 px-2 py-1 rounded text-sm">
                  <span className="text-secondary-700">{cat}</span>
                  <button
                    onClick={() => handleCategoryFilter(cat)}
                    className="text-secondary-600 hover:text-secondary-700"
                  >
                    <IconX />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 p-6">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <h1 className="text-3xl font-bold text-neutral-800">Intelligens Keresés</h1>
              {!isFiltersOpen && (
                <button
                  onClick={() => setIsFiltersOpen(true)}
                  className="lg:hidden px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 flex items-center"
                >
                  <IconFilter className="mr-2" />
                  Szűrők
                </button>
              )}
            </div>
            
            {/* Search Bar */}
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <IconSearch className="text-neutral-400" />
              </div>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Természetes nyelvű keresés: pl. 'hőszigetelés családi házhoz'"
                className="w-full pl-12 pr-4 py-4 text-lg border-2 border-neutral-200 rounded-2xl focus:outline-none focus:border-primary-400 bg-white shadow-sm"
              />
              <button
                onClick={() => handleSearch()}
                disabled={isLoading}
                className="absolute inset-y-0 right-0 px-8 bg-primary-500 text-white rounded-r-2xl hover:bg-primary-600 disabled:opacity-50"
              >
                {isLoading ? 'Keresés...' : 'Keresés'}
              </button>
            </div>
          </div>

          {/* Results Header */}
          {searchQuery && (
            <div className="mb-6 flex items-center justify-between">
              <div className="text-sm text-neutral-600">
                {isLoading ? 'Keresés...' : `${totalResults} találat "${searchQuery}" keresésre`}
              </div>
              <div className="text-sm text-neutral-500">
                {filters.sortBy === 'relevance' ? 'Relevancia szerint rendezve' : 'Egyedi rendezés'}
              </div>
            </div>
          )}

          {/* Results Grid */}
          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="bg-white rounded-2xl p-6 shadow-soft animate-pulse">
                  <div className="h-4 bg-neutral-200 rounded mb-3"></div>
                  <div className="h-3 bg-neutral-200 rounded mb-2"></div>
                  <div className="h-3 bg-neutral-200 rounded w-2/3"></div>
                </div>
              ))}
            </div>
          ) : searchResults.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {searchResults.map((result, index) => (
                <div key={index} className="bg-white rounded-2xl p-6 shadow-soft hover:shadow-medium transition-all duration-300 border border-neutral-100">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-neutral-800 mb-2 line-clamp-2">
                        {result.name}
                      </h3>
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="text-sm bg-primary-100 text-primary-700 px-2 py-1 rounded">
                          {result.category}
                        </span>
                        {result.metadata.manufacturer && (
                          <span className="text-sm bg-secondary-100 text-secondary-700 px-2 py-1 rounded">
                            {result.metadata.manufacturer}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-1">
                      <button className="p-2 text-neutral-400 hover:text-accent-500">
                        <IconHeart />
                      </button>
                      <button className="p-2 text-neutral-400 hover:text-primary-500">
                        <IconEye />
                      </button>
                    </div>
                  </div>
                  
                  <p className="text-sm text-neutral-600 mb-4 line-clamp-3">
                    {result.description}
                  </p>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="text-sm bg-accent-100 text-accent-700 px-2 py-1 rounded">
                        {Math.round(result.similarity_score * 100)}% egyezés
                      </span>
                      {result.metadata.price && (
                        <span className="text-sm font-medium text-neutral-700">
                          {result.metadata.price.toLocaleString()} Ft
                        </span>
                      )}
                    </div>
                    <button
                      onClick={() => window.open(`http://localhost:8000/products/${result.metadata.product_id}/view`, '_blank')}
                      className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                    >
                      Részletek →
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : searchQuery ? (
            <div className="text-center py-12">
              <div className="text-neutral-500 mb-4">
                Nincs találat a keresett kifejezésre: <strong>"{searchQuery}"</strong>
              </div>
              <p className="text-sm text-neutral-400 mb-6">
                Próbálj meg más kulcsszavakat vagy módosítsd a szűrőket
              </p>
              <button
                onClick={clearFilters}
                className="text-primary-600 hover:text-primary-700 text-sm"
              >
                Szűrők törlése
              </button>
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="text-neutral-500 mb-4">
                Írj be egy keresési kifejezést a termékek megtalálásához
              </div>
              <p className="text-sm text-neutral-400">
                Például: "hőszigetelés", "ROCKWOOL", "homlokzati rendszer"
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 