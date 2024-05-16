const BACKEND_URL = process.env.BACKEND_URL ?? 'https://penncoursereview.com';

/** @type {import('next').NextConfig} */
const nextConfig = {
    rewrites: async () => {
        return [
            {
                source: '/api/:path*',
                destination: `${BACKEND_URL}/api/:path*`,
            },
            {
                source: '/assets/:path*',
                destination: `${BACKEND_URL}/assets/:path*`,
            }
        ]
    },
}

export default nextConfig;
