import type { NextConfig } from "next";

// Deploy tách riêng: đặt BACKEND_URL (vd. https://math9-api.onrender.com) và NEXT_PUBLIC_API_URL=""
// để trình duyệt gọi /api/* cùng tên miền với frontend, Next.js chuyển tiếp sang backend.
// Cookie đăng nhập khi đó là cookie "first-party" — không bị Safari/Chrome chặn như cookie bên thứ ba.
const BACKEND_URL = process.env.BACKEND_URL?.replace(/\/+$/, "");

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return BACKEND_URL ? [{ source: "/api/:path*", destination: `${BACKEND_URL}/api/:path*` }] : [];
  },
};

export default nextConfig;
