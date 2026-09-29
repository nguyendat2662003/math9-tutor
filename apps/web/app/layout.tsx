import type { Metadata, Viewport } from "next";
import "katex/dist/katex.min.css";
import "./globals.css";
import { Nav } from "../components/Nav";
import { AuthProvider } from "../components/auth/AuthProvider";

export const metadata: Metadata = {
  title: "Math9 Tutor — Học Toán 9 thật vui",
  description: "Trợ lý học Toán 9 — gợi ý từng bước, hình vẽ chính xác, lời giải được kiểm chứng",
};

export const viewport: Viewport = {
  themeColor: "#6353e8",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <head>
        {/* Be Vietnam Pro: phông tròn, dễ đọc, đủ dấu tiếng Việt. Mất mạng thì rơi về phông hệ thống. */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap"
        />
      </head>
      <body>
        <AuthProvider>
          <Nav />
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
