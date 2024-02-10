/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: ['pcx-shared-components'],
  reactStrictMode: true,
  compiler: {
    styledComponents: {
      ssr: true,
      displayName: true
    }
  },
}

module.exports = nextConfig
