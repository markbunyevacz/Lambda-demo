"use client";

import { useState, useEffect } from 'react';

interface AnalyticsData {
  totalProducts: number;
  totalSearches: number;
  avgResponseTime: number;
  topCategories: Array<{ name: string; count: number; percentage: number }>;
  recentActivity: Array<{ id: string; action: string; timestamp: string; details: string }>;
  performanceMetrics: {
    uptime: number;
    accuracy: number;
    satisfaction: number;
  };
}

export default function AnalyticsDashboard() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<'1h' | '24h' | '7d' | '30d'>('24h');

  const mockData: AnalyticsData = {
    totalProducts: 15847,
    totalSearches: 2834,
    avgResponseTime: 0.8,
    topCategories: [
      { name: 'Insulation', count: 4521, percentage: 28.5 },
      { name: 'Roofing', count: 3456, percentage: 21.8 },
      { name: 'Walls', count: 2890, percentage: 18.2 },
      { name: 'Flooring', count: 2234, percentage: 14.1 },
      { name: 'HVAC', count: 1876, percentage: 11.8 },
      { name: 'Other', count: 870, percentage: 5.6 }
    ],
    recentActivity: [
      {
        id: '1',
        action: 'Product Search',
        timestamp: '2 minutes ago',
        details: 'User searched for "thermal insulation"'
      },
      {
        id: '2',
        action: 'Data Sync',
        timestamp: '15 minutes ago',
        details: 'ROCKWOOL catalog updated - 234 products'
      },
      {
        id: '3',
        action: 'AI Analysis',
        timestamp: '32 minutes ago',
        details: 'Generated recommendations for sustainable materials'
      },
      {
        id: '4',
        action: 'Inventory Update',
        timestamp: '1 hour ago',
        details: 'Stock levels updated for 1,245 products'
      },
      {
        id: '5',
        action: 'Price Update',
        timestamp: '2 hours ago',
        details: 'Price changes detected for BRAMAC products'
      }
    ],
    performanceMetrics: {
      uptime: 99.7,
      accuracy: 94.2,
      satisfaction: 4.6
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      setData(mockData);
      setLoading(false);
    };

    fetchData();
  }, [timeRange]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400 mx-auto mb-4"></div>
          <p className="text-white">Loading analytics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900">
      {/* Header */}
      <header className="bg-gray-900/80 backdrop-blur-sm border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <a href="/demo" className="text-2xl font-bold text-white">
                Lambda<span className="text-blue-400">.hu</span>
              </a>
              <span className="text-gray-400">|</span>
              <h1 className="text-lg font-medium text-white">Analytics Dashboard</h1>
            </div>
            <div className="flex items-center space-x-4">
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value as any)}
                className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="1h">Last Hour</option>
                <option value="24h">Last 24 Hours</option>
                <option value="7d">Last 7 Days</option>
                <option value="30d">Last 30 Days</option>
              </select>
              <div className="text-sm text-gray-400">
                DEMO MODE
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-400">Total Products</p>
                <p className="text-2xl font-bold text-white">{data?.totalProducts.toLocaleString()}</p>
              </div>
              <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4-8-4m16 0v10l-8 4-8-4V7" />
                </svg>
              </div>
            </div>
            <div className="mt-2 flex items-center text-sm">
              <span className="text-green-400">+12%</span>
              <span className="text-gray-400 ml-2">vs last month</span>
            </div>
          </div>

          <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-400">Searches Today</p>
                <p className="text-2xl font-bold text-white">{data?.totalSearches.toLocaleString()}</p>
              </div>
              <div className="w-12 h-12 bg-green-600 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
            </div>
            <div className="mt-2 flex items-center text-sm">
              <span className="text-green-400">+8%</span>
              <span className="text-gray-400 ml-2">vs yesterday</span>
            </div>
          </div>

          <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-400">Avg Response Time</p>
                <p className="text-2xl font-bold text-white">{data?.avgResponseTime}s</p>
              </div>
              <div className="w-12 h-12 bg-purple-600 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
            <div className="mt-2 flex items-center text-sm">
              <span className="text-green-400">-15%</span>
              <span className="text-gray-400 ml-2">faster than target</span>
            </div>
          </div>

          <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-400">AI Accuracy</p>
                <p className="text-2xl font-bold text-white">{data?.performanceMetrics.accuracy}%</p>
              </div>
              <div className="w-12 h-12 bg-orange-600 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
            </div>
            <div className="mt-2 flex items-center text-sm">
              <span className="text-green-400">+2.1%</span>
              <span className="text-gray-400 ml-2">this week</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Category Distribution */}
          <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700">
            <h2 className="text-xl font-semibold text-white mb-6">Product Categories</h2>
            <div className="space-y-4">
              {data?.topCategories.map((category, index) => (
                <div key={category.name} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`w-3 h-3 rounded-full ${
                      index === 0 ? 'bg-blue-500' :
                      index === 1 ? 'bg-green-500' :
                      index === 2 ? 'bg-purple-500' :
                      index === 3 ? 'bg-yellow-500' :
                      index === 4 ? 'bg-red-500' : 'bg-gray-500'
                    }`}></div>
                    <span className="text-white font-medium">{category.name}</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <span className="text-gray-400 text-sm">{category.count.toLocaleString()}</span>
                    <span className="text-white font-medium">{category.percentage}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Activity */}
          <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700">
            <h2 className="text-xl font-semibold text-white mb-6">Recent Activity</h2>
            <div className="space-y-4">
              {data?.recentActivity.map((activity) => (
                <div key={activity.id} className="flex items-start space-x-3">
                  <div className="w-2 h-2 rounded-full bg-blue-500 mt-2"></div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-white font-medium">{activity.action}</span>
                      <span className="text-xs text-gray-400">{activity.timestamp}</span>
                    </div>
                    <p className="text-sm text-gray-300 mt-1">{activity.details}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Performance Metrics */}
          <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700 lg:col-span-2">
            <h2 className="text-xl font-semibold text-white mb-6">System Performance</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="relative w-24 h-24 mx-auto mb-4">
                  <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 24 24">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" fill="none" className="text-gray-600" />
                    <circle 
                      cx="12" 
                      cy="12" 
                      r="10" 
                      stroke="currentColor" 
                      strokeWidth="2" 
                      fill="none" 
                      className="text-green-500"
                      strokeDasharray={`${2 * Math.PI * 10 * (data?.performanceMetrics.uptime || 0) / 100} ${2 * Math.PI * 10}`}
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-2xl font-bold text-white">{data?.performanceMetrics.uptime}%</span>
                  </div>
                </div>
                <p className="text-gray-300 font-medium">System Uptime</p>
              </div>

              <div className="text-center">
                <div className="relative w-24 h-24 mx-auto mb-4">
                  <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 24 24">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" fill="none" className="text-gray-600" />
                    <circle 
                      cx="12" 
                      cy="12" 
                      r="10" 
                      stroke="currentColor" 
                      strokeWidth="2" 
                      fill="none" 
                      className="text-blue-500"
                      strokeDasharray={`${2 * Math.PI * 10 * (data?.performanceMetrics.accuracy || 0) / 100} ${2 * Math.PI * 10}`}
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-2xl font-bold text-white">{data?.performanceMetrics.accuracy}%</span>
                  </div>
                </div>
                <p className="text-gray-300 font-medium">Search Accuracy</p>
              </div>

              <div className="text-center">
                <div className="relative w-24 h-24 mx-auto mb-4">
                  <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 24 24">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" fill="none" className="text-gray-600" />
                    <circle 
                      cx="12" 
                      cy="12" 
                      r="10" 
                      stroke="currentColor" 
                      strokeWidth="2" 
                      fill="none" 
                      className="text-purple-500"
                      strokeDasharray={`${2 * Math.PI * 10 * (data?.performanceMetrics.satisfaction || 0) / 5 * 100 / 100} ${2 * Math.PI * 10}`}
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-2xl font-bold text-white">{data?.performanceMetrics.satisfaction}/5</span>
                  </div>
                </div>
                <p className="text-gray-300 font-medium">User Satisfaction</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}