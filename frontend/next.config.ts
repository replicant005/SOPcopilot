import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  devIndicators: false,
  async rewrites() {
    const backend =
      process.env.BACKEND_URL ?? "http://127.0.0.1:10000"; // only as a dev default
    return [
      {
        source: "/api/pipeline/:path*",
        destination: `${backend}/api/pipeline/:path*`,
      },
    ];
  },
};

export default nextConfig;
