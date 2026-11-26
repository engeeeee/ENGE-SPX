import { ArrowUpRight, FolderOpen, IdCard, Terminal } from "lucide-react";
import { Screenshot } from "@/components/interactions";
import { docs } from "@/lib/content";

export function WorkspaceSection() {
    return (
        <section id="workspace" className="section container showcase workspace-section" aria-labelledby="workspace-title">
            <div className="showcase-copy">
                <h2 id="workspace-title">独立的项目工作区</h2>
                <p>从左侧导航打开项目工作区，先选身份与目录，再启动工具。</p>
                <dl className="detail-list">
                    <div><dt><FolderOpen size={17} aria-hidden="true" />项目目录</dt><dd>只挂载你选中的本地文件夹，支持只读或读写。</dd></div>
                    <div><dt><IdCard size={17} aria-hidden="true" />工作区身份</dt><dd>账号、会话历史和浏览器资料按身份保存。</dd></div>
                    <div><dt><Terminal size={17} aria-hidden="true" />工具入口</dt><dd>打开 Claude Code、Codex、Antigravity、Linux 终端或 Chromium。</dd></div>
                </dl>
                <a className="text-link" href={docs.workspaces}>创建与切换工作区 <ArrowUpRight size={14} aria-hidden="true" /></a>
            </div>
            <div className="showcase-image">
                <Screenshot id="workspace" className="workspace-shot" caption />
            </div>
        </section>
    );
}
