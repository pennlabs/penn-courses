/** @type {import('next').NextConfig} */
const nextConfig = {
    async rewrites() {
        return [
            {
                source: "/api/:apipath*",
                destination: "http://127.0.0.1:8000/api/:apipath*",
            },
            {
                source: "/accounts/:path*",
                destination: "http://127.0.0.1:8000/accounts/:path*/",
            },
        ];
    },
};

export default nextConfig;
