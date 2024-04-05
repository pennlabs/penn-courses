const PROXY_URL =
  process.env.NODE_ENV === "production" ? "" : "http://127.0.0.1:8000";

/** @type {import('next').NextConfig} */
const nextConfig = {
  trailingSlash: true,
  skipTrailingSlashRedirect: true,
  transpilePackages: ["pcx-shared-components"],
  reactStrictMode: true,
  compiler: {
    styledComponents: {
      ssr: true,
      displayName: true,
    },
  },
  async rewrites() {
    return [
      {
        source: "/api/options",
        destination: `${PROXY_URL}/api/options/`,
      },
      {
        source: "/api/base/all/search/courses",
        destination: `${PROXY_URL}/api/base/all/search/courses/`, // TODO: remove 2023C
      },
      {
        source: "/api/base/all/courses/:course*",
        destination: `${PROXY_URL}/api/base/all/courses/:course*/`, // TODO: remove 2023C
      },
      {
        source: "/api/:apipath*",
        destination: `${PROXY_URL}/api/:apipath*`,
      },
      {
        source: "/accounts/:path*",
        destination: `${PROXY_URL}/accounts/:path*/`,
      },
    ];
  },
};

module.exports = nextConfig;
