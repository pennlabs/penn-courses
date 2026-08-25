/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,
    compiler: {
        styledComponents: {
            ssr: true,
            displayName: true,
        },
    },
    // The backend is proxied by server.js, not by Next rewrites — see the comment
    // there for why. Nothing to configure here.
};

module.exports = nextConfig;
