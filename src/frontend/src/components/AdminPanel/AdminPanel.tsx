'use client';

import React, { useState, useEffect } from 'react';

interface DatabaseStats {
  manufacturers: number;
  categories: number;
  products: number;
  processed_files: number;
  last_updated: string;
  products_by_manufacturer: Array<{
    manufacturer: string;
    count: number;
  }>;
}

interface Product {
  id: number;
  name: string;
  sku: string;
  price: number | null;
  manufacturer: string | null;
  category: string | null;
  technical_specs_count: number;
  has_full_text: boolean;
  full_text_length: number;
  created_at: string | null;
}

interface ProductDetail {
  id: number;
  name: string;
  description: string;
  sku: string;
  price: number | null;
  manufacturer: {
    id: number;
    name: string;
    website: string;
  } | null;
  category: {
    id: number;
    name: string;
    parent_id: number | null;
  } | null;
  technical_specs: Record<string, any>;
  full_text_content: string;
  full_text_length: number;
  created_at: string | null;
}

const AdminPanel: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'products' | 'detail'>('overview');
  const [stats, setStats] = useState<DatabaseStats | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<ProductDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const API_BASE = 'http://localhost:8000/admin';

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/database/overview`);
      if (!response.ok) throw new Error('Failed to fetch stats');
      const data = await response.json();
      setStats(data.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const fetchProducts = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/database/products?limit=50`);
      if (!response.ok) throw new Error('Failed to fetch products');
      const data = await response.json();
      setProducts(data.data.products);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const fetchProductDetail = async (productId: number) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/database/product/${productId}`);
      if (!response.ok) throw new Error('Failed to fetch product detail');
      const data = await response.json();
      setSelectedProduct(data.data);
      setActiveTab('detail');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'overview') {
      fetchStats();
    } else if (activeTab === 'products') {
      fetchProducts();
    }
  }, [activeTab]);

  const renderOverview = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">📊 Adatbázis Áttekintés</h2>
      
      {stats && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-blue-100 p-4 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{stats.manufacturers}</div>
              <div className="text-sm text-gray-600">Gyártók</div>
            </div>
            <div className="bg-green-100 p-4 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{stats.categories}</div>
              <div className="text-sm text-gray-600">Kategóriák</div>
            </div>
            <div className="bg-purple-100 p-4 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">{stats.products}</div>
              <div className="text-sm text-gray-600">Termékek</div>
            </div>
            <div className="bg-orange-100 p-4 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">{stats.processed_files}</div>
              <div className="text-sm text-gray-600">Feldolgozott fájlok</div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-4">🏭 Termékek gyártónként</h3>
            <div className="space-y-2">
              {stats.products_by_manufacturer.map((item, index) => (
                <div key={index} className="flex justify-between items-center py-2 border-b">
                  <span className="font-medium">{item.manufacturer}</span>
                  <span className="bg-gray-100 px-3 py-1 rounded-full text-sm">
                    {item.count} termék
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="text-sm text-gray-500">
            Utolsó frissítés: {new Date(stats.last_updated).toLocaleString('hu-HU')}
          </div>
        </>
      )}
    </div>
  );

  const renderProducts = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-800">📋 Termékek listája</h2>
        <button
          onClick={fetchProducts}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        >
          🔄 Frissítés
        </button>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Termék név
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Gyártó
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Kategória
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Műszaki adatok
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Teljes szöveg
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Műveletek
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {products.map((product) => (
                <tr key={product.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {product.id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {product.name}
                    </div>
                    <div className="text-sm text-gray-500">{product.sku}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {product.manufacturer || 'N/A'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {product.category || 'N/A'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {product.technical_specs_count} spec
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="flex items-center">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        product.has_full_text 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {product.has_full_text ? '✅' : '❌'}
                      </span>
                      {product.has_full_text && (
                        <span className="ml-2 text-xs text-gray-500">
                          {(product.full_text_length / 1000).toFixed(1)}k chars
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      onClick={() => fetchProductDetail(product.id)}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      🔍 Részletek
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  const renderProductDetail = () => (
    selectedProduct && (
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setActiveTab('products')}
            className="text-blue-600 hover:text-blue-800"
          >
            ← Vissza a termékekhez
          </button>
          <h2 className="text-2xl font-bold text-gray-800">
            🔍 {selectedProduct.name}
          </h2>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-4">Alapadatok</h3>
            <div className="space-y-3">
              <div>
                <span className="font-medium">ID:</span> {selectedProduct.id}
              </div>
              <div>
                <span className="font-medium">SKU:</span> {selectedProduct.sku || 'N/A'}
              </div>
              <div>
                <span className="font-medium">Ár:</span> {selectedProduct.price || 'N/A'} HUF
              </div>
              <div>
                <span className="font-medium">Gyártó:</span> {selectedProduct.manufacturer?.name || 'N/A'}
              </div>
              <div>
                <span className="font-medium">Kategória:</span> {selectedProduct.category?.name || 'N/A'}
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-4">Műszaki adatok</h3>
            <div className="space-y-2">
              {Object.entries(selectedProduct.technical_specs || {}).map(([key, value]) => (
                <div key={key} className="flex justify-between">
                  <span className="font-medium">{key}:</span>
                  <span>{JSON.stringify(value)}</span>
                </div>
              ))}
              {Object.keys(selectedProduct.technical_specs || {}).length === 0 && (
                <div className="text-gray-500">Nincsenek műszaki adatok</div>
              )}
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Leírás</h3>
          <p className="text-gray-700">{selectedProduct.description || 'Nincs leírás'}</p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">
            Teljes szöveges tartalom ({selectedProduct.full_text_length} karakter)
          </h3>
          <div className="bg-gray-50 p-4 rounded max-h-96 overflow-y-auto">
            <pre className="whitespace-pre-wrap text-sm">
              {selectedProduct.full_text_content || 'Nincs szöveges tartalom'}
            </pre>
          </div>
        </div>
      </div>
    )
  );

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <h1 className="text-3xl font-bold text-gray-900">
              🔧 Lambda.hu Admin Panel
            </h1>
            <div className="text-sm text-gray-500">
              PostgreSQL Adatbázis Viewer
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <nav className="flex space-x-4">
            <button
              onClick={() => setActiveTab('overview')}
              className={`px-4 py-2 rounded-lg font-medium ${
                activeTab === 'overview'
                  ? 'bg-blue-500 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              📊 Áttekintés
            </button>
            <button
              onClick={() => setActiveTab('products')}
              className={`px-4 py-2 rounded-lg font-medium ${
                activeTab === 'products'
                  ? 'bg-blue-500 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              📋 Termékek
            </button>
          </nav>
        </div>

        {loading && (
          <div className="text-center py-8">
            <div className="text-xl">🔄 Betöltés...</div>
          </div>
        )}

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            ❌ Hiba: {error}
          </div>
        )}

        {!loading && !error && (
          <>
            {activeTab === 'overview' && renderOverview()}
            {activeTab === 'products' && renderProducts()}
            {activeTab === 'detail' && renderProductDetail()}
          </>
        )}
      </div>
    </div>
  );
};

export default AdminPanel; 