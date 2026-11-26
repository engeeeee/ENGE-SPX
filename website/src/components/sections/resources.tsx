import { ArrowUpRight, Cpu, PanelTop } from "lucide-react";
import { Screenshot } from "@/components/interactions";
import { docs } from "@/lib/content";

export function ResourcesSection() {
    return (
        <section id="resources" className="section resource-section" aria-labelledby="resources-title">
            <div className="container showcase showcase-reversed">
                <div className="showcase-copy">
                    <h2 id="resources-title">资源与性能</h2>
                    <p>为 CLI、Chromium、代理网关和会话组件分别设置 CPU 与内存上限。</p>
                    <dl className="detail-list">
                        <div><dt><Cpu size={17} aria-hidden="true" />标准和低资源模式</dt><dd>查看各组件的占用，按需要调整资源预算。</dd></div>
                        <div><dt><PanelTop size={17} aria-hidden="true" />Chromium 按需启动</dt><dd>可单独关闭浏览器，同时保留 CLI 会话。</dd></div>
                    </dl>
                    <a className="text-link" href={docs.resources}>预算与资源监控说明 <ArrowUpRight size={14} aria-hidden="true" /></a>
                </div>
                <div className="showcase-image">
                    <Screenshot id="resources" className="resource-shot" caption />
                </div>
            </div>
        </section>
    );
}
