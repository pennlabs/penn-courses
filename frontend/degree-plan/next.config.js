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
  webpack(config) {
    Object.defineProperty(config, 'devtool', {
        get() {
            return 'source-map';
        },
        set() {},
    });
    return config;
},
  async rewrites() {
    if (process.env.node !== "production") {
      return [
        {
          source: "/api/options",
          destination: "http://127.0.0.1:8000/api/options/",
        },
        {
          source: "/api/base/all/search/courses",
          destination: "http://127.0.0.1:8000/api/base/all/search/courses/", // TODO: remove 2023C
        },
        {
          source: "/api/base/all/courses/:course*",
          destination: "http://127.0.0.1:8000/api/base/all/courses/:course*/", // TODO: remove 2023C
        },
        {
          source: "/api/:apipath*",
          destination: "http://127.0.0.1:8000/api/:apipath*",
        },
        {
          source: "/accounts/:path*",
          destination: "http://127.0.0.1:8000/accounts/:path*/",
        },
      ];
    }
    return [];
  },
};

module.exports = nextConfig;
