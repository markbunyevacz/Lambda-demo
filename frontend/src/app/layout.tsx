import type { Metadata } from 'next'
import './globals.css'
import { ErrorBoundary } from '../components/ErrorBoundary'
import { ToastContainer } from '../components/Toast'

export const metadata: Metadata = {
  title: 'Lambda.hu Építőanyag AI',
  description: 'AI-alapú építőanyag keresési és ajánlási rendszer',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="hu">
      <body>
        <ErrorBoundary>
          {children}
          <ToastContainer position="top-right" />
        </ErrorBoundary>
      </body>
    </html>
  )
} 