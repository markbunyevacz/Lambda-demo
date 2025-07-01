"use client";

import { useState, useEffect, FormEvent } from 'react';

interface Manufacturer {
  id: number;
  name: string;
  description?: string;
  website?: string;
  country?: string;
}

export default function ManufacturersPage() {
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

  const [manufacturers, setManufacturers] = useState<Manufacturer[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    website: '',
    country: '',
  });

  const fetchManufacturers = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${backendUrl}/manufacturers`);
      const data = await res.json();
      setManufacturers(data);
      setError(null);
    } catch (err) {
      setError('Failed to load manufacturers');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchManufacturers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
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
    if (formData.website) params.append('website', formData.website);
    if (formData.country) params.append('country', formData.country);

    try {
      const res = await fetch(`${backendUrl}/manufacturers?${params.toString()}`, {
        method: 'POST',
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Failed to create manufacturer');
      }
      setFormData({ name: '', description: '', website: '', country: '' });
      await fetchManufacturers();
    } catch (err: any) {
      setError(err.message || 'Failed to create manufacturer');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex flex-col items-center p-8 bg-gray-900 text-white min-h-screen">
      <h1 className="text-3xl font-bold mb-6">Manufacturers</h1>

      <section className="w-full max-w-xl mb-12">
        <h2 className="text-xl font-semibold mb-4">Add Manufacturer</h2>
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
            type="url"
            name="website"
            value={formData.website}
            onChange={handleChange}
            placeholder="Website"
            className="w-full px-3 py-2 rounded bg-gray-800 focus:outline-none"
          />
          <input
            type="text"
            name="country"
            value={formData.country}
            onChange={handleChange}
            placeholder="Country"
            className="w-full px-3 py-2 rounded bg-gray-800 focus:outline-none"
          />
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
        <h2 className="text-xl font-semibold mb-4">Existing Manufacturers</h2>
        {loading && !manufacturers.length ? (
          <p>Loading...</p>
        ) : error ? (
          <p className="text-red-500">{error}</p>
        ) : (
          <table className="w-full text-left border-collapse">
            <thead>
              <tr>
                <th className="border-b border-gray-700 p-2">ID</th>
                <th className="border-b border-gray-700 p-2">Name</th>
                <th className="border-b border-gray-700 p-2">Website</th>
                <th className="border-b border-gray-700 p-2">Country</th>
              </tr>
            </thead>
            <tbody>
              {manufacturers.map((mfr) => (
                <tr key={mfr.id}>
                  <td className="border-b border-gray-700 p-2">{mfr.id}</td>
                  <td className="border-b border-gray-700 p-2">{mfr.name}</td>
                  <td className="border-b border-gray-700 p-2">{mfr.website || '-'}</td>
                  <td className="border-b border-gray-700 p-2">{mfr.country || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </main>
  );
}