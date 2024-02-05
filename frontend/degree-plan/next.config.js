/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ["pcx-shared-components"],
}

module.exports = {...nextConfig,
  trailingSlash: true,
  async rewrites() {
    console.log("Rewrites called");
    return [
        {
          source: '/api/:path*',
          destination: 'http://localhost:8000/api/:path*/'
        },
        {
          source: '/accounts/:path*',
          destination: 'http://localhost:8000/accounts/:path*/'
        }
      ];
  }
}
