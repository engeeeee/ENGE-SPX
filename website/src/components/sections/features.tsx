import { Box, FolderLock, Gauge } from "lucide-react";
import { docs } from "@/lib/content";

const features = [
    {
        icon: Box,
        title: "容器工作区",
        body: "AI 编程工具在 Docker Desktop 的 Linux 容器里运行，可按需启动独立的 Chromium。",
        href: docs.security,
        link: "安全模型",
    },
    {
        icon: FolderLock,
        title: "独立资料与文件权限",
        body: "新建工作区时从空白登录状态开始。只挂载你选择的项目，支持只读和读写。",
        href: docs.workspaces,
        link: "工作区说明",
    },
    {
        icon: Gauge,
        title: "资源控制",
        body: "给 CLI、浏览器和网关分别设置 CPU 与内存预算。关闭浏览器后可继续使用 CLI。",
        href: "#resources",
        link: "查看资源设置",
    },
];

export function FeaturesSection() {
    return (
        <section id="features" className="section container" aria-labelledby="features-title">
            <h2 id="features-title">工作区功能</h2>
            <div className="features-grid">
                {features.map(({ icon: Icon, title, body, href, link }) => (
                    <article key={title}>
                        <Icon size={23} strokeWidth={1.5} aria-hidden="true" />
                        <h3>{title}</h3>
                        <p>{body}</p>
                        <a className="text-link" href={href}>{link}</a>
                    </article>
                ))}
            </div>
        </section>
    );
}
