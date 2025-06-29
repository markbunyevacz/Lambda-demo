/** @type {import('next').NextConfig} */
const nextConfig = {
  // Az appDir már alapértelmezett a Next.js 13+ verziókban
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://backend:8000/api/:path*',
      },
    ]
  },
}

module.exports = nextConfig 