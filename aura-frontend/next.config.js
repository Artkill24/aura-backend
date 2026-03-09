/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [{ 
      source: "/api/backend/:path*", 
      destination: "https://aura-backend-production-4f12.up.railway.app/:path*" 
    }];
  },
  httpAgentOptions: { keepAlive: true },
  experimental: { proxyTimeout: 300000 },
};
module.exports = nextConfig;
