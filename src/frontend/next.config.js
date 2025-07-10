/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    instrumentationHook: false,
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `http://backend:8000/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig; 