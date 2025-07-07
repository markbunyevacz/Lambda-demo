'use client';

import { useState, useEffect } from 'react';
import { api, SystemMetrics } from '@/lib/api';

// Helper function for className joining
function cn(...classes: (string | boolean | undefined)[]): string {
  return classes.filter(Boolean).join(' ');
}

// Icons
const IconRefresh = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
  </svg>
);

const IconServer = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2" />
  </svg>
);

const IconDatabase = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
  </svg>
);

const IconChart = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 00-2-2z" />
  </svg>
);

const IconCpu = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
  </svg>
);

const IconCheckCircle = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const IconXCircle = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const IconWarning = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-1.732-.833-2.464 0L4.35 16.5c-.77.833.192 2.5 1.732 2.5z" />
  </svg>
);

export default function MonitoringDashboard() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Load system metrics
  const loadMetrics = async (isRefresh = false) => {
    if (isRefresh) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }
    setError(null);

    try {
      const systemMetrics = await api.getSystemMetrics();
      setMetrics(systemMetrics);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Failed to load system metrics:', err);
      setError(err instanceof Error ? err.message : 'Ismeretlen hiba történt');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  // Initial load
  useEffect(() => {
    loadMetrics();
  }, []);

  // Status indicator component
  const StatusIndicator = ({ status, label }: { status: 'healthy' | 'unhealthy' | 'warning' | 'unknown', label: string }) => {
    const getStatusStyles = () => {
      switch (status) {
        case 'healthy':
          return { icon: IconCheckCircle, color: 'text-green-500', bg: 'bg-green-100' };
        case 'unhealthy':
          return { icon: IconXCircle, color: 'text-red-500', bg: 'bg-red-100' };
        case 'warning':
          return { icon: IconWarning, color: 'text-yellow-500', bg: 'bg-yellow-100' };
        default:
          return { icon: IconWarning, color: 'text-gray-500', bg: 'bg-gray-100' };
      }
    };

    const { icon: Icon, color, bg } = getStatusStyles();

    return (
      <div className="flex items-center space-x-2">
        <div className={cn("p-1 rounded-full", bg)}>
          <Icon className={cn("w-4 h-4", color)} />
        </div>
        <span className="text-sm text-neutral-700">{label}</span>
      </div>
    );
  };

  // Progress bar component
  const ProgressBar = ({ value, max = 100, className = "", color = "bg-primary-500" }: { 
    value: number; 
    max?: number; 
    className?: string; 
    color?: string;
  }) => {
    const percentage = Math.min((value / max) * 100, 100);
    
    return (
      <div className={cn("w-full bg-neutral-200 rounded-full h-2", className)}>
        <div 
          className={cn("h-2 rounded-full transition-all duration-300", color)}
          style={{ width: `${percentage}%` }}
        />
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-neutral-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-neutral-200 rounded w-1/3 mb-6"></div>
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-4 gap-6 mb-6">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="bg-white p-6 rounded-2xl shadow-soft">
                  <div className="h-4 bg-neutral-200 rounded w-1/2 mb-4"></div>
                  <div className="h-8 bg-neutral-200 rounded w-3/4"></div>
                </div>
              ))}
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
          <div>
            <h1 className="text-3xl font-bold text-neutral-800">Rendszer Monitoring</h1>
            {lastUpdated && (
              <p className="text-sm text-neutral-600 mt-1">
                Utolsó frissítés: {lastUpdated.toLocaleString('hu-HU')}
              </p>
            )}
          </div>
          <button
            onClick={() => loadMetrics(true)}
            disabled={isRefreshing}
            className="flex items-center px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 transition-colors"
          >
            <IconRefresh className={cn("mr-2", isRefreshing && "animate-spin")} />
            {isRefreshing ? 'Frissítés...' : 'Frissítés'}
          </button>
        </div>

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            <div className="flex items-center">
              <IconXCircle className="mr-2" />
              <span>Hiba a monitoring adatok betöltésében: {error}</span>
            </div>
          </div>
        )}

        {/* System Status Overview */}
        {metrics && (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-4 gap-6 mb-6">
            {/* Health Status */}
            <div className="bg-white p-6 rounded-2xl shadow-soft">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-neutral-800 flex items-center">
                  <IconServer className="mr-2 text-primary-500" />
                  Rendszer Állapot
                </h3>
              </div>
              <div className="space-y-3">
                <StatusIndicator 
                  status={metrics.health.status === 'healthy' ? 'healthy' : 'unhealthy'} 
                  label={`API: ${metrics.health.status}`}
                />
                <StatusIndicator 
                  status={metrics.database.data.database_status === 'connected' ? 'healthy' : 'unhealthy'} 
                  label={`PostgreSQL: ${metrics.database.data.database_status}`}
                />
                <StatusIndicator 
                  status={metrics.database.data.products > 0 ? 'healthy' : 'warning'} 
                  label={`ChromaDB: ${metrics.database.data.products > 0 ? 'Elérhető' : 'Nincs adat'}`}
                />
              </div>
            </div>

            {/* Performance Metrics */}
            <div className="bg-white p-6 rounded-2xl shadow-soft">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-neutral-800 flex items-center">
                  <IconChart className="mr-2 text-secondary-500" />
                  Teljesítmény
                </h3>
              </div>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-neutral-600">API válaszidő</span>
                    <span className="font-medium">{metrics.performance.api_response_time}ms</span>
                  </div>
                  <ProgressBar 
                    value={metrics.performance.api_response_time || 0} 
                    max={2000} 
                    color={metrics.performance.api_response_time && metrics.performance.api_response_time < 1000 ? "bg-green-500" : "bg-yellow-500"}
                  />
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-neutral-600">RAG pontosság</span>
                    <span className="font-medium">{((metrics.performance.search_accuracy || 0) * 100).toFixed(1)}%</span>
                  </div>
                  <ProgressBar 
                    value={(metrics.performance.search_accuracy || 0) * 100} 
                    color="bg-accent-500"
                  />
                </div>
                <div className="text-sm">
                  <span className="text-neutral-600">Aktív kapcsolatok: </span>
                  <span className="font-medium">{metrics.performance.active_connections || 0}</span>
                </div>
                <div className="text-sm">
                  <span className="text-neutral-600">Üzemidő: </span>
                  <span className="font-medium">{metrics.performance.uptime || 'Ismeretlen'}</span>
                </div>
              </div>
            </div>

            {/* Database Statistics */}
            <div className="bg-white p-6 rounded-2xl shadow-soft">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-neutral-800 flex items-center">
                  <IconDatabase className="mr-2 text-accent-500" />
                  Adatbázis
                </h3>
              </div>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-neutral-600">Termékek</span>
                  <span className="font-bold text-2xl text-accent-600">{metrics.database.data.products}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-600">Gyártók</span>
                  <span className="font-medium">{metrics.database.data.manufacturers}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-600">Kategóriák</span>
                  <span className="font-medium">{metrics.database.data.categories}</span>
                </div>
                <div className="text-xs text-neutral-500 mt-2">
                  Utolsó frissítés: {new Date(metrics.database.data.last_updated).toLocaleString('hu-HU')}
                </div>
              </div>
            </div>

            {/* System Resources */}
            <div className="bg-white p-6 rounded-2xl shadow-soft">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-neutral-800 flex items-center">
                  <IconCpu className="mr-2 text-purple-500" />
                  Erőforrások
                </h3>
              </div>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-neutral-600">CPU használat</span>
                    <span className="font-medium">{metrics.resources.cpu_usage || 0}%</span>
                  </div>
                  <ProgressBar 
                    value={metrics.resources.cpu_usage || 0} 
                    color={metrics.resources.cpu_usage && metrics.resources.cpu_usage > 80 ? "bg-red-500" : metrics.resources.cpu_usage && metrics.resources.cpu_usage > 60 ? "bg-yellow-500" : "bg-green-500"}
                  />
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-neutral-600">Memória</span>
                    <span className="font-medium">{metrics.resources.memory_usage || 0} MB</span>
                  </div>
                  <ProgressBar 
                    value={metrics.resources.memory_usage || 0} 
                    max={2000} 
                    color={metrics.resources.memory_usage && metrics.resources.memory_usage > 1500 ? "bg-red-500" : "bg-blue-500"}
                  />
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-neutral-600">Lemez</span>
                    <span className="font-medium">{metrics.resources.disk_space || 0}%</span>
                  </div>
                  <ProgressBar 
                    value={metrics.resources.disk_space || 0} 
                    color={metrics.resources.disk_space && metrics.resources.disk_space > 85 ? "bg-red-500" : "bg-green-500"}
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Detailed Information */}
        {metrics && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Manufacturer Breakdown */}
            <div className="bg-white p-6 rounded-2xl shadow-soft">
              <h3 className="text-lg font-semibold text-neutral-800 mb-4">Gyártónkénti Termékszám</h3>
              <div className="space-y-3">
                {metrics.database.data.products_by_manufacturer.map((item, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-neutral-50 rounded-lg">
                    <span className="font-medium text-neutral-700">{item.manufacturer}</span>
                    <div className="flex items-center space-x-3">
                      <span className="text-neutral-600">{item.count} termék</span>
                      <div className="w-20">
                        <ProgressBar 
                          value={item.count} 
                          max={Math.max(...metrics.database.data.products_by_manufacturer.map(m => m.count))} 
                          color="bg-primary-500"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* System Information */}
            <div className="bg-white p-6 rounded-2xl shadow-soft">
              <h3 className="text-lg font-semibold text-neutral-800 mb-4">Rendszer Információk</h3>
              <div className="space-y-4">
                <div className="border-l-4 border-primary-500 pl-4">
                  <h4 className="font-medium text-neutral-800">API Státusz</h4>
                  <p className="text-sm text-neutral-600">{metrics.health.message}</p>
                  <p className="text-xs text-neutral-500 mt-1">
                    Válaszidő: {metrics.performance.api_response_time}ms
                  </p>
                </div>
                
                <div className="border-l-4 border-accent-500 pl-4">
                  <h4 className="font-medium text-neutral-800">Adatbázis Státusz</h4>
                  <p className="text-sm text-neutral-600">
                    PostgreSQL kapcsolat: {metrics.database.data.database_status}
                  </p>
                  <p className="text-xs text-neutral-500 mt-1">
                    Összes rekord: {metrics.database.data.products + metrics.database.data.manufacturers + metrics.database.data.categories}
                  </p>
                </div>
                
                <div className="border-l-4 border-secondary-500 pl-4">
                  <h4 className="font-medium text-neutral-800">Keresési Szolgáltatás</h4>
                  <p className="text-sm text-neutral-600">
                    RAG pontosság: {((metrics.performance.search_accuracy || 0) * 100).toFixed(1)}%
                  </p>
                  <p className="text-xs text-neutral-500 mt-1">
                    ChromaDB dokumentumok: {metrics.database.data.products}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 