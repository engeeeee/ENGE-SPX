import {
    ArrowUpRight,
    Clock3,
    Cpu,
    Download,
    PanelsTopLeft,
    Waypoints,
} from "lucide-react";
import { Screenshot } from "@/components/interactions";
import { SectionLabel, TextLink } from "@/components/section-ui";
import { docs } from "@/lib/content";

export function ResourcesSection() {
    return (
        <section id="resources" className="section resources-section">
            <div className="container">
                <div className="resources-layout">
                    <div className="resources-copy" data-reveal>
                        <SectionLabel number="05">资源与环境设置</SectionLabel>
                        <h2>
                            按组件设置
                            <br />
                            <span className="clay-text">CPU 和内存上限。</span>
                        </h2>
                        <p className="resource-intro">
                            网关、会话、CLI 项目与 Chromium，分别设置 CPU
                            和内存上限。正常与低资源模式之间，自由选择适合当前工作的预算。
                        </p>
                        <div className="resource-details">
                            <div>
                                <Cpu size={18} />
                                <div>
                                    <h3>组件预算，项目也能单独设</h3>
                                    <p>
                                        每个环境有自己的上限，多项目按各自预算运行。
                                    </p>
                                </div>
                            </div>
                            <div>
                                <PanelsTopLeft size={18} />
                                <div>
                                    <h3>需要时，再打开浏览器</h3>
                                    <p>
                                        低资源模式默认按需启动；也可停止
                                        Chromium，保留 CLI。
                                    </p>
                                </div>
                            </div>
                            <div>
                                <Waypoints size={18} />
                                <div>
                                    <h3>看清占用来源</h3>
                                    <p>
                                        区分应用、容器与
                                        WSL2，按需记录资源或检查网络。
                                    </p>
                                </div>
                            </div>
                        </div>
                        <TextLink href={docs.resources}>了解资源管理</TextLink>
                        <p className="resource-note">
                            预算是上限，不是预留或实测占用；降低预算可能影响编译速度。安全监测独立运行。
                        </p>
                    </div>
                    <div className="resources-visual" data-reveal>
                        <div className="resource-halo" aria-hidden="true" />
                        <div className="resource-visual-label mono">
                            <span>CONTAINER RESOURCE LIMITS</span>
                            <span>CPU / MEMORY</span>
                        </div>
                        <Screenshot id="resources" className="resources-shot" />
                        <div className="resource-bottom-note">
                            <span>
                                <span className="tiny-dot" />
                                真实预算设置界面
                            </span>
                            <span>
                                可为当前项目设置独立预算{" "}
                                <ArrowUpRight size={12} />
                            </span>
                        </div>
                    </div>
                </div>
                <div className="environment-settings" data-reveal>
                    <article>
                        <Clock3 size={22} />
                        <div>
                            <h3>时区跟随最终落地出口</h3>
                            <p>
                                核验最终出口后显示对应 IANA
                                时区，由你确认再启用。工具和浏览器使用一致的容器时区，也可手动固定；不改
                                Windows 系统时区。
                            </p>
                            <TextLink href={docs.updates}>
                                时区设置说明
                            </TextLink>
                        </div>
                    </article>
                    <article>
                        <Download size={22} />
                        <div>
                            <h3>在软件内检查与安装更新</h3>
                            <p>
                                偏好设置中检查正式版，下载并校验文件后确认重启。支持安装版和便携版，保留配置与数据。0.14
                                及更早版本需先手动升级一次。
                            </p>
                            <TextLink href={docs.updates}>
                                软件更新说明
                            </TextLink>
                        </div>
                    </article>
                </div>
            </div>
        </section>
    );
}
