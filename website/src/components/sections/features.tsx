import { ArrowUpRight, Box, FolderLock, Route } from "lucide-react";
import { docs } from "@/lib/content";

const features = [
    {
        icon: Box,
        title: "容器工作区",
        body: "在 Docker Linux 工作区里运行 AI 编程工具，按需打开独立 Chromium。",
        href: docs.security,
        link: "安全模型",
    },
    {
        icon: FolderLock,
        title: "项目授权与身份隔离",
        body: "按工作区保存登录状态，只挂载授权的项目目录，支持只读或读写。",
        href: docs.workspaces,
        link: "工作区说明",
    },
    {
        icon: Route,
        title: "指定代理出口",
        body: "配置线路与落地代理，分别核对出口。链路异常时停止工作区。",
        href: "#architecture",
        link: "查看网络路径",
    },
];

export function FeaturesSection() {
    return (
        <section id="features" className="container features-section" aria-label="工作区核心功能">
            <div className="features-grid">
                {features.map(({ icon: Icon, title, body, href, link }) => (
                    <article key={title}>
                        <div className="feature-title"><Icon size={19} aria-hidden="true" /><h2>{title}</h2></div>
                        <p>{body}</p>
                        <a className="text-link" href={href}>{link}<ArrowUpRight size={13} aria-hidden="true" /></a>
                    </article>
                ))}
            </div>
        </section>
    );
}
