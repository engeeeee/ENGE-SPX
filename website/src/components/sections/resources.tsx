import { ArrowUpRight, Cpu, HardDrive, PanelTop, Power } from "lucide-react";
import { Screenshot } from "@/components/interactions";
import { docs } from "@/lib/content";

export function ResourcesSection() {
    return (
        <section
            id="resources"
            className="section container showcase showcase-reversed resource-section"
            aria-labelledby="resources-title"
        >
            <div className="showcase-copy">
                <span className="kicker">RESOURCES & STORAGE</span>
                <h2 id="resources-title">精细资源预算与存储可控</h2>
                <p>
                    为受控网关、会话容器、CLI 与专用 Chromium 分别设定 CPU 和内存上限；支持低资源模式、实机资源录制与跨盘迁移。
                </p>
                <dl className="detail-list">
                    <div>
                        <dt>
                            <Cpu size={17} aria-hidden="true" />
                            分组件配额与实机占用分析
                        </dt>
                        <dd>
                            区分桌面进程、容器组、Docker Desktop 与 WSL2 开销，支持导出脱敏资源录制报告。
                        </dd>
                    </div>
                    <div>
                        <dt>
                            <PanelTop size={17} aria-hidden="true" />
                            按需启动和独立关闭浏览器
                        </dt>
                        <dd>
                            默认无需常驻浏览器；完成登录后可「停止浏览器 · 保留 CLI」，释放闲置内存。
                        </dd>
                    </div>
                    <div>
                        <dt>
                            <HardDrive size={17} aria-hidden="true" />
                            应用数据迁移与安全退出
                        </dt>
                        <dd>
                            支持一键迁移应用数据至指定盘符、引导迁移 Docker 数据盘；托盘退出可安全停止工作区或联动关闭 Docker Desktop。
                        </dd>
                    </div>
                </dl>
                <div className="text-links">
                    <a className="text-link" href={docs.resources}>
                        资源预算说明{" "}
                        <ArrowUpRight size={13} aria-hidden="true" />
                    </a>
                    <a className="text-link" href={docs.storage}>
                        磁盘迁移指南{" "}
                        <ArrowUpRight size={13} aria-hidden="true" />
                    </a>
                    <a className="text-link" href={docs.exit}>
                        <Power size={13} aria-hidden="true" /> 退出流程
                    </a>
                </div>
            </div>
            <div className="showcase-image">
                <Screenshot id="resources" caption />
            </div>
        </section>
    );
}
