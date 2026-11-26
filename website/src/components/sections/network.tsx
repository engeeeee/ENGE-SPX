import { Architecture } from "@/components/architecture";
import { Screenshot } from "@/components/interactions";
import { docs } from "@/lib/content";

const protocols = [
    "VLESS (TLS / WS / gRPC / Reality / Vision)",
    "Trojan (TLS / WS / gRPC)",
    "VMess (AEAD)",
    "Shadowsocks (AEAD / 2022)",
    "Hysteria2 (QUIC/UDP)",
    "SOCKS5 / HTTP / HTTPS 落地",
] as const;

export function NetworkSection() {
    return (
        <section
            id="architecture"
            className="section section-band"
            aria-labelledby="network-title"
        >
            <div className="container">
                <div className="section-intro">
                    <div>
                        <span className="kicker">NETWORK ARCHITECTURE</span>
                        <h2 id="network-title">双跳代理链路与独立出口核验</h2>
                    </div>
                    <div className="section-intro-copy">
                        <p>
                            选定第一跳加密线路与落地代理后，软件分别检查线路出口和最终落地出口，由你确认后才启动工作区；不写入 DIRECT 或隐式回退，且不修改 Windows 系统代理。
                        </p>
                        <div className="text-links">
                            <a className="text-link" href={docs.proxies}>
                                代理配置指南
                            </a>
                            <a className="text-link" href={docs.protocols}>
                                协议与组合限制
                            </a>
                            <a className="text-link" href={docs.diagnostics}>
                                网络检查与 HTTPS 测速
                            </a>
                        </div>
                    </div>
                </div>
                <Architecture />
                <div className="protocol-strip" aria-label="支持的代理协议">
                    {protocols.map((item) => (
                        <span className="protocol-chip" key={item}>
                            {item}
                        </span>
                    ))}
                </div>
                <div className="network-preview">
                    <Screenshot id="connection" caption />
                    <div className="network-preview-copy">
                        <h3>单个可控落地，运行期持续守望</h3>
                        <p>
                            工作区仅通过受控网关接入选定出口。支持从分享链接、Base64、Clash / Mihomo YAML 或订阅导入节点（只提取可用节点，不执行分流或回退规则）；运行环境与订阅还可通过独立下载代理获取。
                        </p>
                        <p>
                            启用期间持续监测连接、出口和拓扑变化；检测到异常直连或出口漂移时自动停止当前工作区。
                        </p>
                        <a className="text-link" href={docs.security}>
                            查看网络隔离与安全模型
                        </a>
                    </div>
                </div>
            </div>
        </section>
    );
}
