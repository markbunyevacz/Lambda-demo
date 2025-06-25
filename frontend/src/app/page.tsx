import { Search, Bot } from 'lucide-react';

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      
      {/* Header */}
      <header className="w-full bg-white shadow-md">
        <div className="container mx-auto px-4 py-3">
          <h1 className="text-2xl font-bold text-gray-800">
            Lambda<span className="text-orange-500">.hu</span> Építőanyag AI
          </h1>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-grow container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          
          {/* Search Bar */}
          <div className="relative mb-8">
            <input
              type="text"
              placeholder="Miben segíthetek? Keressen termékre, vagy tegyen fel kérdést..."
              className="w-full p-4 pl-12 text-lg border rounded-lg shadow-sm focus:ring-2 focus:ring-orange-500 focus:outline-none"
            />
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={24} />
          </div>

          {/* Product List Placeholder */}
          <div className="bg-white p-6 rounded-lg shadow-sm">
            <h2 className="text-xl font-semibold mb-4 text-gray-700">Termékajánlatok</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* Placeholder Product Cards */}
              {[1, 2, 3].map((i) => (
                <div key={i} className="border rounded-lg p-4 animate-pulse">
                  <div className="w-full h-32 bg-gray-200 rounded-md mb-3"></div>
                  <div className="h-6 bg-gray-200 rounded w-3/4 mb-2"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                </div>
              ))}
            </div>
          </div>

        </div>
      </main>

      {/* Floating AI Chat Button */}
      <div className="fixed bottom-8 right-8">
        <button className="bg-orange-500 text-white p-4 rounded-full shadow-lg hover:bg-orange-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500 transition-transform hover:scale-110">
          <Bot size={32} />
        </button>
      </div>

    </div>
  );
} 