# Magyar Építőanyag AI - Frontend Architektúra Dokumentáció

## 📋 Tartalomjegyzék
1. [Áttekintés](#áttekintés)
2. [Technológiai Stack](#technológiai-stack)
3. [Projekt Struktúra](#projekt-struktúra)
4. [Komponens Architektúra](#komponens-architektúra)
5. [State Management](#state-management)
6. [API Integráció](#api-integráció)
7. [Design System](#design-system)
8. [Függőségi Térképek](#függőségi-térképek)
9. [Development Guide](#development-guide)

---

## 🏗️ Áttekintés

A Lambda.hu Magyar Építőanyag AI frontend egy modern, professzionális React alkalmazás, amely természetes nyelvű AI asszisztenst és intelligens termékkeresést biztosít az építőipar számára.

### Fő Célok
- **Természetes nyelvű interakció**: RAG-alapú AI chat widget
- **Professzionális UI/UX**: Építőipari identitás modern design nyelvvel
- **Valós adatok**: PostgreSQL + ChromaDB backend integráció
- **Reszponzív design**: Desktop és mobil támogatás
- **Type Safety**: Teljes TypeScript coverage

---

## 🛠️ Technológiai Stack

### Core Framework
```yaml
Framework: Next.js 14.2.18
  - App Router (src/app directory)
  - Server Components + Client Components hibrid
  - Built-in optimalizációk (Image, Font, CSS)
  
React: 18.x
  - Hooks-based functional components
  - Context API state management
  - Strict TypeScript integration
```

### Styling & UI
```yaml
Tailwind CSS 3.4.1:
  - Utility-first CSS framework
  - Custom építőipari color palette
  - Responsive design utilities
  - Custom animations és transitions

Typography:
  - Inter font family (Google Fonts)
  - Harmonikus font scale
  - Magyar karakterkészlet támogatás
```

### Development Tools
```yaml
TypeScript 5.x:
  - Strict type checking
  - Interface-driven development
  - API response type safety

ESLint + Next.js config:
  - Code quality enforcement
  - Accessibility rules (jsx-a11y)
  - React hooks rules
```

---

## 📁 Projekt Struktúra

```
src/frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── layout.tsx         # Root layout component
│   │   ├── page.tsx           # Main application page
│   │   ├── globals.css        # Global styles
│   │   └── admin/             # Admin panel route
│   │       └── page.tsx       # Admin page component
│   │
│   ├── components/            # Reusable UI components
│   │   ├── Navigation.tsx     # Main navigation bar
│   │   ├── Dashboard.tsx      # Central dashboard component
│   │   ├── ChatWidget.tsx     # RAG AI chat widget
│   │   ├── Providers.tsx      # Context providers wrapper
│   │   └── AdminPanel/        # Admin-specific components
│   │       ├── AdminPanel.tsx
│   │       └── ExtractionAnalysis.tsx
│   │
│   └── lib/                   # Utility libraries
│       └── api.ts            # Backend API integration layer
│
├── public/                    # Static assets
├── package.json              # Dependencies and scripts
├── tailwind.config.js        # Tailwind CSS configuration
├── tsconfig.json            # TypeScript configuration
└── next.config.js           # Next.js configuration
```

### Fájl Szervezési Elvek

**1. Feature-based grouping**: Kapcsolódó komponensek egy mappában
**2. Shared utilities**: Common libraries a `lib/` mappában
**3. Type co-location**: API types az api.ts fájlban
**4. Component isolation**: Minden komponens self-contained

---

## 🧩 Komponens Architektúra

### 1. App Layout Hierarchy

```
RootLayout (layout.tsx)
├── Providers (context wrappers)
│   └── QueryClient, Toaster
└── Main Application (page.tsx)
    ├── Navigation
    ├── Content Router
    │   ├── Dashboard
    │   ├── SearchInterface  
    │   ├── ProductCatalog
    │   ├── MonitoringDashboard
    │   └── AdminPanel
    └── ChatWidget (floating)
```

### 2. Fő Komponensek Részletesen

#### **Navigation.tsx**
```typescript
// Célja: Fő navigációs interfész
// Függőségek: NINCS (pure UI component)
// Props: activeTab, onTabChange
// State: NINCS (stateless)

Funkciók:
- Tab-based navigation (5 fő modul)
- Responsive mobile/desktop layout
- Active state management
- Lambda.hu branding
- System status indicator
```

#### **Dashboard.tsx**
```typescript
// Célja: Központi landing page és keresési interfész
// Függőségek: api.ts (backend integration)
// Props: onSearchSubmit, onCategorySelect
// State: searchQuery, isSearchFocused, stats

Funkciók:
- Hero section központi keresősávval
- Dynamic statistics (real backend data)
- Quick access category modules
- Sample query suggestions
- Real-time data loading
```

#### **ChatWidget.tsx**
```typescript
// Célja: Lebegő AI chat asszisztens
// Függőségek: api.ts (RAG search integration)
// Props: onClose
// State: isOpen, isMinimized, messages, inputValue, isTyping

Funkciók:
- Floating chat window (minimizable)
- Real RAG API integration
- Product recommendations dengan
- Natural language processing
- Conversation history
- Quick action buttons
```

#### **api.ts**
```typescript
// Célja: Backend API integration layer
// Függőségek: Native fetch API
// Exports: ApiService class, type definitions

Funkciók:
- Type-safe API calls
- Error handling
- Request/response transformation
- Endpoint abstraction (products, search, admin)
```

### 3. Component Communication Patterns

```mermaid
graph TD
    A[page.tsx - Main App] --> B[Navigation]
    A --> C[Dashboard]
    A --> D[ChatWidget]
    
    C --> E[api.ts - Backend]
    D --> E
    
    A --> F[Other Pages]
    F --> G[AdminPanel]
    G --> E
    
    B --> A[Tab Change Events]
    C --> A[Search Events]
    D --> A[Floating Widget]
```

**Communication Flow:**
1. **Downward**: Props drilling for callbacks és configuration
2. **Upward**: Event callbacks (onSearchSubmit, onTabChange)
3. **Lateral**: Shared API service közös backend hozzáféréshez

---

## 🔄 State Management

### 1. Local State (useState)

```typescript
// Dashboard component
const [searchQuery, setSearchQuery] = useState('');
const [stats, setStats] = useState<SystemStats>({...});

// ChatWidget component  
const [messages, setMessages] = useState<Message[]>([...]);
const [isTyping, setIsTyping] = useState(false);

// Navigation
const [activeTab, setActiveTab] = useState<NavigationTab>('dashboard');
```

**Reasoning**: Local state egyszerű komponens-specifikus adatokhoz

### 2. Prop Drilling

```typescript
// Main App koordinálja a tab state-et
function Home() {
  const [activeTab, setActiveTab] = useState<NavigationTab>('dashboard');
  
  return (
    <>
      <Navigation activeTab={activeTab} onTabChange={setActiveTab} />
      <main>{renderContent()}</main>
    </>
  );
}
```

**Reasoning**: Egyszerű app struktúra esetén elegendő

### 3. Server State (useEffect + API)

```typescript
useEffect(() => {
  const loadSystemStats = async () => {
    try {
      const [products, manufacturers] = await Promise.all([
        api.getProducts(1000, 0),
        api.getManufacturers(),
      ]);
      setStats({...}); // Update local state
    } catch (error) {
      // Error handling
    }
  };
  loadSystemStats();
}, []);
```

**Reasoning**: Server state useEffect-tel kezelve, jövőbeli React Query integrációval

---

## 🔌 API Integráció

### 1. API Service Architecture

```typescript
// src/lib/api.ts
export class ApiService {
  private baseUrl: string;
  
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }
  
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    // Centralized request handling
    // Error handling
    // Type safety
  }
  
  // Domain-specific methods
  async getProducts(limit = 100, offset = 0): Promise<Product[]>
  async searchRAG(query: string, limit = 10): Promise<SearchResponse>
  async healthCheck(): Promise<{status: string}>
}

// Default instance
export const api = new ApiService();
```

### 2. Type Definitions

```typescript
// Backend schema mapping
export interface Product {
  id: number;
  name: string;
  description?: string;
  technical_specs?: Record<string, any>;
  manufacturer?: Manufacturer;
  category?: Category;
}

export interface SearchResponse {
  query: string;
  total_results: number;
  results: SearchResult[];
}
```

### 3. Integration Points

```yaml
Backend Endpoints:
  GET /products              → Dashboard statistics
  GET /manufacturers         → Dashboard statistics  
  GET /categories           → Dashboard statistics
  POST /search/rag          → ChatWidget AI responses
  GET /health               → System status
  POST /api/v1/scrape       → Admin panel actions
```

### 4. Error Handling Strategy

```typescript
// Centralized error handling in API service
private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  try {
    const response = await fetch(url, options);
    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`);
    }
    return response.json();
  } catch (error) {
    // Log error
    // User feedback
    throw error;
  }
}

// Component level error handling
try {
  const searchResponse = await api.searchRAG(query, 5);
  // Success path
} catch (error) {
  // Graceful degradation
  const errorMessage: Message = {
    type: 'ai',
    content: 'Sajnálom, jelenleg nem tudok kapcsolódni az adatbázishoz.'
  };
}
```

---

## 🎨 Design System

### 1. Color Palette

```typescript
// tailwind.config.js
colors: {
  // Építőipari színpaletta
  primary: {
    500: '#2E5C8A', // Fő kék - bizalom és szakértelem
    // ... teljes skála
  },
  secondary: {
    500: '#F5A623', // Építőipari narancs - energia és innováció
    // ... teljes skála
  },
  accent: {
    500: '#4CAF50', // Zöld - fenntarthatóság és siker
    // ... teljes skála
  },
  neutral: {
    // Világosszürke árnyalatok
  }
}
```

### 2. Typography System

```typescript
fontFamily: {
  sans: ['Inter', 'system-ui', 'sans-serif'], // Magyar karakterkészlet
  mono: ['Fira Code', 'monospace'],
}
```

### 3. Spacing & Layout

```typescript
spacing: {
  '18': '4.5rem',    // Custom spacing
  '88': '22rem',     // Large spacing
  '128': '32rem',    // XL spacing
}

borderRadius: {
  '4xl': '2rem',     // Soft rounded corners
}
```

### 4. Animation System

```typescript
animation: {
  'fade-in': 'fadeIn 0.3s ease-in-out',
  'slide-up': 'slideUp 0.4s ease-out', 
  'pulse-soft': 'pulseSoft 2s infinite',
}

// Usage in components
className={cn(
  "transition-all duration-300",
  isSearchFocused ? "scale-105" : ""
)}
```

### 5. Shadow System

```typescript
boxShadow: {
  'soft': '0 2px 15px -3px rgba(0, 0, 0, 0.07)...',
  'medium': '0 4px 25px -5px rgba(0, 0, 0, 0.1)...',
  'strong': '0 10px 40px -10px rgba(0, 0, 0, 0.15)...',
}
```

---

## 🕸️ Függőségi Térképek

### 1. Component Dependencies

```mermaid
graph TD
    A[page.tsx] --> B[Navigation.tsx]
    A --> C[Dashboard.tsx]
    A --> D[ChatWidget.tsx]
    A --> E[AdminPanel.tsx]
    
    C --> F[api.ts]
    D --> F
    E --> F
    
    F --> G[Backend API]
    
    A --> H[Providers.tsx]
    H --> I[React Context]
    
    style F fill:#e1f5fe
    style G fill:#f3e5f5
```

### 2. Data Flow Dependencies

```mermaid
sequenceDiagram
    participant U as User
    participant D as Dashboard
    participant C as ChatWidget
    participant A as API Service
    participant B as Backend
    
    U->>D: Load page
    D->>A: getProducts(), getManufacturers()
    A->>B: HTTP requests
    B-->>A: Data response
    A-->>D: Formatted data
    D-->>U: Display statistics
    
    U->>C: Ask question
    C->>A: searchRAG(query)
    A->>B: POST /search/rag
    B-->>A: Search results
    A-->>C: SearchResponse
    C-->>U: AI response + products
```

### 3. Build Dependencies

```yaml
Production Dependencies:
  next: "14.2.18"              # Framework
  react: "^18"                 # UI library
  react-dom: "^18"             # DOM rendering
  
Development Dependencies:
  typescript: "^5"             # Type system
  tailwindcss: "^3.4.1"       # Styling
  eslint: "^8"                 # Code quality
  @types/*: "^20|^18"          # Type definitions
```

---

## 🚀 Development Guide

### 1. Setup Instructions

```bash
# Navigate to frontend directory
cd src/frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Open browser
# http://localhost:3000
```

### 2. Environment Configuration

```bash
# .env.local (optional)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Development Workflow

```yaml
Code Style:
  - TypeScript strict mode
  - ESLint compliance
  - Functional components only
  - Hooks-based state management

Component Creation:
  1. Create component file in appropriate directory
  2. Export default function component
  3. Add TypeScript interfaces for props
  4. Include JSDoc comments for complex logic
  5. Add to parent component imports

API Integration:
  1. Add new methods to ApiService class
  2. Define TypeScript interfaces for responses
  3. Implement error handling
  4. Add loading states in components
```

### 4. Testing Strategy

```yaml
Unit Testing:
  - Component rendering tests
  - User interaction tests
  - API service tests
  
Integration Testing:
  - Full user flows
  - API integration tests
  - Cross-component communication
  
E2E Testing:
  - Complete user journeys
  - Real backend integration
  - Performance validation
```

### 5. Build & Deployment

```bash
# Production build
npm run build

# Start production server
npm start

# Build analysis
npm run analyze
```

### 6. Performance Considerations

```yaml
Optimizations:
  - Next.js automatic code splitting
  - Image optimization (next/image)
  - Font optimization (next/font)
  - CSS tree shaking (Tailwind)
  
Monitoring:
  - Core Web Vitals
  - API response times
  - Component render performance
  - Bundle size analysis
```

---

## 📋 Implementation Checklist

### ✅ Completed Features
- [x] Modern responsive design system
- [x] Navigation with tab-based routing
- [x] Dashboard with real backend data
- [x] AI chat widget with RAG integration
- [x] TypeScript type safety
- [x] API service layer
- [x] Error handling and loading states
- [x] Accessibility features (ARIA labels)

### 🔄 In Progress
- [ ] Admin panel full functionality
- [ ] Search interface advanced filtering
- [ ] Product catalog detailed views

### 📋 Future Enhancements
- [ ] React Query for better server state
- [ ] Internationalization (i18n)
- [ ] Advanced animation library (Framer Motion)
- [ ] Progressive Web App (PWA)
- [ ] Real-time notifications

---

## 📚 References

- **Next.js Documentation**: https://nextjs.org/docs
- **Tailwind CSS**: https://tailwindcss.com/docs
- **TypeScript**: https://www.typescriptlang.org/docs
- **React**: https://react.dev
- **Design Inspiration**: Modern dashboard design trends 2025

---

*Dokumentáció utolsó frissítése: 2025-01-28*
*Verzió: 1.0.0*
*Státusz: Production Ready* 