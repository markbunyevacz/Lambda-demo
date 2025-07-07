"use client";

import { useState } from 'react';
import Navigation, { NavigationTab } from '@/components/Navigation';
import Dashboard from '@/components/Dashboard';
import ChatWidget from '@/components/ChatWidget';
import AdminPanel from '@/components/AdminPanel/AdminPanel';
import SearchInterface from '@/components/SearchInterface/SearchInterface';
import ProductCatalog from '@/components/ProductCatalog/ProductCatalog';
import MonitoringDashboard from '@/components/MonitoringDashboard/MonitoringDashboard';

export default function Home() {
  const [activeTab, setActiveTab] = useState<NavigationTab>('dashboard');
  const [showChat, setShowChat] = useState(true);

  // These handlers can be passed to children components if needed
  const handleSearchSubmit = (query: string) => {
    console.log('Search submitted from parent:', query);
    // Potentially switch to search tab and pass the query
    setActiveTab('search');
  };

  const handleCategorySelect = (category: string) => {
    console.log('Category selected in parent:', category);
    // Potentially switch to products tab and pre-filter
    setActiveTab('products');
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