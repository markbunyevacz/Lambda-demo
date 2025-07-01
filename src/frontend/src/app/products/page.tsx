"use client";

import { useState, useEffect, FormEvent } from 'react';

interface Product {
  id: number;
  name: string;
  description?: string;
  price?: number;
  category_id?: number;
  manufacturer_id?: number;
}

interface CategoryOption {
  id: number;
  name: string;
}

interface ManufacturerOption {
  id: number;
  name: string;
}

export default function ProductsPage() {
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<CategoryOption[]>([]);
  const [manufacturers, setManufacturers] = useState<ManufacturerOption[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    price: '',
    category_id: '',
    manufacturer_id: '',
  });

  const fetchInitialData = async () => {
    setLoading(true);
    try {
      const [prodRes, catRes, mfrRes] = await Promise.all([
        fetch(`${backendUrl}/products`),
        fetch(`${backendUrl}/categories`),
        fetch(`${backendUrl}/manufacturers`),
      ]);
      const [prodData, catData, mfrData] = await Promise.all([
        prodRes.json(),
        catRes.json(),
        mfrRes.json(),
      ]);
      setProducts(prodData);
      setCategories(catData);
      setManufacturers(mfrData);
      setError(null);
    } catch (err) {
      setError('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInitialData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) return;

    setLoading(true);
    const params = new URLSearchParams();
    params.append('name', formData.name);
    if (formData.description) params.append('description', formData.description);
    if (formData.price) params.append('price', formData.price);
    if (formData.category_id) params.append('category_id', formData.category_id);
    if (formData.manufacturer_id) params.append('manufacturer_id', formData.manufacturer_id);

    try {
      const res = await fetch(`${backendUrl}/products?${params.toString()}`, {
        method: 'POST',
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Failed to create product');
      }
      setFormData({ name: '', description: '', price: '', category_id: '', manufacturer_id: '' });
      await fetchInitialData();
    } catch (err: any) {
      setError(err.message || 'Failed to create product');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex flex-col items-center p-8 bg-gray-900 text-white min-h-screen">
      <h1 className="text-3xl font-bold mb-6">Products</h1>

      <section className="w-full max-w-xl mb-12">
        <h2 className="text-xl font-semibold mb-4">Add Product</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            placeholder="Name"
            className="w-full px-3 py-2 rounded bg-gray-800 focus:outline-none"
          />
          <input
            type="text"
            name="description"
            value={formData.description}
            onChange={handleChange}
            placeholder="Description"
            className="w-full px-3 py-2 rounded bg-gray-800 focus:outline-none"
          />
          <input
            type="number"
            name="price"
            value={formData.price}
            onChange={handleChange}
            placeholder="Price"
            className="w-full px-3 py-2 rounded bg-gray-800 focus:outline-none"
          />
          <select
            name="category_id"
            value={formData.category_id}
            onChange={handleChange}
            className="w-full px-3 py-2 rounded bg-gray-800 focus:outline-none"
          >
            <option value="">Select Category</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {cat.name}
              </option>
            ))}
          </select>
          <select
            name="manufacturer_id"
            value={formData.manufacturer_id}
            onChange={handleChange}
            className="w-full px-3 py-2 rounded bg-gray-800 focus:outline-none"
          >
            <option value="">Select Manufacturer</option>
            {manufacturers.map((mfr) => (
              <option key={mfr.id} value={mfr.id}>
                {mfr.name}
              </option>
            ))}
          </select>
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded disabled:opacity-50"
          >
            {loading ? 'Saving...' : 'Create'}
          </button>
        </form>
      </section>

      <section className="w-full max-w-5xl overflow-x-auto">
        <h2 className="text-xl font-semibold mb-4">Existing Products</h2>
        {loading && !products.length ? (
          <p>Loading...</p>
        ) : error ? (
          <p className="text-red-500">{error}</p>
        ) : (
          <table className="min-w-full text-left border-collapse">
            <thead>
              <tr>
                <th className="border-b border-gray-700 p-2">ID</th>
                <th className="border-b border-gray-700 p-2">Name</th>
                <th className="border-b border-gray-700 p-2">Price</th>
                <th className="border-b border-gray-700 p-2">Category</th>
                <th className="border-b border-gray-700 p-2">Manufacturer</th>
              </tr>
            </thead>
            <tbody>
              {products.map((prod) => (
                <tr key={prod.id}>
                  <td className="border-b border-gray-700 p-2">{prod.id}</td>
                  <td className="border-b border-gray-700 p-2">{prod.name}</td>
                  <td className="border-b border-gray-700 p-2">{prod.price ?? '-'}</td>
                  <td className="border-b border-gray-700 p-2">{prod.category_id ?? '-'}</td>
                  <td className="border-b border-gray-700 p-2">{prod.manufacturer_id ?? '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </main>
  );
}