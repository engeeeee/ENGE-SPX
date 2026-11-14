import type { Metadata, Viewport } from "next";
import { GeistSans } from "geist/font/sans";
import { product } from "@/lib/content";
import { SiteInteractions } from "@/components/interactions";
import "./globals.css";

export const metadata: Metadata = {
    metadataBase: new URL(product.site),
    title: "ENGE SPX — Windows AI 编程隔离工作台",
    description:
        "在 Windows 管理 Claude Code、Codex 与 Chromium 容器工作区。支持截图和文件粘贴、独立身份、固定代理链路、出口核验、资源预算、自动时区与软件内更新。",
    applicationName: product.name,
    alternates: { canonical: "/" },
    openGraph: {
        title: "ENGE SPX — Windows AI 编程隔离工作台",
        description:
            "Windows 上的 AI 编程隔离工作台。容器工作区、独立身份、固定代理链路与出口核验。",
        url: product.site,
        siteName: product.name,
        locale: "zh_CN",
        type: "website",
        images: [
            {
                url: "/og.png",
                width: 1200,
                height: 630,
                alt: "ENGE SPX 官网与真实 Windows 软件界面",
            },
        ],
    },
    twitter: {
        card: "summary_large_image",
        title: "ENGE SPX — Windows AI 编程隔离工作台",
        images: ["/og.png"],
    },
    icons: { icon: "/brand/logo.svg", apple: "/apple-touch-icon.png" },
    robots: { index: true, follow: true },
};

export const viewport: Viewport = {
    themeColor: "#191815",
    colorScheme: "dark",
    width: "device-width",
    initialScale: 1,
};

export default function RootLayout({
    children,
}: Readonly<{ children: React.ReactNode }>) {
    return (
        <html lang="zh-CN" className={GeistSans.variable}>
            <body>
                <SiteInteractions>{children}</SiteInteractions>
            </body>
        </html>
    );
}
