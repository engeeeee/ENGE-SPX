import { ClipboardPaste, MousePointer2, Palette } from "lucide-react";
import { Screenshot } from "@/components/interactions";
import { SectionLabel, TextLink } from "@/components/section-ui";
import { docs } from "@/lib/content";

export function TerminalSection() {
    return (
        <section id="terminal" className="section terminal-section">
            <div className="container">
                <div className="section-heading" data-reveal>
                    <div>
                        <SectionLabel number="04">智能粘贴终端</SectionLabel>
                        <h2>
                            在 CLI 里直接粘贴
                            <br />
                            <span className="muted-heading">
                                文字、截图和文件。
                            </span>
                        </h2>
                    </div>
                    <p className="heading-description">
                        Claude Code、Codex 仍使用自己的交互界面。
                        <br />
                        Ctrl+V 将内容放进当前草稿，由你按 Enter 发送。
                        <br />
                        无需保存截图、填写容器路径或打开上传窗口。
                    </p>
                </div>
                <div className="terminal-stage" data-reveal>
                    <Screenshot
                        id="terminal"
                        className="terminal-shot"
                        caption
                    />
                </div>
                <div className="terminal-details" data-reveal>
                    <article>
                        <ClipboardPaste size={21} />
                        <h3>截图附加，文件引用</h3>
                        <p>
                            截图和 PNG/JPEG/WebP 以 CLI
                            原生图片标记附加；PDF、文档与代码文件保留原件并插入容器内路径。支持多文件和连续混合粘贴，不清空已有输入。
                        </p>
                    </article>
                    <article>
                        <MousePointer2 size={21} />
                        <h3>复制、编辑与查看历史</h3>
                        <p>
                            拖选后自动复制，右键粘贴到草稿。支持中文输入法、ANSI
                            颜色和滚动历史；支持原生鼠标的 CLI 可单击定位，Codex
                            草稿可全选后删除。
                        </p>
                    </article>
                    <article>
                        <Palette size={21} />
                        <h3>外观与操作偏好可保存</h3>
                        <p>
                            调整字体、字号、暖灰／紫晶／石墨配色及背景不透明度。Windows
                            可选 Acrylic
                            毛玻璃，实际效果取决于系统支持。重新打开终端恢复已保存设置。
                        </p>
                    </article>
                </div>
                <div className="terminal-note">
                    <p>
                        智能附件粘贴仅用于 ENGE SPX
                        自带终端。外部终端保留原有行为；普通文件是否能解析取决于
                        CLI 及项目工具。上图来自 Linux 上实际运行的产品终端与
                        Codex，草稿未发送，不是 Windows 毛玻璃效果展示。
                    </p>
                    <div>
                        <TextLink href={docs.clipboard}>
                            粘贴使用与兼容范围
                        </TextLink>
                        <TextLink href={docs.terminal}>
                            终端操作与外观设置
                        </TextLink>
                    </div>
                </div>
            </div>
        </section>
    );
}
