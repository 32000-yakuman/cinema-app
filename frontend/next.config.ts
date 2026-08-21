/** @type {import('next').NextConfig} */
const nextConfig = {
  allowedDevOrigins: ['127.0.0.1', 'localhost'],
  skipTrailingSlashRedirect: true,
  async rewrites() {
    return [
      {
        source: '/api/cinema/:path*',
        destination: 'http://backend:8000/api/cinema/:path*/'
      },
    ]
  },
}

module.exports = nextConfig