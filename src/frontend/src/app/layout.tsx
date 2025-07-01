import type { Metadata } from 'next'
import './globals.css'
import Link from 'next/link'

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
        <nav className="bg-gray-800 text-white px-4 py-3 flex gap-6">
          <Link href="/" className="font-semibold hover:text-gray-300">Home</Link>
          <Link href="/categories" className="hover:text-gray-300">Categories</Link>
          <Link href="/manufacturers" className="hover:text-gray-300">Manufacturers</Link>
          <Link href="/products" className="hover:text-gray-300">Products</Link>
        </nav>
        {children}
      </body>
    </html>
  )
} 