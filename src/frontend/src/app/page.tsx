"use client";

import { useState } from 'react';
import Navigation, { NavigationTab } from '@/components/Navigation';
import Dashboard from '@/components/Dashboard';
import ChatWidget from '@/components/ChatWidget';
import AdminPanel from '@/components/AdminPanel/AdminPanel';

// Placeholder komponensek a többi fülhöz
const SearchInterface = () => (
  <div className="min-h-screen bg-neutral-50 p-6">
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-neutral-800 mb-6">Intelligens Keresés</h1>
      <div className="bg-white p-8 rounded-2xl shadow-soft">
        <p className="text-neutral-600 mb-4">
          Itt lesz a hibrid keresési interfész RAG-alapú természetes nyelvi kereséssel és szűrőkkel.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-primary-50 rounded-lg">
            <h3 className="font-semibold text-primary-800 mb-2">Szöveg alapú keresés</h3>
            <p className="text-sm text-primary-600">Természetes nyelvű lekérdezések</p>
          </div>
          <div className="p-4 bg-secondary-50 rounded-lg">
            <h3 className="font-semibold text-secondary-800 mb-2">Műszaki szűrők</h3>
            <p className="text-sm text-secondary-600">Paraméter-alapú szűrési opciók</p>
          </div>
          <div className="p-4 bg-accent-50 rounded-lg">
            <h3 className="font-semibold text-accent-800 mb-2">AI ajánlások</h3>
            <p className="text-sm text-accent-600">Intelligens termék javaslatok</p>
          </div>
        </div>
      </div>
    </div>
  </div>
);

const ProductCatalog = () => (
  <div className="min-h-screen bg-neutral-50 p-6">
    <div className="max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold text-neutral-800 mb-6">Termék Katalógus</h1>
      <div className="bg-white p-8 rounded-2xl shadow-soft">
        <p className="text-neutral-600 mb-6">
          Gyártó-specifikus termék böngészés interaktív katalógussal.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-6 border-2 border-primary-200 rounded-xl">
            <h3 className="text-lg font-bold text-primary-800 mb-2">ROCKWOOL</h3>
            <p className="text-sm text-neutral-600 mb-4">129 termék</p>
            <div className="space-y-2 text-sm">
              <div className="text-neutral-700">• Hőszigetelő lemezek</div>
              <div className="text-neutral-700">• Tetőszigetelés</div>
              <div className="text-neutral-700">• Homlokzati rendszerek</div>
            </div>
          </div>
          <div className="p-6 border-2 border-secondary-200 rounded-xl">
            <h3 className="text-lg font-bold text-secondary-800 mb-2">Leier</h3>
            <p className="text-sm text-neutral-600 mb-4">87 termék</p>
            <div className="space-y-2 text-sm">
              <div className="text-neutral-700">• Falazóelemek</div>
              <div className="text-neutral-700">• Tetőcserepek</div>
              <div className="text-neutral-700">• Előregyártott elemek</div>
            </div>
          </div>
          <div className="p-6 border-2 border-accent-200 rounded-xl">
            <h3 className="text-lg font-bold text-accent-800 mb-2">Baumit</h3>
            <p className="text-sm text-neutral-600 mb-4">156 termék</p>
            <div className="space-y-2 text-sm">
              <div className="text-neutral-700">• HŐSZ rendszerek</div>
              <div className="text-neutral-700">• Homlokzatfestékek</div>
              <div className="text-neutral-700">• Színes vakolatok</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
);

const MonitoringDashboard = () => (
  <div className="min-h-screen bg-neutral-50 p-6">
    <div className="max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold text-neutral-800 mb-6">Rendszer Monitoring</h1>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-2xl shadow-soft">
          <h3 className="text-lg font-semibold text-neutral-800 mb-4">Teljesítmény Metrikák</h3>
          <div className="space-y-4">
            <div className="flex justify-between">
              <span className="text-neutral-600">API válaszidő</span>
              <span className="text-accent-600 font-medium">0.8s</span>
            </div>
            <div className="flex justify-between">
              <span className="text-neutral-600">RAG pontosság</span>
              <span className="text-accent-600 font-medium">94.2%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-neutral-600">Aktív felhasználók</span>
              <span className="text-accent-600 font-medium">156</span>
            </div>
          </div>
        </div>
        <div className="bg-white p-6 rounded-2xl shadow-soft">
          <h3 className="text-lg font-semibold text-neutral-800 mb-4">Rendszer Állapot</h3>
          <div className="space-y-4">
            <div className="flex items-center">
              <div className="w-3 h-3 bg-accent-500 rounded-full mr-3"></div>
              <span className="text-neutral-700">PostgreSQL: Elérhető</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-accent-500 rounded-full mr-3"></div>
              <span className="text-neutral-700">ChromaDB: Elérhető</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-accent-500 rounded-full mr-3"></div>
              <span className="text-neutral-700">Claude AI: Elérhető</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
);

export default function Home() {
  const [activeTab, setActiveTab] = useState<NavigationTab>('dashboard');
  const [showChat, setShowChat] = useState(true);

  const handleSearchSubmit = (query: string) => {
    console.log('Search submitted:', query);
    // Itt majd meghívjuk a RAG API-t
  };

  const handleCategorySelect = (category: string) => {
    console.log('Category selected:', category);
    setActiveTab('products'); // Váltás a termék katalógusra
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <Dashboard 
            onSearchSubmit={handleSearchSubmit}
            onCategorySelect={handleCategorySelect}
          />
        );
      case 'search':
        return <SearchInterface />;
      case 'products':
        return <ProductCatalog />;
      case 'monitoring':
        return <MonitoringDashboard />;
      case 'admin':
        return <AdminPanel />;
      default:
        return (
          <Dashboard 
            onSearchSubmit={handleSearchSubmit}
            onCategorySelect={handleCategorySelect}
          />
        );
    }
  };

  return (
    <div className="min-h-screen bg-neutral-50">
      <Navigation activeTab={activeTab} onTabChange={setActiveTab} />
      <main>
        {renderContent()}
      </main>
      {showChat && <ChatWidget />}
    </div>
  );
} 