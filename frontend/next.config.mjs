/** @type {import('next').NextConfig} */
const nextConfig = {
  // Docker standalone build için gerekli — minimal imaj boyutu
  output: "standalone",

  // Backend container'a server-side istekler için
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${process.env.INTERNAL_API_URL || "http://backend:8000"}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;