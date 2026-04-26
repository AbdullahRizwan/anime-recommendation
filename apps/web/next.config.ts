import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // API calls from Server Components go here — never exposed to the browser.
  env: {
    API_URL: process.env.API_URL ?? "http://localhost:8000",
  },
};

export default nextConfig;
