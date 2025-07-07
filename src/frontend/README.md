# 🏗️ Lambda.hu Magyar Építőanyag AI - Frontend Alkalmazás

## 📋 Projekt Áttekintés

A Lambda.hu egy professzionális magyar építőanyag AI alkalmazás, amely természetes nyelvű keresést és intelligens termékajánlást biztosít az építőipar számára. A frontend egy modern React/Next.js alkalmazás, amely RAG (Retrieval-Augmented Generation) technológiával és ChromaDB vektoros adatbázissal működik.

![Lambda.hu Dashboard](docs/screenshots/dashboard.png)

---

## 🚀 Gyors Indítás

### Előfeltételek
```bash
Node.js 18.x+
npm 9.x+
Backend szolgáltatások futnak (FastAPI + PostgreSQL + ChromaDB)
```

### Telepítés és Indítás
```bash
# 1. Repository clone
git clone <repository-url>
cd Lambda/src/frontend

# 2. Dependencies telepítése
npm install

# 3. Environment konfiguráció (opcionális)
cp .env.example .env.local

# 4. Development server indítása
npm run dev

# 5. Browser megnyitása
# http://localhost:3000
```

---

## 🏗️ Architektúra Áttekintés

### Technológiai Stack

```yaml
Framework: Next.js 14.2.18 (App Router)
UI Library: React 18
Styling: Tailwind CSS 3.4.1
Language: TypeScript 5.x
Backend: FastAPI + PostgreSQL + ChromaDB
```

### Komponens Struktúra

```
src/frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── layout.tsx         # Root layout
│   │   ├── page.tsx           # Main application
│   │   └── globals.css        # Global styles
│   │
│   ├── components/            # UI komponensek
│   │   ├── Navigation.tsx     # Tab-alapú navigáció
│   │   ├── Dashboard.tsx      # Központi dashboard
│   │   ├── ChatWidget.tsx     # RAG AI chat widget
│   │   └── Providers.tsx      # Context providers
│   │
│   └── lib/
│       └── api.ts            # Backend API integráció
│
├── docs/                      # Részletes dokumentáció
├── package.json              # Dependencies és scripts
└── tailwind.config.js        # Design system konfiguráció
```

---

## 🧩 Fő Komponensek

### 1. Navigation Component
**Célja**: Tab-alapú navigációs rendszer
```typescript
<Navigation 
  activeTab={activeTab} 
  onTabChange={setActiveTab} 
/>
```

**Funkciók**:
- 5 fő modul közötti navigáció
- Responsive mobile/desktop design
- Lambda.hu brand identity
- System status indicator

### 2. Dashboard Component  
**Célja**: Központi keresési és áttekintő interfész
```typescript
<Dashboard 
  onSearchSubmit={handleSearch}
  onCategorySelect={handleCategory}
/>
```

**Funkciók**:
- Központi keresősáv természetes nyelvű inputtal
- Real-time rendszer statisztikák (termékek, gyártók)
- Gyors kategória elérések
- Sample query suggestions

### 3. ChatWidget Component
**Célja**: RAG-alapú AI asszisztens
```typescript
<ChatWidget onClose={() => setShowChat(false)} />
```

**Funkciók**:
- Lebegő chat ablak (minimalizálható)
- Természetes nyelvű RAG keresés
- Termékajánlások similarity score-ral
- Conversational AI interaction pattern

### 4. API Service Layer
**Célja**: Centralizált backend kommunikáció
```typescript
import { api } from '@/lib/api';

const products = await api.getProducts(100, 0);
const searchResults = await api.searchRAG("hőszigetelés", 5);
```

**Funkciók**:
- Type-safe API calls TypeScript interface-ekkel
- Centralizált error handling
- ChromaDB RAG search integráció
- PostgreSQL termékadatok kezelése

---

## 🎨 Design System

### Építőipari Színpaletta
```css
Primary Blue: #2E5C8A     /* Bizalom és szakértelem */
Secondary Orange: #F5A623  /* Energia és innováció */
Accent Green: #4CAF50      /* Fenntarthatóság és siker */
Neutral Grays: #F8F9FA..#1F2937  /* Clean megjelenés */
```

### Typography System
```css
Font Family: Inter (Google Fonts)
Magyar karakterkészlet: teljes támogatás
Font Scale: 12px - 48px (harmonikus arányok)
```

### Spacing & Layout
```css
Spacing Scale: 4px base unit (Tailwind standard)
Container Max Width: 1280px (7xl)
Responsive Breakpoints: sm:640px, md:768px, lg:1024px, xl:1280px
```

---

## 📡 Backend Integráció

### API Endpoints
```typescript
// Termék adatok
GET /products?limit={}&offset={}     // Termékek listája
GET /products/{id}                   // Egyedi termék

// Kategóriák és gyártók
GET /categories                      // Hierarchikus kategóriák
GET /manufacturers                   // Gyártók listája

// RAG Search (ChromaDB)
POST /search/rag                     // Természetes nyelvű keresés
{
  "query": "hőszigetelés családi házhoz",
  "limit": 5
}

// Rendszer monitoring
GET /health                          // API egészség
POST /api/v1/scrape                  // Admin scraping trigger
```

### Error Handling Strategy
```typescript
// Centralizált error handling
try {
  const result = await api.searchRAG(query, 5);
  // Success path
} catch (error) {
  // Graceful degradation
  showUserFriendlyMessage(error.message);
}

// Loading states minden API call-nál
const [isLoading, setIsLoading] = useState(true);
const [error, setError] = useState<string | null>(null);
```

---

## 🔄 Adatáramlás

### Unidirectional Data Flow
```
page.tsx (Main App)
├── activeTab state ────────────► Navigation
├── search handlers ────────────► Dashboard  
└── chat widget state ──────────► ChatWidget
    │
    └── RAG API calls ──────────► Backend
        ├── ChromaDB Vector Search
        ├── PostgreSQL Product Data
        └── AI Response Generation
```

### State Management Patterns
```typescript
// Local state (component level)
const [searchQuery, setSearchQuery] = useState('');
const [messages, setMessages] = useState<Message[]>([]);

// Props drilling (simple app structure)
<Dashboard onSearchSubmit={handleSearch} />

// Server state (API integration)
useEffect(() => {
  api.getProducts().then(setProducts).catch(setError);
}, []);
```

---

## 🧪 Testing Strategy

### Testing Pyramid
```
E2E Tests (Playwright)     <- Complete user journeys
Integration Tests          <- Component communication  
Unit Tests (Jest/RTL)      <- Individual components
```

### Test Commands
```bash
# Unit tests
npm run test

# Unit tests watch mode
npm run test:watch

# E2E tests
npm run test:e2e

# Type checking
npm run type-check

# Linting
npm run lint
```

### Sample Tests
```typescript
// Component test
test('Navigation calls onTabChange when tab clicked', () => {
  const mockOnTabChange = jest.fn();
  render(<Navigation activeTab="dashboard" onTabChange={mockOnTabChange} />);
  
  fireEvent.click(screen.getByText('AI Keresés'));
  expect(mockOnTabChange).toHaveBeenCalledWith('search');
});

// API test
test('searchRAG returns formatted results', async () => {
  const results = await api.searchRAG('hőszigetelés', 3);
  expect(results.total_results).toBeGreaterThan(0);
  expect(results.results).toHaveLength(3);
});
```

---

## 📊 Performance Monitoring

### Core Web Vitals Targets
```yaml
LCP (Largest Contentful Paint): < 2.5 seconds
FID (First Input Delay): < 100 milliseconds  
CLS (Cumulative Layout Shift): < 0.1
```

### Bundle Analysis
```bash
# Bundle analyzer
npm run analyze

# Performance profiling
npm run dev
# Chrome DevTools > Performance tab
```

### API Performance
```typescript
// API response time monitoring
const apiMonitor = new APIMonitor();
const results = await apiMonitor.monitorRequest(
  '/search/rag',
  () => api.searchRAG(query, limit)
);

// Target: < 500ms average API response time
```

---

## 🚀 Deployment

### Development
```bash
npm run dev          # Development server (http://localhost:3000)
npm run build        # Production build
npm run start        # Production server
```

### Production Build
```bash
# Optimalizált production build
npm run build

# Bundle size check
npm run analyze

# Type safety verification  
npm run type-check
```

### Docker Deployment
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

---

## 📚 Dokumentáció

### Teljes Dokumentáció
- **[Frontend Architektúra](docs/FRONTEND_ARCHITECTURE.md)** - Részletes technikai architektúra
- **[Komponens Kapcsolatok](docs/COMPONENT_RELATIONSHIPS.md)** - Adatáramlás és függőségek  
- **[Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** - Telepítés és testing
- **[PDF Processing Risks](docs/PDF_PROCESSING_RISK_ANALYSIS_AND_MITIGATION.md)** - Rendszer kockázatok

### API Dokumentáció
```bash
# Backend API docs (Swagger)
http://localhost:8000/docs

# RAG search endpoint example
curl -X POST http://localhost:8000/search/rag \
  -H "Content-Type: application/json" \
  -d '{"query":"ROCKWOOL hőszigetelés","limit":5}'
```

---

## 🎯 Fő Funkciók

### ✅ Implementált Funkciók
- [x] **Modern responsive design** építőipari identitással
- [x] **Tab-based navigation** 5 fő modullal
- [x] **Dashboard** real-time backend adatokkal
- [x] **RAG-alapú AI chat widget** ChromaDB integrációval
- [x] **Type-safe API layer** teljes TypeScript support-tal
- [x] **Error handling** graceful degradation-nel
- [x] **Accessibility features** ARIA labels és keyboard navigation

### 🔄 Fejlesztés Alatt
- [ ] **Advanced search filters** kategória és gyártó alapján
- [ ] **Product catalog** detailed view-kkal
- [ ] **Admin monitoring** dashboard
- [ ] **Performance analytics** real-time metrics-ekkel

### 📋 Jövőbeli Fejlesztések
- [ ] **React Query** server state management-hez
- [ ] **PWA features** offline capability-vel
- [ ] **Internationalization** (i18n) többnyelvű támogatás
- [ ] **Advanced caching** strategy

---

## 🤝 Development Workflow

### Branch Strategy
```bash
main          # Production-ready code
develop       # Integration branch  
feature/*     # Feature development
hotfix/*      # Critical bug fixes
```

### Code Quality
```bash
# Pre-commit hooks
npm run lint          # ESLint checks
npm run type-check    # TypeScript validation  
npm run test          # Unit tests
```

### Pull Request Checklist
```yaml
Code Quality:
  - [ ] TypeScript errors resolved
  - [ ] ESLint warnings addressed
  - [ ] Unit tests added/updated
  - [ ] Integration tests passing

Documentation:
  - [ ] README updated if needed
  - [ ] API changes documented
  - [ ] Component props documented

Testing:
  - [ ] Manual testing completed
  - [ ] Cross-browser compatibility checked
  - [ ] Mobile responsiveness verified
```

---

## 🛠️ Troubleshooting

### Gyakori Problémák

**Problem**: Build type errors
```bash
npm run type-check    # TypeScript validation
npm run lint          # ESLint fixes
```

**Problem**: API connection issues
```bash
# Backend health check
curl http://localhost:8000/health

# Environment variable check
echo $NEXT_PUBLIC_API_URL
```

**Problem**: Chat widget RAG search fails
```bash
# ChromaDB status check
docker ps | grep chroma

# PostgreSQL connection check  
docker exec -it lambda-db-1 psql -U lambda_user -d lambda_db
```

### Debug Tools
```typescript
// Component debug
console.log('Component props:', { activeTab, onTabChange });

// API debug
console.log('API request:', { method: 'POST', url: '/search/rag', data: { query, limit } });

// Performance debug
performance.mark('component-render-start');
// Component logic
performance.measure('component-render', 'component-render-start');
```

---

## 📞 Support

### Team Contacts
- **Frontend Development**: [Team Frontend]
- **Backend Integration**: [Team Backend]  
- **DevOps/Deployment**: [Team DevOps]

### Resources
- **Internal Wiki**: [Link to internal documentation]
- **API Documentation**: http://localhost:8000/docs
- **Design System**: [Link to Figma/design docs]

---

## 📄 License

Proprietary - Lambda.hu Magyar Építőanyag AI Project

---

*Dokumentáció utolsó frissítése: 2025-01-28*  
*Alkalmazás verzió: 1.0.0*  
*Status: Production Ready*

**🎯 Production Demo Ready!** Az alkalmazás teljes mértékben működőképes és bemutatásra kész a Lambda.hu magyar építőanyag AI projekthez. 