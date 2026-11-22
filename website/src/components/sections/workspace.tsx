import { Screenshot } from "@/components/interactions";
import { docs } from "@/lib/content";

export function WorkspaceSection() {
    return (
        <section id="workspace" className="section container showcase workspace-section" aria-labelledby="workspace-title">
            <div className="showcase-copy">
                <h2 id="workspace-title">项目工作区</h2>
                <p>在左侧选择身份、本地目录和访问权限，在右侧启动 Claude Code、Codex、Antigravity、终端或 Chromium。</p>
                <p>工具账号、会话历史和浏览器资料分别保存在各个工作区。</p>
                <a className="text-link" href={docs.workspaces}>创建与切换工作区</a>
            </div>
            <div className="showcase-image">
                <Screenshot id="workspace" caption />
            </div>
        </section>
    );
}
