"use client";

import { useState } from "react";
import { ArrowDownToLine, ArrowUpRight, FolderOpen, LayoutGrid, Network } from "lucide-react";
import { Screenshot } from "@/components/interactions";
import { product, type ScreenshotId } from "@/lib/content";

const views = [
    { id: "overview", label: "工作台", icon: LayoutGrid },
    { id: "workspace", label: "项目工作区", icon: FolderOpen },
    { id: "connection", label: "连接与代理", icon: Network },
] as const;

export function HeroSection() {
    const [view, setView] = useState<ScreenshotId>("overview");
    return (
        <section className="hero container" aria-labelledby="hero-title">
            <div className="hero-heading">
                <a className="release-link" href={product.release}>
                    <span className="release-dot" aria-hidden="true" />
                    v{product.version} 正式版 <ArrowUpRight size={14} aria-hidden="true" />
                </a>
                <h1 id="hero-title"><span>Windows AI</span><span>编程隔离工作台</span></h1>
                <p className="hero-description">在 Docker 容器里运行 Claude Code、Codex 和 Antigravity。按工作区隔离账号与浏览器资料，核对代理出口后启动。</p>
                <div className="actions">
                    <a className="button button-primary" href={product.installer}><ArrowDownToLine size={17} aria-hidden="true" />下载 Windows 版</a>
                    <a className="button button-secondary" href={product.repository}>GitHub <ArrowUpRight size={15} aria-hidden="true" /></a>
                </div>
                <p className="hero-requirements">Windows x64 · 容器工作区需要 Docker Desktop</p>
            </div>
            <div className="hero-preview">
                <div className="preview-toolbar">
                    <div className="preview-options" role="group" aria-label="软件界面预览">
                        {views.map(({ id, label, icon: Icon }) => (
                            <button key={id} aria-pressed={view === id} onClick={() => setView(id)}>
                                <Icon size={15} aria-hidden="true" />
                                {label}
                            </button>
                        ))}
                    </div>
                    <span className="preview-platform">Windows 实机</span>
                </div>
                <div className="hero-stage">
                    <Screenshot id={view} priority />
                </div>
            </div>
        </section>
    );
}
