import { ArrowDownToLine, ArrowUpRight, Package, Archive } from "lucide-react";
import { CopyChecksum } from "@/components/interactions";
import { docs, product } from "@/lib/content";

export function GetStartedSection() {
    return (
        <section id="get-started" className="section container" aria-labelledby="download-title">
            <div className="download-panel">
                <div>
                    <p className="eyebrow">Windows x64 · v{product.version}</p>
                    <h2 id="download-title">下载 ENGE SPX</h2>
                    <div className="download-options">
                        <a className="download-option" href={product.installer}>
                            <Package size={21} aria-hidden="true" />
                            <span><strong>安装版</strong><small>EXE · {product.installerSize}</small></span>
                            <ArrowDownToLine size={17} aria-hidden="true" />
                        </a>
                        <a className="download-option" href={product.portable}>
                            <Archive size={21} aria-hidden="true" />
                            <span><strong>便携版</strong><small>ZIP · {product.portableSize}</small></span>
                            <ArrowDownToLine size={17} aria-hidden="true" />
                        </a>
                    </div>
                    <div className="text-links">
                        <a className="text-link" href={product.release}>发布说明 <ArrowUpRight size={13} aria-hidden="true" /></a>
                        <CopyChecksum />
                    </div>
                </div>
                <div className="setup">
                    <h3>快速开始</h3>
                    <ol className="setup-list">
                        <li>安装 <a href={docs.docker}>Docker Desktop</a>，启用 WSL2 和 Linux 容器。</li>
                        <li>安装或解压 ENGE SPX，在工作台点击「一键准备环境」。</li>
                        <li>配置线路和落地代理，检查并确认出口。</li>
                        <li>选择项目目录与权限，启动编程工具。</li>
                    </ol>
                    <a className="text-link" href={docs.quickstart}>完整安装指南 <ArrowUpRight size={13} aria-hidden="true" /></a>
                </div>
            </div>
        </section>
    );
}
