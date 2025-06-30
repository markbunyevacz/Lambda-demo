"use client";

import { useState, useEffect } from 'react';

interface Product {
  id: string;
  name: string;
  category: string;
  description: string;
  specifications: Record<string, string>;
  price?: string;
  imageUrl?: string;
  manufacturer: string;
  inStock: boolean;
}

interface SearchResult {
  products: Product[];
  totalCount: number;
  processingTime: number;
  aiInsights: string[];
}

export default function LambdaDemo() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<SearchResult | null>(null);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [priceRange, setPriceRange] = useState<[number, number]>([0, 100000]);
  const [aiMode, setAiMode] = useState<'smart' | 'precise' | 'creative'>('smart');

  const categories = [
    'all',
    'insulation',
    'roofing',
    'facades',
    'flooring',
    'walls',
    'hvac',
    'structural'
  ];

  const sampleProducts: Product[] = [
    {
      id: '1',
      name: 'ROCKWOOL FRONTROCK MAX E',
      category: 'insulation',
      description: 'High-performance stone wool insulation for external walls with excellent fire resistance',
      specifications: {
        'Thermal Conductivity': '0.034 W/mK',
        'Fire Rating': 'A1 (Non-combustible)',
        'Thickness': '50-200mm',
        'Density': '140 kg/m³'
      },
      manufacturer: 'ROCKWOOL',
      inStock: true,
      imageUrl: '/api/placeholder/300/200'
    },
    {
      id: '2',
      name: 'YTONG Silka S18 Block',
      category: 'walls',
      description: 'Autoclaved aerated concrete blocks for energy-efficient construction',
      specifications: {
        'Compressive Strength': '18 N/mm²',
        'Thermal Conductivity': '0.14 W/mK',
        'Dimensions': '625x240x175mm',
        'Weight': '8.5 kg/block'
      },
      manufacturer: 'YTONG',
      inStock: true,
      imageUrl: '/api/placeholder/300/200'
    },
    {
      id: '3',
      name: 'BRAMAC Classic Protector',
      category: 'roofing',
      description: 'Premium concrete roof tiles with 30-year warranty',
      specifications: {
        'Material': 'Concrete',
        'Coverage': '9.9 tiles/m²',
        'Weight': '45 kg/m²',
        'Colors': '8 standard colors'
      },
      manufacturer: 'BRAMAC',
      inStock: false,
      imageUrl: '/api/placeholder/300/200'
    }
  ];

  const handleSearch = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    
    // Simulate API call with realistic delay
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    const mockResult: SearchResult = {
      products: sampleProducts.filter(p => 
        selectedCategory === 'all' || p.category === selectedCategory
      ),
      totalCount: sampleProducts.length,
      processingTime: 0.8,
      aiInsights: [
        'Based on your query, I recommend focusing on thermal performance',
        'Consider fire safety requirements for your building type',
        'These products offer excellent value for sustainable construction'
      ]
    };
    
    setResults(mockResult);
    setLoading(false);
  };

  const handleQuickSearch = (searchTerm: string) => {
    setQuery(searchTerm);
    setTimeout(() => handleSearch(), 100);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900">
      {/* Header */}
      <header className="bg-gray-900/80 backdrop-blur-sm border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <div className="text-2xl font-bold text-white">
                Lambda<span className="text-blue-400">.hu</span>
              </div>
              <div className="ml-4 text-sm text-gray-300">
                AI Building Materials Platform
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <a 
                href="/demo/analytics" 
                className="text-sm text-blue-400 hover:text-blue-300 transition-colors"
              >
                Analytics
              </a>
              <div className="text-sm text-gray-400">
                DEMO MODE
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-white mb-4">
            AI-Powered Building Materials Search
          </h1>
          <p className="text-xl text-gray-300 mb-8">
            Find the perfect materials for your construction project using advanced AI technology
          </p>
          
          {/* Quick Search Buttons */}
          <div className="flex flex-wrap justify-center gap-3 mb-8">
            {[
              'Thermal insulation for apartment building',
              'Fire-resistant wall materials',
              'Sustainable roofing solutions',
              'Energy-efficient windows'
            ].map((term) => (
              <button
                key={term}
                onClick={() => handleQuickSearch(term)}
                className="px-4 py-2 bg-blue-600/20 text-blue-300 rounded-full hover:bg-blue-600/30 transition-colors text-sm"
              >
                {term}
              </button>
            ))}
          </div>
        </div>

        {/* Search Interface */}
        <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 mb-8 border border-gray-700">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 mb-6">
            {/* Main Search */}
            <div className="lg:col-span-2">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Search Query
              </label>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Describe what you're looking for..."
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Category Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Category
              </label>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {categories.map(cat => (
                  <option key={cat} value={cat}>
                    {cat.charAt(0).toUpperCase() + cat.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            {/* AI Mode */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                AI Mode
              </label>
              <select
                value={aiMode}
                onChange={(e) => setAiMode(e.target.value as any)}
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="smart">Smart Search</option>
                <option value="precise">Precise Match</option>
                <option value="creative">Creative Suggestions</option>
              </select>
            </div>
          </div>

          <button
            onClick={handleSearch}
            disabled={loading || !query.trim()}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-medium py-3 px-6 rounded-lg transition-colors disabled:cursor-not-allowed flex items-center justify-center"
          >
            {loading ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Searching with AI...
              </>
            ) : (
              'Search Products'
            )}
          </button>
        </div>

        {/* Results */}
        {results && (
          <div className="space-y-6">
            {/* Search Summary */}
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-white">
                  Search Results ({results.totalCount} products)
                </h2>
                <div className="text-sm text-gray-400">
                  Processed in {results.processingTime}s
                </div>
              </div>
              
              {/* AI Insights */}
              <div className="mb-4">
                <h3 className="text-sm font-medium text-blue-300 mb-2">AI Insights:</h3>
                <div className="space-y-1">
                  {results.aiInsights.map((insight, index) => (
                    <div key={index} className="text-sm text-gray-300 flex items-start">
                      <span className="text-blue-400 mr-2">•</span>
                      {insight}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Product Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {results.products.map((product) => (
                <div
                  key={product.id}
                  className="bg-gray-800/50 backdrop-blur-sm rounded-xl overflow-hidden border border-gray-700 hover:border-gray-600 transition-colors"
                >
                  {/* Product Image */}
                  <div className="h-48 bg-gray-700 flex items-center justify-center">
                    <div className="text-gray-500 text-sm">Product Image</div>
                  </div>
                  
                  <div className="p-6">
                    {/* Product Header */}
                    <div className="flex items-start justify-between mb-3">
                      <h3 className="text-lg font-semibold text-white leading-tight">
                        {product.name}
                      </h3>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        product.inStock 
                          ? 'bg-green-900/50 text-green-300 border border-green-700'
                          : 'bg-red-900/50 text-red-300 border border-red-700'
                      }`}>
                        {product.inStock ? 'In Stock' : 'Out of Stock'}
                      </span>
                    </div>
                    
                    {/* Manufacturer */}
                    <div className="text-sm text-blue-400 mb-3">
                      {product.manufacturer}
                    </div>
                    
                    {/* Description */}
                    <p className="text-sm text-gray-300 mb-4 line-clamp-3">
                      {product.description}
                    </p>
                    
                    {/* Specifications */}
                    <div className="space-y-2 mb-4">
                      {Object.entries(product.specifications).slice(0, 3).map(([key, value]) => (
                        <div key={key} className="flex justify-between text-xs">
                          <span className="text-gray-400">{key}:</span>
                          <span className="text-gray-200">{value}</span>
                        </div>
                      ))}
                    </div>
                    
                    {/* Actions */}
                    <div className="flex gap-2">
                      <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium py-2 px-4 rounded-lg transition-colors">
                        View Details
                      </button>
                      <button className="bg-gray-700 hover:bg-gray-600 text-white text-sm font-medium py-2 px-4 rounded-lg transition-colors">
                        Add to Cart
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Feature Showcase */}
        {!results && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mt-12">
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700">
              <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">AI-Powered Search</h3>
              <p className="text-gray-300 text-sm">
                Advanced AI understands your requirements and finds the perfect materials for your project.
              </p>
            </div>

            <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700">
              <div className="w-12 h-12 bg-green-600 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">Quality Assured</h3>
              <p className="text-gray-300 text-sm">
                All products are verified and sourced from trusted manufacturers with detailed specifications.
              </p>
            </div>

            <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700">
              <div className="w-12 h-12 bg-purple-600 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">Real-time Updates</h3>
              <p className="text-gray-300 text-sm">
                Live inventory tracking and price updates ensure you always have current information.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}