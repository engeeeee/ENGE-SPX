import { ArrowUpRight, FolderOpen, Globe, IdCard, Terminal } from "lucide-react";
import { Screenshot } from "@/components/interactions";
import { docs } from "@/lib/content";

export function WorkspaceSection() {
    return (
        <section
            id="workspace"
            className="section container showcase workspace-section"
            aria-labelledby="workspace-title"
        >
            <div className="showcase-copy">
                <span className="kicker">WORKSPACES & IDENTITIES</span>
                <h2 id="workspace-title">独立的项目工作区与身份边界</h2>
                <p>
                    从左侧导航进入「项目工作区」，先选定身份和本地项目目录，再决定是否允许容器写入；同一套代码库可随时切换不同工作区账号。
                </p>
                <dl className="detail-list">
                    <div>
                        <dt>
                            <FolderOpen size={17} aria-hidden="true" />
                            显式目录权限控制
                        </dt>
                        <dd>
                            仅挂载选中的项目目录，可在应用前显式切换只读项目或读写项目模式。
                        </dd>
                    </div>
                    <div>
                        <dt>
                            <IdCard size={17} aria-hidden="true" />
                            账号与浏览器资料隔离
                        </dt>
                        <dd>
                            不同工作区身份独立保存 Claude / Codex 登录态与 Chromium Cookie、缓存卷。
                        </dd>
                    </div>
                    <div>
                        <dt>
                            <Terminal size={17} aria-hidden="true" />
                            统一 CLI 与容器语言适配
                        </dt>
                        <dd>
                            一键拉起 Claude Code、Codex、Antigravity、Linux 终端或沙箱 Chromium，容器 UTF-8 语言可跟随代理出口地区。
                        </dd>
                    </div>
                </dl>
                <a className="text-link" href={docs.workspaces}>
                    创建与切换工作区 <ArrowUpRight size={14} aria-hidden="true" />
                </a>
            </div>
            <div className="showcase-image">
                <Screenshot id="workspace" caption />
            </div>
        </section>
    );
}
