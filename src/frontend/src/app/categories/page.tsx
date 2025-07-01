"use client";

import { useState, useEffect, FormEvent } from 'react';

interface Category {
  id: number;
  name: string;
  description?: string;
  parent_id?: number | null;
}

export default function CategoriesPage() {
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    parent_id: '',
  });

  const fetchCategories = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${backendUrl}/categories`);
      const data = await res.json();
      setCategories(data);
      setError(null);
    } catch (err) {
      setError('Failed to load categories');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCategories();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      return;
    }
    setLoading(true);
    const params = new URLSearchParams();
    params.append('name', formData.name);
    if (formData.description) params.append('description', formData.description);
    if (formData.parent_id) params.append('parent_id', formData.parent_id);

    try {
      const res = await fetch(`${backendUrl}/categories?${params.toString()}`, {
        method: 'POST',
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Failed to create category');
      }
      setFormData({ name: '', description: '', parent_id: '' });
      await fetchCategories();
    } catch (err: any) {
      setError(err.message || 'Failed to create category');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex flex-col items-center p-8 bg-gray-900 text-white min-h-screen">
      <h1 className="text-3xl font-bold mb-6">Categories</h1>

      <section className="w-full max-w-xl mb-12">
        <h2 className="text-xl font-semibold mb-4">Add Category</h2>
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
          <select
            name="parent_id"
            value={formData.parent_id}
            onChange={handleChange}
            className="w-full px-3 py-2 rounded bg-gray-800 focus:outline-none"
          >
            <option value="">No parent</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {cat.name}
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

      <section className="w-full max-w-3xl">
        <h2 className="text-xl font-semibold mb-4">Existing Categories</h2>
        {loading && !categories.length ? (
          <p>Loading...</p>
        ) : error ? (
          <p className="text-red-500">{error}</p>
        ) : (
          <table className="w-full text-left border-collapse">
            <thead>
              <tr>
                <th className="border-b border-gray-700 p-2">ID</th>
                <th className="border-b border-gray-700 p-2">Name</th>
                <th className="border-b border-gray-700 p-2">Description</th>
                <th className="border-b border-gray-700 p-2">Parent</th>
              </tr>
            </thead>
            <tbody>
              {categories.map((cat) => (
                <tr key={cat.id}>
                  <td className="border-b border-gray-700 p-2">{cat.id}</td>
                  <td className="border-b border-gray-700 p-2">{cat.name}</td>
                  <td className="border-b border-gray-700 p-2">{cat.description || '-'}</td>
                  <td className="border-b border-gray-700 p-2">{cat.parent_id || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </main>
  );
}