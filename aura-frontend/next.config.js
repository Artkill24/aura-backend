/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [{ source: "/api/backend/:path*", destination: "http://localhost:8000/:path*" }];
  },
  httpAgentOptions: {
    keepAlive: true,
  },
  experimental: {
    proxyTimeout: 300000,
  },
};
module.exports = nextConfig;
