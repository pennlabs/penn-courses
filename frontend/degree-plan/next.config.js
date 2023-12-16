/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
}

module.exports = {...nextConfig,
  // async rewrites() {
  //   return [
  //     {
  //       source: '/api/*',
  //       destination: 'http://localhost:5000/api/*'
  //     },
  //   ]
  // }
}
