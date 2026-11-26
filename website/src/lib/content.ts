export const themeStorageKey = "enge-spx-color-mode";
export type Theme = "dark" | "light";

export const product = {
    name: "ENGE SPX",
    version: "0.16.5",
    published: "2026-11-26",
    site: "https://enge1337.cn",
    repository: "https://github.com/engeeeee/ENGE-SPX",
    release:
        "https://github.com/engeeeee/ENGE-SPX/releases/tag/v0.16.5-windows",
    installer:
        "https://github.com/engeeeee/ENGE-SPX/releases/download/v0.16.5-windows/ENGE-SPX-Windows-x64-0.16.5-Setup.exe",
    portable:
        "https://github.com/engeeeee/ENGE-SPX/releases/download/v0.16.5-windows/ENGE-SPX-Windows-x64-0.16.5-Portable.zip",
    installerSize: "35.6 MB",
    portableSize: "54.8 MB",
    installerSha256:
        "1d1ed37abe14016576e959908026e36da565d6205cfd2fdfcefff40c3ba1ebf9",
    portableSha256:
        "710e83db867f126806e414419f8ac7d16b943f53102cb76bf04fe75cfdfc8ed8",
    screenshotVersion: "0.16.2",
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
    ssh: `${product.repository}/blob/main/docs/storage-terminal.zh-CN.md#ssh-连接及文件粘贴`,
    sftp: `${product.repository}/blob/main/docs/storage-terminal.zh-CN.md#sftp-文件管理`,
    storage: `${product.repository}/blob/main/docs/storage-terminal.zh-CN.md`,
    updates: `${product.repository}/blob/main/docs/updates-and-timezone.zh-CN.md`,
    screenshots: `${product.repository}/blob/main/docs/screenshots/README.md`,
    releaseNotes: `${product.repository}/blob/main/docs/releases/0.16.5.zh-CN.md`,
    license: `${product.repository}/blob/main/LICENSE`,
    issues: `${product.repository}/issues`,
    docker: "https://docs.docker.com/desktop/setup/install/windows-install/",
} as const;

export const navigation = [
    { id: "workspace", label: "工作区" },
    { id: "architecture", label: "代理网络" },
    { id: "terminal", label: "智能终端" },
    { id: "ssh", label: "远程 SSH" },
    { id: "resources", label: "资源预算" },
] as const;

export const screenshots = [
    {
        id: "overview",
        title: "工作台",
        alt: "ENGE SPX Windows 工作台，显示左侧导航、环境准备和代理路径",
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
        alt: "项目工作区界面：本地目录、身份授权、Claude Code、Codex、终端及 Chromium 入口",
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
        alt: "连接与代理界面：分别选择落地代理、前置加密线路和本机下载代理",
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
        id: "ssh",
        title: "远程 SSH 管理",
        alt: "远程 SSH 管理页：保存多台服务器配置，支持 DPAPI 凭据保存、私钥登录、一键终端与 SFTP",
        source: `/screenshots/${product.screenshotVersion}/dark/ssh.png`,
        lightSource: `/screenshots/${product.screenshotVersion}/light/ssh.png`,
        width: 960,
        height: 840,
        pixelRatio: 2,
        platform: "ENGE SPX 界面示例",
        version: product.screenshotVersion,
        context: "使用 RFC 5737 示例地址演示",
    },
    {
        id: "ssh-terminal",
        title: "分组与 SSH 智能终端",
        alt: "ENGE SPX 0.16.5 多会话分组终端：可收起左侧会话栏统一切换容器与 SSH 会话，支持独立窗口、快捷输入、SFTP 与 Ctrl+V 自动上传",
        source: "/screenshots/0.16.5/terminal-ssh@2x.png",
        lightSource: "/screenshots/0.16.5/terminal-ssh-light@2x.png",
        width: 1100,
        height: 680,
        pixelRatio: 2,
        platform: "分组终端真实界面示例",
        version: "0.16.5",
        context: "可收起会话侧栏 · 独立窗口 · SFTP · 自动重连",
    },
    {
        id: "sftp",
        title: "SFTP 文件管理器",
        alt: "内置 SFTP 文件管理器：路径导航、文件大小与修改时间列表、多选上传、下载和传输进度",
        source: `/screenshots/${product.screenshotVersion}/sftp@2x.png`,
        lightSource: `/screenshots/${product.screenshotVersion}/sftp-light@2x.png`,
        width: 860,
        height: 560,
        pixelRatio: 2,
        platform: "SFTP 文件管理器",
        version: product.screenshotVersion,
        context: "基于系统 OpenSSH SFTP v3",
    },
    {
        id: "terminal",
        title: "Codex 智能终端",
        alt: "ENGE SPX 0.16.2 实际运行 Codex，中文草稿中有两张图片附件和一个文件引用",
        source: `/screenshots/${product.screenshotVersion}/terminal-codex@2x.png`,
        lightSource: `/screenshots/${product.screenshotVersion}/terminal-codex-light@2x.png`,
        width: 1100,
        height: 680,
        pixelRatio: 2,
        platform: "Linux 实际运行画面",
        version: product.screenshotVersion,
        context: "Codex 0.169.0 · 未发送的测试草稿",
    },
    {
        id: "resources",
        title: "资源与性能",
        alt: "资源预算界面：网关、会话、CLI 与 Chromium 的 CPU、内存上限",
        source: `/screenshots/${product.screenshotVersion}/dark/resources.png`,
        lightSource: `/screenshots/${product.screenshotVersion}/light/resources.png`,
        width: 840,
        height: 1000,
        pixelRatio: 3,
        platform: "Windows 原生界面",
        version: product.screenshotVersion,
        context: "未配置账号与节点",
    },
] as const;

export type ScreenshotId = (typeof screenshots)[number]["id"];
export const asset = (path: string) =>
    `${process.env.NEXT_PUBLIC_BASE_PATH || ""}${path}`;

export const brand = {
    logo: asset(`/brand/logo.svg?v=${product.version}`),
    icon: asset(`/favicon.ico?v=${product.version}`),
    touchIcon: asset(`/apple-touch-icon.png?v=${product.version}`),
} as const;

export const screenshotPath = (
    item: { source: string; lightSource?: string },
    theme: Theme,
) => asset(theme === "light" ? item.lightSource ?? item.source : item.source);

export const faqs = [
    {
        question: "外部终端（Windows Terminal / PowerShell）能用智能粘贴吗？",
        answer: "Ctrl+V 直接粘贴截图和文件仅在 ENGE SPX 内置智能终端中生效。如果配置使用 Windows Terminal、PowerShell 或自定义程序，软件保留第三方终端原有快捷键与行为，不劫持系统热键。",
    },
    {
        question: "本地已经在用 v2rayN / Clash 等客户端，可以共存吗？",
        answer: "可以。ENGE SPX 不修改 Windows 系统代理。代理页面可选「本机 v2ray 兼容模式」，让外部客户端负责第一跳，工作台仍保留工作区内部网关与落地出口核验。",
    },
    {
        question: "多个容器终端或 SSH 会话可以合并管理，或拆成独立窗口吗？",
        answer: "可以。容器工具与 SSH 会话默认进入同一个分组终端窗口，在可收起的左侧会话栏之间切换即可；点击顶栏「独立窗口」可弹出为单独窗口（如放在副屏对比输出），也能随时点击「移回会话窗口」，迁移过程中会话进程、历史与草稿保持不断。",
    },
    {
        question: "SSH 断线后能自动恢复吗？密码和私钥口令保存在哪里？",
        answer: "SSH 网络断开时，终端会保留最多 10,000 行历史输出并按 1–30 秒退避自动重试重连，重新握手时照常核验服务器公钥指纹。密码或私钥口令仅使用当前 Windows 用户的 DPAPI 加密存储在本地，不上传任何云端服务；编辑机器时勾选「清除已保存的凭据」即可删除，多因素认证机器可留空密码交互输入。",
    },
    {
        question: "SSH 终端里 Ctrl+V 上传文件大小与远端目录规则是什么？",
        answer: "在 SSH 终端按下 Ctrl+V 或右键粘贴本机图片/文件时，系统 SFTP 客户端会先核对主机密钥，随后上传至远端账户主目录的 .enge-spx-paste-* 文件夹并自动把远端路径填入输入框。单文件上限 128 MiB，单批上限 256 MiB。",
    },
    {
        question: "首次运行环境占用多大？可以把数据迁移到 D 盘吗？",
        answer: "Linux 容器运行环境首次约需 1 GB，在软件内一键准备即可（下载后自动校验 SHA-256，校验导入后自动清理包缓存）。可在「偏好设置 → 存储」中一键迁移应用数据，或通过 Docker 数据盘迁移助手引导更换盘符。",
    },
    {
        question: "如何更新与安全回退？",
        answer: "软件启动时默认检查正式版更新，可在「偏好设置 → 常规」查看或关闭；下载的新包仍保持数据兼容性。退出软件默认隐藏到托盘，真正退出时可按规则安全停止工作区容器，也可按需同时关闭 Docker Desktop。",
    },
] as const;
