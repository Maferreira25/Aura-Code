import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  generateBuildId: async () => "auracode-studio-0.3.0-dev.0",
  poweredByHeader: false,
  reactStrictMode: true,
};

export default nextConfig;
