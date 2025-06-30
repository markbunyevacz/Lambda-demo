"use client";

import { useState } from 'react';

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleScrape = async (scraperType: 'datasheet' | 'brochure') => {
    setLoading(true);
    setMessage('');

    try {
      const response = await fetch('/api/v1/scrape', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ scraper_type: scraperType }),
      });

      const data = await response.json();

      if (response.ok) {
        setMessage(`Task started successfully! Task ID: ${data.task_id}`);
      } else {
        setMessage(`Error: ${data.detail || 'Unknown error'}`);
      }
    } catch (error) {
      setMessage('Failed to connect to the backend.');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gray-900 text-white">
      <div className="z-10 w-full max-w-5xl items-center justify-between font-mono text-sm lg:flex">
        <p className="fixed left-0 top-0 flex w-full justify-center border-b border-gray-700 bg-gray-800 from-zinc-200 pb-6 pt-8 backdrop-blur-2xl lg:static lg:w-auto lg:rounded-xl lg:border lg:bg-gray-700 lg:p-4">
          Lambda.hu Scraping Control Panel
        </p>
        <div className="fixed right-4 top-4 lg:static">
          <a 
            href="/demo" 
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            View Demo
          </a>
        </div>
      </div>

      <div className="relative z-[-1] flex place-items-center mt-16">
        <h1 className="text-4xl font-bold">Data Refresh</h1>
      </div>

      <div className="mb-32 mt-16 grid gap-8 text-center lg:mb-0 lg:w-full lg:max-w-5xl lg:grid-cols-2 lg:text-left">
        <button
          onClick={() => handleScrape('datasheet')}
          disabled={loading}
          className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-500 hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <h2 className="mb-3 text-2xl font-semibold">
            Update Datasheets{' '}
            <span className="inline-block transition-transform group-hover:translate-x-1 motion-reduce:transform-none">
              -&gt;
            </span>
          </h2>
          <p className="m-0 max-w-[30ch] text-sm opacity-70">
            Fetch the latest product datasheets from the Rockwool website.
          </p>
        </button>

        <button
          onClick={() => handleScrape('brochure')}
          disabled={loading}
          className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-500 hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <h2 className="mb-3 text-2xl font-semibold">
            Update Brochures{' '}
            <span className="inline-block transition-transform group-hover:translate-x-1 motion-reduce:transform-none">
              -&gt;
            </span>
          </h2>
          <p className="m-0 max-w-[30ch] text-sm opacity-70">
            Download the latest brochures and pricelists.
          </p>
        </button>
      </div>

      {message && (
        <div className="mt-8 rounded-lg bg-gray-800 p-4 text-center">
          <p>{message}</p>
        </div>
      )}
    </main>
  );
} 