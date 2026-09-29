import type { Metadata } from "next";
import "katex/dist/katex.min.css";
import "./globals.css";
import { Nav } from "../components/Nav";
import { AuthProvider } from "../components/auth/AuthProvider";

export const metadata: Metadata = {
  title: "Math9 Tutor",
  description: "Trợ lý học Toán 9 — gợi ý từng bước, hình vẽ chính xác, lời giải được kiểm chứng",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body>
        <AuthProvider>
          <Nav />
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
