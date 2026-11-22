import { Screenshot } from "@/components/interactions";
import { docs } from "@/lib/content";

export function TerminalSection() {
    return (
        <section id="terminal" className="section terminal-section" aria-labelledby="terminal-title">
            <div className="container">
                <div className="section-intro">
                    <h2 id="terminal-title">智能粘贴终端</h2>
                    <div>
                        <p>在 Claude Code 或 Codex 输入区按 <kbd>Ctrl</kbd> + <kbd>V</kbd>。截图作为原生图片附加，普通文件插入容器可访问的路径。按 Enter 发送。</p>
                        <a className="text-link" href={docs.clipboard}>粘贴与兼容范围</a>
                    </div>
                </div>
                <div className="terminal-stage">
                    <Screenshot id="terminal" caption />
                </div>
            </div>
        </section>
    );
}
