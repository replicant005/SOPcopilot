import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    const backend =
      process.env.BACKEND_URL ?? "http://127.0.0.1:5000"; // only as a dev default
    return [
      {
        source: "/api/pipeline/:path*",
        destination: `${backend}/api/pipeline/:path*`,
      },
    ];
  },
};

export default nextConfig;
