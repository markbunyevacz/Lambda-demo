'use client';

import { useState, useEffect } from 'react';
import { api, SystemMetrics } from '@/lib/api';

// Helper function for className joining
function cn(...classes: (string | boolean | undefined)[]): string {
  return classes.filter(Boolean).join(' ');
}

// Icons remain the same...
const IconSearch = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
  </svg>
);

const IconShield = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
  </svg>
);

const IconHome = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 21l8-8-8-8" />
  </svg>
);

const IconBuild = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
  </svg>
);

const IconColorSwatch = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zM7 21h10a2 2 0 002-2v-4a2 2 0 00-2-2H7M7 21V9a2 2 0 012-2h10a2 2 0 012 2v4M7 9V5a2 2 0 012-2h4a2 2 0 012 2v4M7 9h10" />
  </svg>
);

interface DashboardProps {
  onSearchSubmit?: (query: string) => void;
  onCategorySelect?: (category: string) => void;
}

interface DashboardStats {
  productCount: number;
  manufacturerCount: number;
  categoryCount: number;
  lastUpdated: string;
  apiResponseTime: number;
  searchAccuracy: number;
  isLoading: boolean;
  error?: string;
}

interface QuickAccessModule {
  id: string;
  title: string;
  description: string;
  icon: React.ComponentType;
  color: string;
  count: string;
}

export default function Dashboard({ onSearchSubmit, onCategorySelect }: DashboardProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const [stats, setStats] = useState<DashboardStats>({
    productCount: 0,
    manufacturerCount: 0,
    categoryCount: 0,
    lastUpdated: 'Betöltés...',
    apiResponseTime: 0,
    searchAccuracy: 0,
    isLoading: true,
  });

  // Load real system metrics efficiently
  useEffect(() => {
    const loadSystemStats = async () => {
      try {
        // Use the optimized system metrics API that combines all data
        const metrics: SystemMetrics = await api.getSystemMetrics();

        setStats({
          productCount: metrics.database.data.products,
          manufacturerCount: metrics.database.data.manufacturers,
          categoryCount: metrics.database.data.categories,
          lastUpdated: new Date(metrics.database.data.last_updated).toLocaleDateString('hu-HU', {
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
          }),
          apiResponseTime: metrics.performance.api_response_time || 0,
          searchAccuracy: (metrics.performance.search_accuracy || 0) * 100,
          isLoading: false,
        });
      } catch (error) {
        console.error('Failed to load system stats:', error);
        setStats(prev => ({
          ...prev,
          lastUpdated: 'Hiba a betöltésben',
          isLoading: false,
          error: error instanceof Error ? error.message : 'Ismeretlen hiba',
        }));
      }
    };

    loadSystemStats();
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim() && onSearchSubmit) {
      onSearchSubmit(searchQuery.trim());
    }
  };

  const sampleQueries = [
    "Milyen hőszigetelés kell családi házhoz?",
    "10 cm vastag homlokzati szigetelés",
    "ROCKWOOL termékek tető alá",
    "Leier falazóelemek árak"
  ];

  // Dynamic quick access modules based on real data
  const getQuickAccessModules = (): QuickAccessModule[] => {
    const totalProducts = stats.productCount;
    
    return [
      {
        id: 'insulation',
        title: 'Hőszigetelés',
        description: 'Homlokzati és tetőszigetelési megoldások',
        icon: IconShield,
        color: 'bg-primary-500',
        count: `~${Math.floor(totalProducts * 0.4)} termék`,
      },
      {
        id: 'masonry',
        title: 'Falazóelemek',
        description: 'Téglák, blokkok és falazórendszerek',
        icon: IconHome,
        color: 'bg-secondary-500',
        count: `~${Math.floor(totalProducts * 0.25)} termék`,
      },
      {
        id: 'facade',
        title: 'Homlokzati rendszerek',
        description: 'HŐSZ rendszerek és homlokzatfestékek',
        icon: IconBuild,
        color: 'bg-accent-500',
        count: `~${Math.floor(totalProducts * 0.35)} termék`,
      },
      {
        id: 'colors',
        title: 'Színrendszerek',
        description: 'Festékek és színes vakolatok',
        icon: IconColorSwatch,
        color: 'bg-purple-500',
        count: `${stats.categoryCount} kategória`,
      },
    ];
  };

  const getSystemStatsDisplay = () => [
    { 
      label: 'Termékek száma', 
      value: stats.isLoading ? '...' : stats.productCount.toString(), 
      change: stats.isLoading ? 'Betöltés...' : `${stats.manufacturerCount} gyártótól`
    },
    { 
      label: 'Gyártók', 
      value: stats.isLoading ? '...' : stats.manufacturerCount.toString(), 
      change: 'ROCKWOOL, Leier, Baumit' 
    },
    { 
      label: 'Adatbázis frissítve', 
      value: stats.lastUpdated, 
      change: 'Automatikus szinkronizálás' 
    },
    { 
      label: 'AI válaszidő', 
      value: stats.isLoading ? '...' : `${stats.apiResponseTime}ms`, 
      change: `${stats.searchAccuracy.toFixed(1)}% pontosság` 
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 to-neutral-100">
      {/* Hero szekció központi keresővel */}
      <div className="pt-12 pb-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl sm:text-5xl font-bold text-neutral-800 mb-4">
            Magyar Építőanyag
            <span className="block text-primary-500">AI Asszisztens</span>
          </h1>
          <p className="text-xl text-neutral-600 mb-12 max-w-2xl mx-auto">
            Természetes nyelven kérdezhetsz építőanyagokról. Az AI szakértő válaszokat ad 
            és konkrét termékeket ajánl a {stats.isLoading ? '...' : stats.productCount} terméket tartalmazó adatbázisból.
          </p>

          {/* Error State */}
          {stats.error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6 max-w-md mx-auto">
              <span className="text-sm">Rendszerstatisztikák nem elérhetők</span>
            </div>
          )}

          {/* Központi keresősáv */}
          <form onSubmit={handleSearchSubmit} className="relative mb-8">
            <div className={cn(
              "relative max-w-2xl mx-auto transition-all duration-300",
              isSearchFocused ? "scale-105" : ""
            )}>
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <IconSearch />
              </div>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onFocus={() => setIsSearchFocused(true)}
                onBlur={() => setIsSearchFocused(false)}
                placeholder="Kérdezz az AI-tól: pl. 'Milyen szigetelés kell családi házhoz?'"
                className={cn(
                  "block w-full pl-12 pr-4 py-4 text-lg border-2 rounded-2xl",
                  "focus:outline-none focus:ring-0 transition-all duration-300",
                  "placeholder-neutral-400 bg-white shadow-medium",
                  isSearchFocused 
                    ? "border-primary-400 shadow-strong" 
                    : "border-neutral-200 hover:border-neutral-300"
                )}
              />
              <button
                type="submit"
                disabled={!searchQuery.trim()}
                className={cn(
                  "absolute inset-y-0 right-0 flex items-center px-6",
                  "bg-primary-500 text-white rounded-r-2xl transition-all duration-300",
                  "hover:bg-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-400 focus:ring-offset-2",
                  "disabled:opacity-50 disabled:cursor-not-allowed",
                  searchQuery.trim() ? "opacity-100" : "opacity-70"
                )}
              >
                Kérdezz
              </button>
            </div>
          </form>

          {/* Minta kérdések */}
          <div className="flex flex-wrap justify-center gap-2 mb-12">
            <span className="text-sm text-neutral-500 mr-2">Példa kérdések:</span>
            {sampleQueries.map((query, index) => (
              <button
                key={index}
                onClick={() => setSearchQuery(query)}
                className="text-sm text-primary-600 hover:text-primary-700 bg-primary-50 hover:bg-primary-100 px-3 py-1 rounded-full transition-colors duration-200"
              >
                {query}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Gyors elérési modulok */}
      <div className="px-4 sm:px-6 lg:px-8 pb-12">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-2xl font-bold text-neutral-800 mb-8 text-center">
            Gyors hozzáférés kategóriákhoz
          </h2>
          
          {stats.isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {[...Array(4)].map((_, index) => (
                <div key={index} className="animate-pulse">
                  <div className="p-6 bg-white rounded-2xl shadow-soft border border-neutral-100">
                    <div className="w-12 h-12 bg-gray-200 rounded-xl mb-4"></div>
                    <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                    <div className="h-3 bg-gray-200 rounded w-full mb-3"></div>
                    <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {getQuickAccessModules().map((module) => {
                const Icon = module.icon;
                return (
                  <button
                    key={module.id}
                    onClick={() => onCategorySelect?.(module.id)}
                    className="group p-6 bg-white rounded-2xl shadow-soft hover:shadow-medium transition-all duration-300 hover:-translate-y-1 border border-neutral-100"
                  >
                    <div className={cn(
                      "w-12 h-12 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300 text-white",
                      module.color
                    )}>
                      <Icon />
                    </div>
                    <h3 className="text-lg font-semibold text-neutral-800 mb-2">
                      {module.title}
                    </h3>
                    <p className="text-sm text-neutral-600 mb-3">
                      {module.description}
                    </p>
                    <div className="text-xs text-primary-600 font-medium">
                      {module.count}
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Élő statisztikai widget-ek */}
      <div className="px-4 sm:px-6 lg:px-8 pb-16">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {getSystemStatsDisplay().map((stat, index) => (
              <div
                key={index}
                className="bg-white p-4 rounded-xl shadow-soft border border-neutral-100"
              >
                <div className="text-2xl font-bold text-neutral-800 mb-1">
                  {stat.value}
                </div>
                <div className="text-sm text-neutral-600 mb-1">
                  {stat.label}
                </div>
                <div className="text-xs text-accent-600">
                  {stat.change}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
} 