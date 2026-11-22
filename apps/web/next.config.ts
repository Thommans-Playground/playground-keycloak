import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone", // a small server for the Docker image
  poweredByHeader: false, // NFR-6: do not name the framework in every answer
  // NFR-6: browser protection on every page. A starting policy: no framing, no other base address, no plugins.
  // A script-src needs per-request nonces with Next's own scripts, so it is a separate step.
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "Content-Security-Policy", value: "frame-ancestors 'none'; base-uri 'self'; object-src 'none'" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
        ],
      },
    ];
  },
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
