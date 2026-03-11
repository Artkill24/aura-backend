/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [{ 
      source: "/api/backend/:path*", 
      destination: "https://artkill24-aura-backend.hf.space/:path*" 
    }];
  },
  httpAgentOptions: { keepAlive: true },
  experimental: { proxyTimeout: 300000 },
};
module.exports = nextConfig;
