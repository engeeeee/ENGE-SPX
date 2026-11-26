"use client";

import { useState } from "react";
import {
    ArrowDownToLine,
    ArrowUpRight,
    CheckCircle2,
    FolderOpen,
    LayoutGrid,
    Network,
    Server,
    Terminal,
} from "lucide-react";
import { Screenshot } from "@/components/interactions";
import { product, type ScreenshotId } from "@/lib/content";

const views = [
    { id: "overview", label: "工作台", icon: LayoutGrid },
    { id: "workspace", label: "项目工作区", icon: FolderOpen },
    { id: "ssh", label: "远程 SSH", icon: Server },
    { id: "connection", label: "连接与代理", icon: Network },
    { id: "terminal", label: "智能终端", icon: Terminal },
] as const;

const pillars = [
    "Docker 容器运行 Claude Code / Codex",
    "双跳加密线路与双出口独立核验",
    "多会话分组终端与 Ctrl+V 截图直贴",
    "DPAPI SSH、断线自动重连与 SFTP",
] as const;

export function HeroSection() {
    const [view, setView] = useState<ScreenshotId>("overview");
    return (
        <section className="hero container" aria-labelledby="hero-title">
            <div className="hero-heading">
                <a className="release-link" href={product.release}>
                    <span className="release-dot" aria-hidden="true" />
                    v{product.version} 正式版 · {product.published}{" "}
                    <ArrowUpRight size={13} aria-hidden="true" />
                </a>
                <h1 id="hero-title">
                    <span>Windows AI</span>
                    <span>编程隔离工作台</span>
                </h1>
                <p className="hero-description">
                    在隔离的 Docker Linux 容器中运行 Claude Code、Codex、Antigravity 与专用 Chromium；支持固定双跳出口核验、智能粘贴终端，以及带内置 SFTP 的原生远程 SSH 客户端。
                </p>
                <div className="actions">
                    <a className="button button-primary" href={product.installer}>
                        <ArrowDownToLine size={17} aria-hidden="true" />
                        下载安装版 ({product.installerSize})
                    </a>
                    <a className="button button-secondary" href="#get-started">
                        便携版与校验
                    </a>
                    <a
                        className="text-link"
                        href={product.repository}
                        target="_blank"
                        rel="noreferrer"
                    >
                        GitHub <ArrowUpRight size={14} aria-hidden="true" />
                    </a>
                </div>
                <div className="hero-meta">
                    <span>Windows 10/11 x64</span>
                    <span>·</span>
                    <span>无需另装 Python</span>
                    <span>·</span>
                    <span>容器工作区需 Docker Desktop (WSL 2)</span>
                </div>
                <div className="hero-pillars" aria-label="核心能力摘要">
                    {pillars.map((item) => (
                        <div className="hero-pillar" key={item}>
                            <CheckCircle2 size={15} aria-hidden="true" />
                            <span>{item}</span>
                        </div>
                    ))}
                </div>
            </div>
            <div className="hero-preview">
                <div className="preview-toolbar">
                    <div
                        className="preview-options"
                        role="group"
                        aria-label="软件界面预览"
                    >
                        {views.map(({ id, label, icon: Icon }) => (
                            <button
                                key={id}
                                aria-pressed={view === id}
                                onClick={() => setView(id)}
                            >
                                <Icon size={14} aria-hidden="true" />
                                {label}
                            </button>
                        ))}
                    </div>
                    <span className="preview-platform">v{product.version}</span>
                </div>
                <div className="hero-stage">
                    <Screenshot id={view} priority />
                </div>
            </div>
        </section>
    );
}
