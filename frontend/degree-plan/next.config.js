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
        source: '/api/options',
        destination: 'http://127.0.0.1:8000/api/options/'
      },
      {
        source: '/api/base/current/courses/search',
        destination: 'http://127.0.0.1:8000/api/base/2023C/courses/search/' // TODO: remove 2023C
      },
      {
        source: '/api/base/current/courses/:course*',
        destination: 'http://127.0.0.1:8000/api/base/2023C/courses/:course*/' // TODO: remove 2023C
      },
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
