import { ArrowUpRight, Clipboard, Command, SlidersHorizontal } from "lucide-react";
import { Screenshot } from "@/components/interactions";
import { docs } from "@/lib/content";

export function TerminalSection() {
    return (
        <section
            id="terminal"
            className="section container terminal-section"
            aria-labelledby="terminal-title"
        >
            <div className="section-intro">
                <div>
                    <span className="kicker">SMART TERMINAL</span>
                    <h2 id="terminal-title">为 AI CLI 打造的智能粘贴终端</h2>
                </div>
                <div className="section-intro-copy">
                    <p>
                        0.16.2–0.16.5 持续完善智能终端外观与多会话体验：纯黑高对比画布搭配深蓝点缀、浅色预设与无边框外观面板；多个容器与 SSH 会话共用可收起左侧会话栏，并可随时一键拆出「独立窗口」或「移回会话窗口」。
                    </p>
                    <a className="text-link" href={docs.terminal}>
                        终端外观与渲染说明 <ArrowUpRight size={14} aria-hidden="true" />
                    </a>
                </div>
            </div>
            <div className="terminal-stage">
                <Screenshot id="terminal" caption />
            </div>
            <div className="terminal-features">
                <article className="feature-card">
                    <div className="feature-title">
                        <Clipboard size={18} aria-hidden="true" />
                        <h3>Ctrl+V 截图与文件直贴</h3>
                    </div>
                    <p>
                        在 Claude Code / Codex 输入区按 <kbd>Ctrl</kbd> +{" "}
                        <kbd>V</kbd>，剪贴板截图转为原生附件标记，本机文件直接传入并填入路径，始终由你亲自按 Enter 发送。
                    </p>
                    <a className="text-link" href={docs.clipboard}>
                        智能粘贴架构与兼容说明{" "}
                        <ArrowUpRight size={13} aria-hidden="true" />
                    </a>
                </article>
                <article className="feature-card">
                    <div className="feature-title">
                        <Command size={18} aria-hidden="true" />
                        <h3>快捷输入与行内补全</h3>
                    </div>
                    <p>
                        按 <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>P</kbd>{" "}
                        或点击顶栏「快捷输入」插入常用指令与模板；支持命令行灰色后缀提示按{" "}
                        <kbd>Tab</kbd>{" "}
                        一键行内补全，并为 Antigravity CLI 缩放同步备用屏幕视口。
                    </p>
                    <a className="text-link" href={docs.storage}>
                        快捷输入使用说明{" "}
                        <ArrowUpRight size={13} aria-hidden="true" />
                    </a>
                </article>
                <article className="feature-card">
                    <div className="feature-title">
                        <SlidersHorizontal size={18} aria-hidden="true" />
                        <h3>外观、材质与第三方面板</h3>
                    </div>
                    <p>
                        自定义 21 项界面配色、纯黑/紫晶/石墨色调、等宽字体字号及 Windows 透明材质（Acrylic / Mica / Blur），改动实时保存。
                    </p>
                    <a className="text-link" href={docs.terminal}>
                        性能、字号与外观设置{" "}
                        <ArrowUpRight size={13} aria-hidden="true" />
                    </a>
                </article>
            </div>
        </section>
    );
}
