import { ArrowUpRight, Box, FolderLock, Route, Server } from "lucide-react";
import { docs } from "@/lib/content";

const features = [
    {
        icon: Box,
        title: "容器工作区隔离",
        body: "AI 编程工具与专用 Chromium 在独立 Linux 容器中运行，降低宿主机文件与全局环境变量暴露。",
        href: docs.security,
        link: "隔离与安全模型",
    },
    {
        icon: FolderLock,
        title: "身份分离与目录授权",
        body: "按工作区身份保存工具账号与浏览器资料，仅显式挂载选中项目目录，支持只读或读写。",
        href: docs.workspaces,
        link: "工作区与身份说明",
    },
    {
        icon: Route,
        title: "双跳线路与异常停机",
        body: "固定加密第一跳串联 SOCKS5/HTTP(S) 落地，核对两处出口后启用；发现异常自动停止环境。",
        href: "#architecture",
        link: "查看网络路径",
    },
    {
        icon: Server,
        title: "原生远程 SSH 与 SFTP",
        body: "Windows DPAPI 加密保存主机凭据；终端支持万行回看、Tab 补全、Ctrl+V 自动传图与 SFTP 文件管理。",
        href: "#ssh",
        link: "查看 SSH 功能",
    },
];

export function FeaturesSection() {
    return (
        <section
            id="features"
            className="container pillars-section"
            aria-label="工作台核心能力"
        >
            <div className="pillars-grid">
                {features.map(({ icon: Icon, title, body, href, link }) => (
                    <article className="pillar-card" key={title}>
                        <div className="pillar-icon" aria-hidden="true">
                            <Icon size={18} />
                        </div>
                        <h2>{title}</h2>
                        <p>{body}</p>
                        <a className="text-link" href={href}>
                            {link}
                            <ArrowUpRight size={13} aria-hidden="true" />
                        </a>
                    </article>
                ))}
            </div>
        </section>
    );
}
