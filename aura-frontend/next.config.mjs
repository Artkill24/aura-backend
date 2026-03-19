/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [{
      source: "/api/backend/:path*",
      destination: "https://giving-elegance-production.up.railway.app/:path*"
    }];
  },
  httpAgentOptions: { keepAlive: true },
  experimental: { proxyTimeout: 300000 },
};
export default nextConfig;
