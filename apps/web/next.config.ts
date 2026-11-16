import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone", // a small server for the Docker image
  /* config options here */
  // Every page here depends on the signed-in person, so nothing is prerendered or cached.
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
