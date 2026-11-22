import { Architecture } from "@/components/architecture";
import { Screenshot } from "@/components/interactions";
import { docs } from "@/lib/content";

export function NetworkSection() {
    return (
        <section id="architecture" className="section container network-section" aria-labelledby="network-title">
            <div className="section-intro">
                <h2 id="network-title">代理路径与出口</h2>
                <div>
                    <p>选定第一跳线路和落地代理，分别核对两处出口。发现出口或链路异常时停止工作区。</p>
                    <div className="text-links">
                        <a className="text-link" href={docs.proxies}>代理配置</a>
                        <a className="text-link" href={docs.diagnostics}>网络检查</a>
                    </div>
                </div>
            </div>
            <Architecture />
            <div className="network-shot">
                <Screenshot id="connection" className="shot-cropped" caption />
            </div>
        </section>
    );
}
