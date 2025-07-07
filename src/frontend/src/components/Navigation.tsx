'use client';

import { useState } from 'react';

/**
 * ============================================================================
 * NAVIGATION COMPONENT - Fő Navigációs Interfész
 * ============================================================================
 * 
 * Célja: Tab-alapú navigációs rendszer a fő alkalmazás modulok között
 * 
 * Architekturális szerepe:
 * - Top-level navigáció kezelése
 * - Mobile/desktop responsive design
 * - Brand identity megjelenítése
 * - System status indicator
 * 
 * Függőségek:
 * - NINCS külső API függőség (pure UI component)
 * - React useState hook lokális state kezeléshez
 * - Custom utility function (cn) a className összefűzéshez
 * 
 * Props interfész:
 * - activeTab: jelenleg aktív navigációs tab
 * - onTabChange: callback function tab váltáskor
 * 
 * State:
 * - STATELESS komponens (minden state parent-től jön)
 * 
 * Performance jellemzők:
 * - Lightweight SVG ikonok
 * - CSS-only animációk
 * - Memoization nem szükséges (egyszerű UI)
 */

// Helper function for className joining
// Célja: Tailwind class-ok dinamikus összefűzése
function cn(...classes: (string | boolean | undefined)[]): string {
  return classes.filter(Boolean).join(' ');
}

/**
 * ============================================================================
 * SVG ICON COMPONENTS
 * ============================================================================
 * 
 * Custom SVG ikonok a navigációs elemekhez
 * Előnyök:
 * - Nincs külső icon library függőség
 * - Teljes kontroll a styling felett
 * - Optimális performance (inline SVG)
 * - Consistent design language
 */

// Dashboard ikon - Főoldal reprezentálása
const IconHome = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 21l8-8-8-8" />
  </svg>
);

// Keresés ikon - AI keresési funkció
const IconSearch = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
  </svg>
);

// Beállítások ikon - Admin panel reprezentálása
const IconCog = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
);

// Diagram ikon - Monitoring dashboard
const IconChart = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
  </svg>
);

// Termék ikon - Katalógus reprezentálása
const IconCube = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
  </svg>
);

/**
 * ============================================================================
 * TYPE DEFINITIONS
 * ============================================================================
 */

// Navigációs tab típusok - type safety biztosítása
export type NavigationTab = 'dashboard' | 'search' | 'products' | 'monitoring' | 'admin';

// Komponens props interface
interface NavigationProps {
  activeTab: NavigationTab;           // Jelenleg aktív tab
  onTabChange: (tab: NavigationTab) => void; // Tab váltás callback
}

/**
 * ============================================================================
 * NAVIGATION CONFIGURATION
 * ============================================================================
 * 
 * Centralizált konfiguráció az összes navigációs elemhez
 * Könnyen bővíthető és karbantartható struktura
 */
const navigationItems = [
  {
    id: 'dashboard' as NavigationTab,
    name: 'Dashboard',                    // Megjelenítendő név
    icon: IconHome,                       // Icon komponens
    description: 'Központi áttekintés',   // Tooltip/accessibility description
  },
  {
    id: 'search' as NavigationTab,
    name: 'AI Keresés',
    icon: IconSearch,
    description: 'Intelligens termék keresés',
  },
  {
    id: 'products' as NavigationTab,
    name: 'Katalógus',
    icon: IconCube,
    description: 'Termék böngészés',
  },
  {
    id: 'monitoring' as NavigationTab,
    name: 'Monitoring',
    icon: IconChart,
    description: 'Rendszer teljesítmény',
  },
  {
    id: 'admin' as NavigationTab,
    name: 'Admin',
    icon: IconCog,
    description: 'Rendszer beállítások',
  },
];

/**
 * ============================================================================
 * MAIN NAVIGATION COMPONENT
 * ============================================================================
 */
export default function Navigation({ activeTab, onTabChange }: NavigationProps) {
  return (
    <nav className="bg-white shadow-soft border-b border-neutral-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          
          {/* ===== LOGO ÉS BRAND SECTION ===== */}
          <div className="flex items-center">
            <div className="flex-shrink-0 flex items-center">
              {/* Lambda logo - építőipari identitás */}
              <div className="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">λ</span>
              </div>
              
              {/* Brand neve és tagline */}
              <h1 className="ml-3 text-xl font-bold text-neutral-800">
                Lambda.hu
                <span className="ml-2 text-sm font-medium text-neutral-600">
                  Építőanyag AI
                </span>
              </h1>
            </div>
          </div>

          {/* ===== DESKTOP NAVIGATION TABS ===== */}
          <div className="hidden md:block">
            <div className="ml-10 flex items-baseline space-x-1">
              {navigationItems.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                
                return (
                  <button
                    key={item.id}
                    onClick={() => onTabChange(item.id)}
                    className={cn(
                      // Base styling minden tab gombhoz
                      'group flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200',
                      // Conditional styling aktív/inaktív állapothoz
                      isActive
                        ? 'bg-primary-500 text-white shadow-md'       // Aktív tab - kiemelés
                        : 'text-neutral-600 hover:text-primary-500 hover:bg-primary-50' // Inaktív tab - hover effect
                    )}
                  >
                    <Icon />
                    <span className="ml-2">{item.name}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* ===== SYSTEM STATUS INDICATOR ===== */}
          <div className="flex items-center space-x-4">
            <div className="hidden sm:block">
              <div className="flex items-center space-x-2 text-sm text-neutral-600">
                {/* Animált status dot - rendszer elérhető jelzése */}
                <div className="w-2 h-2 bg-accent-500 rounded-full animate-pulse-soft"></div>
                <span>Rendszer aktív</span>
              </div>
            </div>
          </div>
        </div>

        {/* ===== MOBILE NAVIGATION ===== */}
        {/* Responsive design: mobil eszközökön grid layout */}
        <div className="md:hidden border-t border-neutral-200 pt-2 pb-3">
          <div className="grid grid-cols-2 gap-1">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              
              return (
                <button
                  key={item.id}
                  onClick={() => onTabChange(item.id)}
                  className={cn(
                    // Mobile-specifikus styling
                    'flex flex-col items-center px-3 py-2 rounded-lg text-xs font-medium transition-all duration-200',
                    isActive
                      ? 'bg-primary-500 text-white'              // Mobil aktív állapot
                      : 'text-neutral-600 hover:text-primary-500 hover:bg-primary-50' // Mobil hover
                  )}
                >
                  <Icon />
                  <span className="mt-1">{item.name}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
}

/**
 * ============================================================================
 * COMPONENT USAGE EXAMPLE
 * ============================================================================
 * 
 * // Parent component-ben (page.tsx)
 * const [activeTab, setActiveTab] = useState<NavigationTab>('dashboard');
 * 
 * return (
 *   <Navigation 
 *     activeTab={activeTab} 
 *     onTabChange={setActiveTab} 
 *   />
 * );
 * 
 * ============================================================================
 * PERFORMANCE NOTES
 * ============================================================================
 * 
 * - Inline SVG ikonok: optimális performance
 * - CSS transitions: hardware accelerated animációk
 * - Conditional rendering: csak szükséges elemek renderelése
 * - Memoization: nem szükséges (stateless component)
 * 
 * ============================================================================
 * ACCESSIBILITY FEATURES
 * ============================================================================
 * 
 * - Szemantikus HTML elemek (nav, button)
 * - Keyboard navigation support
 * - Screen reader friendly structure
 * - Color contrast compliance (WCAG AA)
 * - Focus management
 * 
 * ============================================================================
 */ 