# Lambda.hu Magyar Építőanyag AI - Deployment és Testing Guide

## 📋 Tartalomjegyzék
1. [Development Environment](#development-environment)
2. [Production Build](#production-build)
3. [Testing Strategy](#testing-strategy)
4. [Performance Monitoring](#performance-monitoring)
5. [Troubleshooting](#troubleshooting)

---

## 🛠️ Development Environment

### Előfeltételek
```bash
Node.js: 18.x vagy újabb
npm: 9.x vagy újabb
Git: 2.x
```

### Setup Lépések

#### 1. Repository Clone és Dependencies
```bash
# Repository cloning
git clone <repository-url>
cd Lambda/src/frontend

# Dependencies telepítése
npm install

# TypeScript és ESLint ellenőrzés
npm run lint
npm run type-check
```

#### 2. Environment Configuration
```bash
# .env.local fájl létrehozása (opcionális)
NEXT_PUBLIC_API_URL=http://localhost:8000
NODE_ENV=development
```

#### 3. Development Server
```bash
# Development server indítása
npm run dev

# Browser megnyitása
# http://localhost:3000
```

#### 4. Backend Service Verification
```bash
# Backend server ellenőrzése
curl http://localhost:8000/health

# PostgreSQL kapcsolat
curl http://localhost:8000/products?limit=5

# ChromaDB RAG search
curl -X POST http://localhost:8000/search/rag \
  -H "Content-Type: application/json" \
  -d '{"query":"hőszigetelés","limit":3}'
```

---

## 🏗️ Production Build

### Build Process

#### 1. Production Build Létrehozása
```bash
# Clean build
rm -rf .next
npm run build

# Build analysis (opcionális)
npm run analyze
```

#### 2. Production Server
```bash
# Production mode indítás
npm start

# Port: 3000 (alapértelmezett)
```

#### 3. Docker Deployment

```dockerfile
# Dockerfile optimizations
FROM node:18-alpine AS base

# Dependencies
FROM base AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

# Builder
FROM base AS builder  
WORKDIR /app
COPY . .
COPY --from=deps /app/node_modules ./node_modules
RUN npm run build

# Runtime
FROM base AS runner
WORKDIR /app
ENV NODE_ENV production

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]
```

#### 4. Environment Variables (Production)
```bash
# .env.production
NEXT_PUBLIC_API_URL=https://api.lambda.hu
NODE_ENV=production
NEXTAUTH_SECRET=<secure-secret>
```

---

## 🧪 Testing Strategy

### Testing Pyramid

```
        /\
       /  \
      / E2E \         <- Comprehensive user journeys
     /______\
    /        \
   /Integration\      <- Component communication
  /__________\
 /            \
/   Unit Tests  \     <- Individual component logic
\______________/
```

### 1. Unit Testing

#### Component Testing Setup
```bash
# Testing dependencies telepítése
npm install --save-dev @testing-library/react @testing-library/jest-dom jest-environment-jsdom
```

#### Sample Component Test
```typescript
// __tests__/components/Navigation.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import Navigation, { NavigationTab } from '@/components/Navigation';

describe('Navigation Component', () => {
  const mockOnTabChange = jest.fn();
  
  beforeEach(() => {
    mockOnTabChange.mockClear();
  });

  test('renders all navigation tabs', () => {
    render(
      <Navigation activeTab="dashboard" onTabChange={mockOnTabChange} />
    );
    
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('AI Keresés')).toBeInTheDocument();
    expect(screen.getByText('Katalógus')).toBeInTheDocument();
  });

  test('calls onTabChange when tab is clicked', () => {
    render(
      <Navigation activeTab="dashboard" onTabChange={mockOnTabChange} />
    );
    
    fireEvent.click(screen.getByText('AI Keresés'));
    expect(mockOnTabChange).toHaveBeenCalledWith('search');
  });

  test('highlights active tab correctly', () => {
    render(
      <Navigation activeTab="search" onTabChange={mockOnTabChange} />
    );
    
    const activeTab = screen.getByText('AI Keresés').closest('button');
    expect(activeTab).toHaveClass('bg-primary-500');
  });
});
```

#### API Service Testing
```typescript
// __tests__/lib/api.test.ts
import { ApiService } from '@/lib/api';

// Mock fetch
global.fetch = jest.fn();

describe('ApiService', () => {
  let apiService: ApiService;
  
  beforeEach(() => {
    apiService = new ApiService('http://test-api.com');
    (fetch as jest.Mock).mockClear();
  });

  test('getProducts returns product array', async () => {
    const mockProducts = [
      { id: 1, name: 'Test Product', description: 'Test Description' }
    ];
    
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockProducts,
    });

    const products = await apiService.getProducts(10, 0);
    
    expect(fetch).toHaveBeenCalledWith(
      'http://test-api.com/products?limit=10&offset=0',
      expect.any(Object)
    );
    expect(products).toEqual(mockProducts);
  });

  test('handles API errors gracefully', async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      statusText: 'Not Found',
    });

    await expect(apiService.getProducts()).rejects.toThrow('API request failed: Not Found');
  });
});
```

### 2. Integration Testing

#### Component Integration Test
```typescript
// __tests__/integration/Dashboard.integration.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import Dashboard from '@/components/Dashboard';
import { api } from '@/lib/api';

// Mock API service
jest.mock('@/lib/api');
const mockedApi = api as jest.Mocked<typeof api>;

describe('Dashboard Integration', () => {
  test('loads and displays system statistics', async () => {
    // Mock API responses
    mockedApi.getProducts.mockResolvedValue([
      { id: 1, name: 'Product 1' },
      { id: 2, name: 'Product 2' },
    ] as any);
    
    mockedApi.getManufacturers.mockResolvedValue([
      { id: 1, name: 'ROCKWOOL' },
    ] as any);

    render(<Dashboard onSearchSubmit={jest.fn()} />);

    // Check loading state
    expect(screen.getByText(/betöltés/i)).toBeInTheDocument();

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('2')).toBeInTheDocument(); // Product count
      expect(screen.getByText('1')).toBeInTheDocument(); // Manufacturer count
    });

    // Verify API was called
    expect(mockedApi.getProducts).toHaveBeenCalledWith(1000, 0);
    expect(mockedApi.getManufacturers).toHaveBeenCalled();
  });
});
```

### 3. E2E Testing

#### Playwright Setup
```bash
# Playwright telepítése
npm init playwright@latest

# E2E test futtatás
npx playwright test
```

#### E2E Test Sample
```typescript
// e2e/search-flow.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Search Flow', () => {
  test('complete RAG search flow', async ({ page }) => {
    // Navigate to application
    await page.goto('http://localhost:3000');
    
    // Verify initial load
    await expect(page.locator('h1')).toContainText('Lambda.hu');
    
    // Open chat widget
    await page.click('[aria-label="AI chat megnyitása"]');
    await expect(page.locator('.chat-widget')).toBeVisible();
    
    // Type search query
    await page.fill('input[placeholder="Írj üzenetet..."]', 'hőszigetelés családi házhoz');
    await page.click('button[type="submit"]');
    
    // Wait for AI response
    await page.waitForSelector('.ai-message', { timeout: 10000 });
    
    // Verify response contains products
    await expect(page.locator('.product-card')).toHaveCount(3);
    
    // Test product card interaction
    await page.click('.product-card button:has-text("Részletek")');
    
    // Verify navigation
    await expect(page).toHaveURL(/products\/\d+\/view/);
  });

  test('dashboard statistics load correctly', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Wait for statistics to load
    await page.waitForSelector('[data-testid="product-count"]');
    
    // Verify statistics are numbers
    const productCount = await page.textContent('[data-testid="product-count"]');
    expect(Number(productCount)).toBeGreaterThan(0);
    
    const manufacturerCount = await page.textContent('[data-testid="manufacturer-count"]');
    expect(Number(manufacturerCount)).toBeGreaterThan(0);
  });
});
```

---

## 📊 Performance Monitoring

### Core Web Vitals Tracking

#### 1. Performance Metrics Setup
```typescript
// lib/performance.ts
export function trackWebVitals(metric: any) {
  switch (metric.name) {
    case 'CLS':
      console.log('Cumulative Layout Shift:', metric.value);
      break;
    case 'FID':
      console.log('First Input Delay:', metric.value);
      break;
    case 'FCP':
      console.log('First Contentful Paint:', metric.value);
      break;
    case 'LCP':
      console.log('Largest Contentful Paint:', metric.value);
      break;
    case 'TTFB':
      console.log('Time to First Byte:', metric.value);
      break;
    default:
      break;
  }
  
  // Send to analytics (future enhancement)
  // analytics.track('web-vital', metric);
}
```

#### 2. Bundle Analysis
```bash
# Bundle analyzer
npm run analyze

# Bundle size limits
next.config.js:
module.exports = {
  experimental: {
    bundlePagesRouterDependencies: true,
  },
  webpack: (config) => {
    config.optimization.splitChunks.cacheGroups.vendor = {
      test: /[\\/]node_modules[\\/]/,
      chunks: 'all',
      enforce: true,
    };
    return config;
  },
};
```

#### 3. API Performance Monitoring
```typescript
// lib/api-monitor.ts
class APIMonitor {
  private metrics: Map<string, number[]> = new Map();
  
  async monitorRequest<T>(
    endpoint: string, 
    requestFn: () => Promise<T>
  ): Promise<T> {
    const startTime = performance.now();
    
    try {
      const result = await requestFn();
      const endTime = performance.now();
      const duration = endTime - startTime;
      
      this.recordMetric(endpoint, duration);
      
      if (duration > 2000) { // Slow request threshold
        console.warn(`Slow API request: ${endpoint} took ${duration}ms`);
      }
      
      return result;
    } catch (error) {
      const endTime = performance.now();
      const duration = endTime - startTime;
      
      console.error(`API request failed: ${endpoint} (${duration}ms)`, error);
      throw error;
    }
  }
  
  private recordMetric(endpoint: string, duration: number) {
    if (!this.metrics.has(endpoint)) {
      this.metrics.set(endpoint, []);
    }
    
    const metrics = this.metrics.get(endpoint)!;
    metrics.push(duration);
    
    // Keep only last 100 measurements
    if (metrics.length > 100) {
      metrics.shift();
    }
  }
  
  getAverageResponseTime(endpoint: string): number {
    const metrics = this.metrics.get(endpoint) || [];
    if (metrics.length === 0) return 0;
    
    return metrics.reduce((sum, time) => sum + time, 0) / metrics.length;
  }
}

export const apiMonitor = new APIMonitor();
```

---

## 🚨 Troubleshooting

### Gyakori Problémák és Megoldások

#### 1. Build Errors

**Problem**: TypeScript type errors
```bash
Error: Type 'string | undefined' is not assignable to type 'string'
```

**Solution**:
```typescript
// Strict null checks handling
const productName = product?.name ?? 'Unknown Product';

// Type guards
if (typeof product.name === 'string') {
  // Safe to use product.name as string
}
```

**Problem**: Missing dependencies
```bash
Error: Module not found: Can't resolve '@/components/...'
```

**Solution**:
```bash
# Check tsconfig.json paths
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

#### 2. Runtime Errors

**Problem**: API connection refused
```bash
Error: fetch failed (ECONNREFUSED)
```

**Solution**:
```bash
# 1. Verify backend is running
curl http://localhost:8000/health

# 2. Check environment variables
echo $NEXT_PUBLIC_API_URL

# 3. CORS configuration on backend
```

**Problem**: Chat widget RAG search fails
```bash
Error: 500 Internal Server Error on /search/rag
```

**Solution**:
```bash
# 1. Check ChromaDB status
docker ps | grep chroma

# 2. Verify PostgreSQL connection
docker exec -it lambda-db-1 psql -U lambda_user -d lambda_db

# 3. Check backend logs
docker logs lambda-backend-1
```

#### 3. Performance Issues

**Problem**: Slow initial page load
```bash
Warning: Page Load Time > 3 seconds
```

**Solution**:
```typescript
// 1. Implement code splitting
const AdminPanel = dynamic(() => import('@/components/AdminPanel'), {
  loading: () => <p>Betöltés...</p>,
});

// 2. Optimize images
import Image from 'next/image';

// 3. Reduce initial bundle size
const LazyComponent = lazy(() => import('./HeavyComponent'));
```

**Problem**: Memory leaks in ChatWidget
```bash
Warning: Memory usage increasing over time
```

**Solution**:
```typescript
// 1. Cleanup effects
useEffect(() => {
  const interval = setInterval(() => {
    // Some recurring task
  }, 1000);

  return () => clearInterval(interval); // Cleanup
}, []);

// 2. Limit message history
const MAX_MESSAGES = 50;
const [messages, setMessages] = useState<Message[]>([]);

const addMessage = (newMessage: Message) => {
  setMessages(prev => {
    const updated = [...prev, newMessage];
    return updated.slice(-MAX_MESSAGES); // Keep only last 50
  });
};
```

### Debugging Tools

#### 1. React Developer Tools
```bash
# Install browser extension
# Chrome: React Developer Tools
# Firefox: React Developer Tools

# Component inspection
# Props/State debugging
# Performance profiling
```

#### 2. Network Debugging
```typescript
// API request logging
const debugAPI = {
  log: (method: string, url: string, data?: any) => {
    console.group(`API ${method} ${url}`);
    if (data) console.log('Request data:', data);
    console.groupEnd();
  },
  
  error: (method: string, url: string, error: any) => {
    console.group(`API ERROR ${method} ${url}`);
    console.error('Error:', error);
    console.groupEnd();
  }
};
```

#### 3. Performance Profiling
```typescript
// Performance markers
performance.mark('component-render-start');
// Component rendering
performance.mark('component-render-end');

performance.measure(
  'component-render',
  'component-render-start',
  'component-render-end'
);

const measure = performance.getEntriesByName('component-render')[0];
console.log(`Component render took: ${measure.duration}ms`);
```

---

## 📋 Deployment Checklist

### Pre-deployment Verification

```yaml
Code Quality:
  - [ ] All TypeScript errors resolved
  - [ ] ESLint warnings addressed
  - [ ] Unit tests passing (>80% coverage)
  - [ ] Integration tests passing
  - [ ] E2E tests passing

Performance:
  - [ ] Bundle size analyzed and optimized
  - [ ] Core Web Vitals meet targets (LCP <2.5s, CLS <0.1)
  - [ ] API response times <500ms average
  - [ ] Memory usage stable

Security:
  - [ ] Environment variables properly configured
  - [ ] No sensitive data in client bundle
  - [ ] HTTPS configured for production
  - [ ] API endpoints secured

Functionality:
  - [ ] All navigation tabs working
  - [ ] Dashboard loads real data
  - [ ] Chat widget RAG search functional
  - [ ] Error handling works correctly
  - [ ] Mobile responsiveness verified
```

### Production Deployment Steps

```bash
# 1. Final testing
npm run test
npm run lint
npm run build

# 2. Environment configuration
cp .env.production .env.local

# 3. Database verification
# Verify backend services are running

# 4. Deploy
# Method 1: Docker
docker build -t lambda-frontend .
docker run -p 3000:3000 lambda-frontend

# Method 2: Platform deployment (Vercel, Netlify)
npm run deploy

# 5. Post-deployment verification
curl https://your-domain.com/
# Manual testing of key features
```

### Monitoring Setup

```yaml
Health Checks:
  - [ ] Uptime monitoring configured
  - [ ] Error rate monitoring
  - [ ] Performance monitoring
  - [ ] API dependency monitoring

User Analytics:
  - [ ] Page view tracking
  - [ ] User interaction tracking
  - [ ] Conversion funnel analysis
  - [ ] Search query analytics

Alerts:
  - [ ] Error rate > 5%
  - [ ] Response time > 2s
  - [ ] API failures
  - [ ] Memory usage > 80%
```

---

*Dokumentáció utolsó frissítése: 2025-01-28*
*Verzió: 1.0.0*
*Státusz: Production Ready Deployment Guide* 