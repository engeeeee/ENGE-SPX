import { Screenshot } from "@/components/interactions";
import { SectionLabel, TextLink } from "@/components/section-ui";
import { docs } from "@/lib/content";
import { Architecture } from "@/components/architecture";

export function NetworkSection() {
    return (
        <section id="architecture" className="section architecture-section">
            <div className="container">
                <div className="section-heading" data-reveal>
                    <div>
                        <SectionLabel number="02">
                            网络与代理
                        </SectionLabel>
                        <h2>
                            固定加密线路，
                            <br />
                            <span className="muted-heading">
                                再连接所选落地。
                            </span>
                        </h2>
                    </div>
                    <p className="heading-description">
                        加密线路负责第一跳，落地代理决定最终出口。
                        <br />
                        分别核验两个出口，连接异常时停止工作环境。
                    </p>
                </div>
                <Architecture />
                <div className="network-detail" data-reveal>
                    <Screenshot id="connection" className="connection-shot" />
                    <div className="network-copy">
                        <span className="eyebrow">PROXY PROTOCOLS</span>
                        <h3>
                            你的线路。
                            <br />
                            你的落地。
                            <br />
                            <span>分别选择。</span>
                        </h3>
                        <p>
                            沿用已有线路，或导入受支持的协议。软件内双跳固定“加密线路
                            → 落地”，也为现有本机 v2ray 客户端保留兼容入口。
                        </p>
                        <div className="protocol-list">
                            <span>VLESS / Reality</span>
                            <span>Trojan</span>
                            <span>VMess</span>
                            <span>Shadowsocks</span>
                            <span>Hysteria2</span>
                            <span>WS / gRPC</span>
                        </div>
                        <p className="small-copy">
                            Clash / Mihomo 配置只提取节点，不执行导入的
                            DIRECT、分组或回退策略。Hysteria2 需要实际 UDP
                            路径。
                        </p>
                        <TextLink href={docs.protocols}>
                            查看协议与组合范围
                        </TextLink>
                    </div>
                </div>
            </div>
        </section>
    );
}
