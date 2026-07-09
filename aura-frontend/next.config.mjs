/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [{
      source: "/api/backend/:path*",
      destination: "https://au-0c55d1a299ec4e8e98d08645f4cb7e46.ecs.us-east-1.on.aws/:path*"
    }];
  },
  httpAgentOptions: { keepAlive: true },
  experimental: { proxyTimeout: 600000 },
};
export default nextConfig;
