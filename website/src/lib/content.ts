export const themeStorageKey = "enge-spx-color-mode";
export type Theme = "dark" | "light";

export const product = {
    name: "ENGE SPX",
    version: "0.15.6",
    published: "2026-11-22",
    site: "https://enge1337.cn",
    repository: "https://github.com/engeeeee/ENGE-SPX",
    release:
        "https://github.com/engeeeee/ENGE-SPX/releases/tag/v0.15.6-windows",
    installer:
        "https://github.com/engeeeee/ENGE-SPX/releases/download/v0.15.6-windows/ENGE-SPX-Windows-x64-0.15.6-Setup.exe",
    portable:
        "https://github.com/engeeeee/ENGE-SPX/releases/download/v0.15.6-windows/ENGE-SPX-Windows-x64-0.15.6-Portable.zip",
    installerSha256:
        "b2acbed64d3569728f108ea18bcd696cbb198602ebcd6687b0e7d21b989d1fb4",
    portableSha256:
        "86c3c8b8e24ce21eda33c159f0a2347fb3fbca035c6a236728c2fd03cf0dfb87",
    screenshotVersion: "0.15.6",
} as const;

export const docs = {
    quickstart: `${product.repository}/blob/main/docs/quickstart.zh-CN.md`,
    proxies: `${product.repository}/blob/main/docs/proxies.zh-CN.md`,
    protocols: `${product.repository}/blob/main/docs/proxy-p1.zh-CN.md`,
    security: `${product.repository}/blob/main/docs/security-model.zh-CN.md`,
    workspaces: `${product.repository}/blob/main/docs/workspaces.zh-CN.md`,
    resources: `${product.repository}/blob/main/docs/resources.zh-CN.md`,
    recording: `${product.repository}/blob/main/docs/field-recording.zh-CN.md`,
    diagnostics: `${product.repository}/blob/main/docs/network-diagnostics.zh-CN.md`,
    exit: `${product.repository}/blob/main/docs/exit.zh-CN.md`,
    clipboard: `${product.repository}/blob/main/docs/smart-clipboard.zh-CN.md`,
    terminal: `${product.repository}/blob/main/docs/terminal-appearance-performance.zh-CN.md`,
    updates: `${product.repository}/blob/main/docs/updates-and-timezone.zh-CN.md`,
    screenshots: `${product.repository}/blob/main/docs/screenshots/README.md`,
    license: `${product.repository}/blob/main/LICENSE`,
    issues: `${product.repository}/issues`,
    docker: "https://docs.docker.com/desktop/setup/install/windows-install/",
} as const;

export const navigation = [
    { id: "workspace", label: "工作区" },
    { id: "architecture", label: "网络路径" },
    { id: "terminal", label: "终端" },
] as const;

export const screenshots = [
    {
        id: "overview",
        title: "工作台",
        alt: "ENGE SPX Windows 工作台：顶部导航、环境准备、项目工具与代理路径",
        source: `/screenshots/${product.screenshotVersion}/dark/overview.png`,
        lightSource: `/screenshots/${product.screenshotVersion}/light/overview.png`,
        width: 960,
        height: 840,
        pixelRatio: 3,
        platform: "Windows 原生界面",
        version: product.screenshotVersion,
        context: "未配置账号与节点",
    },
    {
        id: "workspace",
        title: "项目工作区",
        alt: "真实项目工作区界面：本地目录、身份授权、Claude Code、Codex、终端及 Chromium 入口",
        source: `/screenshots/${product.screenshotVersion}/dark/workspace.png`,
        lightSource: `/screenshots/${product.screenshotVersion}/light/workspace.png`,
        width: 1120,
        height: 1050,
        pixelRatio: 3,
        platform: "Windows 原生界面",
        version: product.screenshotVersion,
        context: "未配置账号与节点",
    },
    {
        id: "connection",
        title: "连接与代理",
        alt: "真实连接与代理界面：分别选择落地、前置线路和本机代理",
        source: `/screenshots/${product.screenshotVersion}/dark/connection.png`,
        lightSource: `/screenshots/${product.screenshotVersion}/light/connection.png`,
        width: 960,
        height: 960,
        pixelRatio: 3,
        platform: "Windows 原生界面",
        version: product.screenshotVersion,
        context: "未配置账号与节点",
    },
    {
        id: "resources",
        title: "资源与性能",
        alt: "真实资源预算界面：网关、会话、CLI 与 Chromium 的 CPU、内存上限",
        source: `/screenshots/${product.screenshotVersion}/dark/resources.png`,
        lightSource: `/screenshots/${product.screenshotVersion}/light/resources.png`,
        width: 840,
        height: 1000,
        pixelRatio: 3,
        platform: "Windows 原生界面",
        version: product.screenshotVersion,
        context: "未配置账号与节点",
    },
    {
        id: "terminal",
        title: "Codex 智能终端",
        alt: "ENGE SPX 0.15.1 实际运行的 Codex 0.169.0：中文草稿中包含两张原生图片标记与文件路径，尚未发送",
        source: "/screenshots/terminal-codex-0.15.1@2x.png",
        width: 1100,
        height: 680,
        pixelRatio: 2,
        platform: "Linux 实际运行画面",
        version: "0.15.1",
        context: "Codex 0.169.0 · 未发送的测试草稿",
    },
] as const;

export type ScreenshotId = (typeof screenshots)[number]["id"];
export const asset = (path: string) =>
    `${process.env.NEXT_PUBLIC_BASE_PATH || ""}${path}`;

export const screenshotPath = (item: { source: string; lightSource?: string }, theme: Theme) =>
    asset(theme === "light" ? item.lightSource ?? item.source : item.source);

export const faqs = [
    {
        question: "外部终端能用智能粘贴吗？",
        answer: "截图和文件粘贴在 ENGE SPX 自带终端中可用。Windows Terminal、PowerShell 和其他外部终端保留各自的快捷键。",
    },
    {
        question: "我已经在用 v2rayN，可以继续用吗？",
        answer: "可以。选用本机 v2ray 兼容模式，再选择落地代理。按目标分流仍由 v2rayN 管理。",
    },
    {
        question: "如何更新 ENGE SPX？",
        answer: "打开“管理 → 偏好设置 → 常规”，在软件更新里检查正式版。",
    },
] as const;
