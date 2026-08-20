/** @type {import('next').NextConfig} */
const nextConfig = {
  allowedDevOrigins: ['127.0.0.1', 'localhost'],
  skipTrailingSlashRedirect: true,
  async rewrites() {
    return [
      {
        source: '/api/inventory/:path*',
        destination: 'http://backend:8000/api/inventory/:path*/'
      },
    ]
  },
}

module.exports = nextConfig