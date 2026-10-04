import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async redirects() {
    return [{ source: "/tafe-id/:path*", destination: "https://ninadnaik.dev/tafe-id/:path*", permanent: true }];
  },
};

export default nextConfig;
