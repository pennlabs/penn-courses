/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,
    transpilePackages: ["pcx-shared-components"],
    compiler: {
        styledComponents: true,
    },
};

module.exports = nextConfig;
