/** @type {import('next').NextConfig} */
const nextConfig = {
  trailingSlash: true,
  skipTrailingSlashRedirect: true,
  transpilePackages: ['pcx-shared-components'],
  reactStrictMode: true,
  compiler: {
    styledComponents: {
      ssr: true,
      displayName: true
    }
  },
  async rewrites() {
    return [
      {
        source: '/api/:apipath*',
        destination: 'http://127.0.0.1:8000/api/:apipath*'
      },
      {
        source: '/accounts/:path*',
        destination: 'http://127.0.0.1:8000/accounts/:path*/'
      }
    ]
  }
}

module.exports = nextConfig
