import type { Metadata, Viewport } from "next";
import { GeistSans } from "geist/font/sans";
import { brand, product, themeStorageKey } from "@/lib/content";
import { SiteInteractions } from "@/components/interactions";
import "./globals.css";

export const metadata: Metadata = {
    metadataBase: new URL(product.site),
    title: "ENGE SPX — Windows AI 编程隔离工作台与原生 SSH / SFTP 终端",
    description:
        "在 Windows 上使用 Docker 容器隔离运行 Claude Code、Codex、Antigravity 与 Chromium。提供双跳代理出口核验、截图直贴智能终端、DPAPI 加密远程 SSH 与内置 SFTP 文件管理器。",
    applicationName: product.name,
    alternates: { canonical: "/" },
    openGraph: {
        title: "ENGE SPX — Windows AI 编程隔离工作台与原生 SSH / SFTP 终端",
        description:
            "Windows 上的 AI 编程隔离工作台。Docker 容器工作区、独立账号身份、双跳代理出口核验、智能粘贴终端以及远程 SSH + SFTP。",
        url: product.site,
        siteName: product.name,
        locale: "zh_CN",
        type: "website",
        images: [
            {
                url: "/og.png",
                width: 1200,
                height: 630,
                alt: `ENGE SPX 官网与真实 ${product.version} 软件界面`,
            },
        ],
    },
    twitter: {
        card: "summary_large_image",
        title: "ENGE SPX — Windows AI 编程隔离工作台",
        images: ["/og.png"],
    },
    icons: {
        icon: [brand.icon, { url: brand.logo, type: "image/svg+xml", sizes: "any" }],
        apple: { url: brand.touchIcon, sizes: "180x180" },
    },
    robots: { index: true, follow: true },
};

export const viewport: Viewport = {
    themeColor: "#000000",
    colorScheme: "dark light",
    width: "device-width",
    initialScale: 1,
};

export default function RootLayout({
    children,
}: Readonly<{ children: React.ReactNode }>) {
    return (
        <html
            lang="zh-CN"
            className={GeistSans.variable}
            data-theme="dark"
            suppressHydrationWarning
        >
            <head>
                <script
                    dangerouslySetInnerHTML={{
                        __html: `try{if(localStorage.getItem(${JSON.stringify(themeStorageKey)})==="light")document.documentElement.dataset.theme="light"}catch{}`,
                    }}
                />
            </head>
            <body>
                <SiteInteractions>{children}</SiteInteractions>
            </body>
        </html>
    );
}
