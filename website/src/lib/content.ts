export const product = {
    name: "ENGE SPX",
    version: "0.15.1",
    published: "2026-11-14",
    site: "https://enge1337.cn",
    repository: "https://github.com/engeeeee/ENGE-SPX",
    release:
        "https://github.com/engeeeee/ENGE-SPX/releases/tag/v0.15.1-windows",
    installer:
        "https://github.com/engeeeee/ENGE-SPX/releases/download/v0.15.1-windows/ENGE-SPX-Windows-x64-0.15.1-Setup.exe",
    portable:
        "https://github.com/engeeeee/ENGE-SPX/releases/download/v0.15.1-windows/ENGE-SPX-Windows-x64-0.15.1-Portable.zip",
    installerSha256:
        "043af7f05940f75a9e3e98c2eec4715653f534a3568640e1fa872225eafc889d",
    portableSha256:
        "7b7844e3bb425835f239c4998c14d76486c12d80e8822048a2d67a6a34606976",
    screenshotVersion: "0.13.2",
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
    { id: "features", label: "功能" },
    { id: "architecture", label: "网络路径" },
    { id: "workspace", label: "项目工作区" },
    { id: "terminal", label: "智能终端" },
    { id: "resources", label: "资源管理" },
] as const;

export const screenshots = [
    {
        id: "overview",
        title: "工作台",
        alt: "ENGE SPX 0.13.2 Windows 工作台：一键准备、线路和落地出口、工作区路径",
        source: "/screenshots/overview-web@3x.png",
        width: 960,
        height: 840,
        pixelRatio: 3,
        platform: "Windows 原生界面",
        version: "0.13.2",
        context: "未配置账号与节点",
    },
    {
        id: "workspace",
        title: "项目工作区",
        alt: "真实项目工作区界面：本地目录、身份授权、Claude Code、Codex、终端及 Chromium 入口",
        source: "/screenshots/workspace-web@3x.png",
        width: 1120,
        height: 1050,
        pixelRatio: 3,
        platform: "Windows 原生界面",
        version: "0.13.2",
        context: "未配置账号与节点",
    },
    {
        id: "connection",
        title: "连接与代理",
        alt: "真实连接与代理界面：分别选择落地、前置线路和本机代理",
        source: "/screenshots/connection-web@3x.png",
        width: 840,
        height: 1050,
        pixelRatio: 3,
        platform: "Windows 原生界面",
        version: "0.13.2",
        context: "未配置账号与节点",
    },
    {
        id: "resources",
        title: "资源与性能",
        alt: "真实资源预算界面：网关、会话、CLI 与 Chromium 的 CPU、内存上限",
        source: "/screenshots/resources-web@3x.png",
        width: 840,
        height: 1000,
        pixelRatio: 3,
        platform: "Windows 原生界面",
        version: "0.13.2",
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

export const faqs = [
    {
        question: "可以直接把截图粘贴到 Codex 或 Claude Code 吗？",
        answer: "可以。在偏好设置选择“自动（AI 智能粘贴）”或“智能粘贴终端”，打开工具后，在原来的 CLI 输入区按 Ctrl+V。截图与 PNG/JPEG/WebP 会导入并等待原生图片标记，文字和已有草稿保留，最后由你按 Enter。普通文件以可访问路径引用，具体格式能否解析取决于 CLI 和已有工具。Windows Terminal、PowerShell 和自定义外部终端不接管附件粘贴。",
    },
    {
        question: "时区会按哪个出口调整？Windows 的时区会变吗？",
        answer: "自动模式跟随核验后的最终落地出口，显示 IANA 时区并由你随出口确认。容器内工具与浏览器使用一致的时区，不修改 Windows 系统时区。也可以手动指定固定时区；已有会话需要停止后重新检查与确认。",
    },
    {
        question: "以后怎么更新软件？",
        answer: "0.15 起可在“偏好设置 → 软件更新”检查正式版，下载并校验后由你确认重启。安装版和便携版保留原有配置与数据，更新前正常停止工作区。0.14 及更早版本需先手动安装一次 0.15 或更新版本。",
    },
    {
        question: "这是 Windows 虚拟机吗？",
        answer: "Windows 运行 ENGE SPX 控制界面和你选择的终端窗口。Claude Code、Codex 和 Chromium 实际运行在 Docker Linux 容器中，通常由 Docker Desktop / WSL2 承载，并不是一套独立安装的 Windows 虚拟机。",
    },
    {
        question: "我已经在用 v2rayN，可以继续用吗？",
        answer: "可以。选择本机 v2ray 兼容模式即可沿用现有客户端，外部客户端的按目标分流仍由你配置。也可以导入受支持的加密线路，由 ENGE SPX 固定“线路 → 落地”路径；两种模式的控制边界不同。",
    },
    {
        question: "不同项目会共享账号和浏览器登录状态吗？",
        answer: "默认共享模式保留旧资料，同一身份内的项目会共享账号。需要分开时，请显式创建并绑定不同 Workspace Profile；工具账号、Cookie、Local Storage 和下载按身份保留。切换项目本身不会自动切换身份。",
    },
    {
        question: "打开软件就会启动 Docker 吗？",
        answer: "不会。打开软件只检查状态，由你点击“一键准备环境”或“启动并检测”后才启动 Docker。X 隐藏到托盘；真正退出默认先停止工作区，也可以保存同时正常关闭 Docker Desktop 的偏好。",
    },
    {
        question: "可以把数据放到 D 盘吗？",
        answer: "可以迁移应用配置、日志和下载缓存。Docker 的镜像、容器、数据卷则使用单独的数据盘迁移助手，并在 Docker Desktop 中应用位置变更。这两项迁移相互独立，项目目录也保留在你选择的位置。",
    },
] as const;
