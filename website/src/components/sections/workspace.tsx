import { Screenshot } from "@/components/interactions";
import { docs } from "@/lib/content";

export function WorkspaceSection() {
    return (
        <section id="workspace" className="section container showcase workspace-section" aria-labelledby="workspace-title">
            <div className="showcase-copy">
                <h2 id="workspace-title">项目工作区</h2>
                <p>选择本地目录和挂载权限，再启动 Claude Code、Codex、Antigravity、Linux 终端或 Chromium。</p>
                <p>工作区分别保存工具账号、会话历史和浏览器资料。切换回去可继续使用原来的资料。</p>
                <a className="text-link" href={docs.workspaces}>创建与切换工作区</a>
            </div>
            <div className="showcase-image">
                <Screenshot id="workspace" caption />
            </div>
        </section>
    );
}
