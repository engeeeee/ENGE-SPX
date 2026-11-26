import { ArrowUpRight, Clipboard, Command, Server } from "lucide-react";
import { Screenshot } from "@/components/interactions";
import { docs, product } from "@/lib/content";

export function TerminalSection() {
    return (
        <section id="terminal" className="section terminal-section" aria-labelledby="terminal-title">
            <div className="container">
                <div className="section-intro">
                    <h2 id="terminal-title">智能终端</h2>
                    <div>
                        <p>0.16.2 更新了标题栏、会话状态和外观设置，提供纯黑与浅色预设。</p>
                        <a className="text-link" href={docs.terminal}>终端外观设置 <ArrowUpRight size={14} aria-hidden="true" /></a>
                    </div>
                </div>
                <div className="terminal-stage">
                    <Screenshot id="terminal" caption />
                </div>
                <div className="features-grid terminal-features">
                    <article>
                        <div className="feature-title"><Clipboard size={19} aria-hidden="true" /><h3>粘贴截图与文件</h3></div>
                        <p>在 CLI 输入区按 <kbd>Ctrl</kbd> + <kbd>V</kbd>，将截图作为图片附加，或插入文件路径。由你按 Enter 发送。</p>
                        <a className="text-link" href={docs.clipboard}>智能粘贴与兼容范围 <ArrowUpRight size={13} aria-hidden="true" /></a>
                    </article>
                    <article>
                        <div className="feature-title"><Command size={19} aria-hidden="true" /><h3>快捷输入</h3></div>
                        <p>保存常用命令和提示词。在 Shell 显示行内建议时，按 <kbd>Tab</kbd> 填入剩余内容。</p>
                    </article>
                    <article>
                        <div className="feature-title"><Server size={19} aria-hidden="true" /><h3>远程 SSH 与 SFTP</h3></div>
                        <p>直接打开已保存的 SSH 连接，通过 SFTP 浏览、上传和下载文件。</p>
                        <a className="text-link" href={product.repository + "/blob/main/README.md#远程-ssh-与-sftp"}>SSH 与 SFTP 说明 <ArrowUpRight size={13} aria-hidden="true" /></a>
                    </article>
                </div>
            </div>
        </section>
    );
}
