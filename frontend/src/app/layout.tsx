import type { Metadata } from 'next'
import './globals.css'

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
      <body>{children}</body>
    </html>
  )
} 