import type { Metadata } from "next";
import { AuthProvider } from "@/contexts/AuthContext";
import "./globals.css";

export const metadata: Metadata = {
  title: "序话Story - 一句话，一个完整故事",
  description: "AI驱动的条漫和短视频创作平台。输入你的创意，获得可发布的完整作品。",
  keywords: ["AI创作", "条漫", "短视频", "故事创作", "AIGC"],
  authors: [{ name: "序话Story" }],
  openGraph: {
    title: "序话Story - 一句话，一个完整故事",
    description: "AI驱动的条漫和短视频创作平台",
    type: "website",
    locale: "zh_CN",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className="antialiased">
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
