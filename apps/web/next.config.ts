import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  env: {
    API_URL: process.env.API_URL ?? "http://localhost:8000",
  },
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "s4.anilist.co" },
    ],
  },
};

export default nextConfig;
