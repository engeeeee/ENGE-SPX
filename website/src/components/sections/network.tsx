import { Architecture } from "@/components/architecture";
import { Screenshot } from "@/components/interactions";
import { docs } from "@/lib/content";

export function NetworkSection() {
    return (
        <section id="architecture" className="section network-section" aria-labelledby="network-title">
            <div className="container">
                <div className="section-intro">
                    <h2 id="network-title">代理路径与出口核验</h2>
                    <div>
                        <p>选定第一跳线路和落地代理，分别核对两处出口。发现出口或链路异常时停止工作区。</p>
                        <div className="text-links">
                            <a className="text-link" href={docs.proxies}>代理配置</a>
                            <a className="text-link" href={docs.diagnostics}>网络检查</a>
                        </div>
                    </div>
                </div>
                <Architecture />
                <div className="network-preview">
                    <Screenshot id="connection" className="network-shot" caption />
                    <div className="network-preview-copy">
                        <h3>一个落地，两处核验</h3>
                        <p>落地可选 SOCKS5、HTTP 或 HTTPS。软件内双跳由工作台固定第一跳，本机 v2ray 模式由外部客户端负责分流。</p>
                        <a className="text-link" href={docs.security}>网络隔离与安全模型</a>
                    </div>
                </div>
            </div>
        </section>
    );
}
