'use client';

import React, { useState } from 'react';
import ExtractionAnalysis from './ExtractionAnalysis'; // Assuming this is now in its own file

// You should create separate components for these for better organization
const AdminOverview = () => <div>Áttekintés Tartalom (helyőrző)...</div>;
const AdminProducts = () => <div>Termékek Tartalom (helyőrző)...</div>;

type AdminTab = 'overview' | 'products' | 'analysis';

const AdminPanel: React.FC = () => {
  const [activeTab, setActiveTab] = useState<AdminTab>('analysis');

  const TabButton: React.FC<{
    tabName: AdminTab;
    currentTab: AdminTab;
    onClick: (tab: AdminTab) => void;
    children: React.ReactNode;
  }> = ({ tabName, currentTab, onClick, children }) => (
    <button
      onClick={() => onClick(tabName)}
      className={`px-4 py-2 rounded-lg font-medium transition-colors duration-200 ${
        currentTab === tabName
          ? 'bg-blue-600 text-white shadow-md'
          : 'bg-white text-gray-600 hover:bg-gray-100'
      }`}
    >
      {children}
    </button>
  );

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return <AdminOverview />;
      case 'products':
        return <AdminProducts />;
      case 'analysis':
        return <ExtractionAnalysis />;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow-sm">
        <div className="max-w-screen-2xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <h1 className="text-2xl font-bold text-gray-800 flex items-center">
              <span className="text-3xl mr-2">🔧</span> Lambda.hu Admin Panel
            </h1>
            <div className="text-sm text-gray-500">
              PostgreSQL Viewer & Extraction Analyzer
            </div>
          </div>
        </div>
      </div>

      <main className="max-w-screen-2xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="mb-6">
          <nav className="flex space-x-2 p-1 bg-white rounded-lg shadow-sm w-min">
            <TabButton tabName="overview" currentTab={activeTab} onClick={setActiveTab}>
              📊 Áttekintés
            </TabButton>
            <TabButton tabName="products" currentTab={activeTab} onClick={setActiveTab}>
              📋 Termékek
            </TabButton>
            <TabButton tabName="analysis" currentTab={activeTab} onClick={setActiveTab}>
              🔬 Elemzés
            </TabButton>
          </nav>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow-md">
          {renderContent()}
        </div>
      </main>
    </div>
  );
};

export default AdminPanel; 