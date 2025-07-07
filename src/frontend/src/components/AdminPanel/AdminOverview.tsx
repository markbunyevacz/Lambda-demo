'use client';

import React, { useState, useEffect } from 'react';
import { api, SystemMetrics } from '@/lib/api';

// Helper function for className joining
function cn(...classes: (string | boolean | undefined)[]): string {
  return classes.filter(Boolean).join(' ');
}

// Icons
const IconTrendingUp = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
  </svg>
);

const IconUsers = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
  </svg>
);

const IconDocumentText = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
);

const IconDatabase = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
  </svg>
);

const IconClock = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const IconCheckCircle = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const IconRefresh = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
  </svg>
);

interface QuickStats {
  totalProducts: number;
  totalManufacturers: number;
  totalCategories: number;
  systemHealth: 'healthy' | 'warning' | 'error';
  apiResponseTime: number;
  searchAccuracy: number;
  lastUpdated: string;
}

export default function AdminOverview() {
  const [stats, setStats] = useState<QuickStats | null>(null);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = async (isRefresh = false) => {
    if (isRefresh) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }
    setError(null);

    try {
      // Load system metrics which contains all needed data
      const systemMetrics = await api.getSystemMetrics();
      setMetrics(systemMetrics);

      // Extract quick stats from metrics
      const quickStats: QuickStats = {
        totalProducts: systemMetrics.database.data.products,
        totalManufacturers: systemMetrics.database.data.manufacturers,
        totalCategories: systemMetrics.database.data.categories,
        systemHealth: systemMetrics.health.status === 'healthy' ? 'healthy' : 'error',
        apiResponseTime: systemMetrics.performance.api_response_time || 0,
        searchAccuracy: (systemMetrics.performance.search_accuracy || 0) * 100,
        lastUpdated: new Date().toISOString()
      };
      setStats(quickStats);
    } catch (err) {
      console.error('Failed to load admin overview data:', err);
      setError(err instanceof Error ? err.message : 'Ismeretlen hiba történt');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-white p-6 rounded-xl shadow-sm border">
                <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
                <div className="h-8 bg-gray-200 rounded w-3/4"></div>
              </div>
            ))}
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
          <h2 className="text-2xl font-bold text-gray-800">Admin Áttekintés</h2>
          <p className="text-gray-600 mt-1">Lambda.hu rendszer statisztikák és állapot</p>
        </div>
        <button
          onClick={() => loadData(true)}
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
          <span>Hiba az adatok betöltésében: {error}</span>
        </div>
      )}

      {/* Quick Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-6 rounded-xl shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Összes Termék</p>
                <p className="text-3xl font-bold text-gray-900">{stats.totalProducts}</p>
                <p className="text-xs text-green-600 flex items-center mt-1">
                  <IconCheckCircle className="w-3 h-3 mr-1" />
                  Aktív
                </p>
              </div>
              <div className="p-3 bg-blue-100 rounded-full">
                <IconDocumentText className="text-blue-600" />
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Gyártók</p>
                <p className="text-3xl font-bold text-gray-900">{stats.totalManufacturers}</p>
                <p className="text-xs text-green-600 flex items-center mt-1">
                  <IconTrendingUp className="w-3 h-3 mr-1" />
                  Teljes
                </p>
              </div>
              <div className="p-3 bg-green-100 rounded-full">
                <IconUsers className="text-green-600" />
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Kategóriák</p>
                <p className="text-3xl font-bold text-gray-900">{stats.totalCategories}</p>
                <p className="text-xs text-blue-600 flex items-center mt-1">
                  <IconDatabase className="w-3 h-3 mr-1" />
                  Hierarchikus
                </p>
              </div>
              <div className="p-3 bg-purple-100 rounded-full">
                <IconDatabase className="text-purple-600" />
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">API Válaszidő</p>
                <p className="text-3xl font-bold text-gray-900">{stats.apiResponseTime}ms</p>
                <p className={cn(
                  "text-xs flex items-center mt-1",
                  stats.apiResponseTime < 1000 ? "text-green-600" : "text-yellow-600"
                )}>
                  <IconClock className="w-3 h-3 mr-1" />
                  {stats.apiResponseTime < 1000 ? 'Gyors' : 'Lassú'}
                </p>
              </div>
              <div className={cn(
                "p-3 rounded-full",
                stats.apiResponseTime < 1000 ? "bg-green-100" : "bg-yellow-100"
              )}>
                <IconClock className={cn(
                  stats.apiResponseTime < 1000 ? "text-green-600" : "text-yellow-600"
                )} />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Detailed Information */}
      {metrics && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* System Status */}
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Rendszer Állapot</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="font-medium">API Szerver</span>
                <span className={cn(
                  "px-3 py-1 rounded-full text-sm font-medium",
                  metrics.health.status === 'healthy' ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                )}>
                  {metrics.health.status === 'healthy' ? 'Elérhető' : 'Hiba'}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="font-medium">PostgreSQL</span>
                <span className={cn(
                  "px-3 py-1 rounded-full text-sm font-medium",
                  metrics.database.data.database_status === 'connected' ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                )}>
                  {metrics.database.data.database_status === 'connected' ? 'Kapcsolódva' : 'Szétkapcsolódva'}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="font-medium">ChromaDB</span>
                <span className={cn(
                  "px-3 py-1 rounded-full text-sm font-medium",
                  metrics.database.data.products > 0 ? "bg-green-100 text-green-800" : "bg-yellow-100 text-yellow-800"
                )}>
                  {metrics.database.data.products > 0 ? 'Működik' : 'Nincs adat'}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="font-medium">RAG Keresés</span>
                <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                  {stats?.searchAccuracy.toFixed(1)}% pontosság
                </span>
              </div>
            </div>
          </div>

          {/* Manufacturer Distribution */}
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Gyártó Megoszlás</h3>
            <div className="space-y-3">
              {metrics.database.data.products_by_manufacturer.map((item, index) => {
                const maxCount = Math.max(...metrics.database.data.products_by_manufacturer.map(m => m.count));
                const percentage = (item.count / maxCount) * 100;
                
                return (
                  <div key={index} className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="font-medium text-gray-700">{item.manufacturer}</span>
                      <span className="text-sm text-gray-600">{item.count} termék</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Performance Metrics */}
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Teljesítmény Metrikák</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <p className="text-2xl font-bold text-blue-600">{metrics.performance.api_response_time}ms</p>
                <p className="text-sm text-gray-600">API Válaszidő</p>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <p className="text-2xl font-bold text-green-600">{stats?.searchAccuracy.toFixed(1)}%</p>
                <p className="text-sm text-gray-600">Keresési Pontosság</p>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <p className="text-2xl font-bold text-purple-600">{metrics.performance.active_connections}</p>
                <p className="text-sm text-gray-600">Aktív Kapcsolatok</p>
              </div>
              <div className="text-center p-4 bg-orange-50 rounded-lg">
                <p className="text-2xl font-bold text-orange-600">{metrics.performance.uptime}</p>
                <p className="text-sm text-gray-600">Üzemidő</p>
              </div>
            </div>
          </div>

          {/* Resource Usage */}
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Erőforrás Használat</h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">CPU Használat</span>
                  <span className="text-sm text-gray-600">{metrics.resources.cpu_usage}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className={cn(
                      "h-2 rounded-full transition-all duration-300",
                      metrics.resources.cpu_usage && metrics.resources.cpu_usage > 80 ? "bg-red-500" : 
                      metrics.resources.cpu_usage && metrics.resources.cpu_usage > 60 ? "bg-yellow-500" : "bg-green-500"
                    )}
                    style={{ width: `${metrics.resources.cpu_usage}%` }}
                  />
                </div>
              </div>
              
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Memória</span>
                  <span className="text-sm text-gray-600">{metrics.resources.memory_usage} MB</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${Math.min((metrics.resources.memory_usage || 0) / 20, 100)}%` }}
                  />
                </div>
              </div>
              
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Lemez Használat</span>
                  <span className="text-sm text-gray-600">{metrics.resources.disk_space}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className={cn(
                      "h-2 rounded-full transition-all duration-300",
                      metrics.resources.disk_space && metrics.resources.disk_space > 85 ? "bg-red-500" : "bg-green-500"
                    )}
                    style={{ width: `${metrics.resources.disk_space}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Last Updated */}
      {stats && (
        <div className="text-center text-sm text-gray-500">
          Utolsó frissítés: {new Date(stats.lastUpdated).toLocaleString('hu-HU')}
        </div>
      )}
    </div>
  );
} 