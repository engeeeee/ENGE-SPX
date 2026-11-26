import { Archive, ArrowDownToLine, ArrowUpRight, Package } from "lucide-react";
import { CopyChecksum } from "@/components/interactions";
import { docs, product } from "@/lib/content";

export function GetStartedSection() {
    return (
        <section
            id="get-started"
            className="section container"
            aria-labelledby="download-title"
        >
            <div className="download-panel">
                <div>
                    <p className="eyebrow">
                        WINDOWS x64 · v{product.version} · {product.published}
                    </p>
                    <h2 id="download-title">下载与获取 ENGE SPX</h2>
                    <p style={{ marginTop: "0.7rem", fontSize: "0.94rem" }}>
                        安装版与便携版均内嵌全部运行时及 <code>spx.exe</code>{" "}
                        命令行入口，开箱即用无需另配 Python 环境。
                    </p>
                    <div className="download-options">
                        <a className="download-option" href={product.installer}>
                            <Package size={21} aria-hidden="true" />
                            <span>
                                <strong>Windows 安装版</strong>
                                <small>
                                    Setup.exe · {product.installerSize}
                                </small>
                            </span>
                            <ArrowDownToLine size={17} aria-hidden="true" />
                        </a>
                        <a className="download-option" href={product.portable}>
                            <Archive size={21} aria-hidden="true" />
                            <span>
                                <strong>Windows 便携版</strong>
                                <small>
                                    Portable.zip · {product.portableSize}
                                </small>
                            </span>
                            <ArrowDownToLine size={17} aria-hidden="true" />
                        </a>
                    </div>
                    <div className="text-links">
                        <a className="text-link" href={product.release}>
                            GitHub Releases{" "}
                            <ArrowUpRight size={13} aria-hidden="true" />
                        </a>
                        <a className="text-link" href={docs.releaseNotes}>
                            {product.version} 更新日志{" "}
                            <ArrowUpRight size={13} aria-hidden="true" />
                        </a>
                        <CopyChecksum
                            hash={product.installerSha256}
                            label="安装版"
                        />
                        <CopyChecksum
                            hash={product.portableSha256}
                            label="便携版"
                        />
                    </div>
                </div>
                <div className="setup">
                    <h3>四步完成环境部署</h3>
                    <ol className="setup-list">
                        <li>
                            安装一次{" "}
                            <a
                                href={docs.docker}
                                target="_blank"
                                rel="noreferrer"
                            >
                                Docker Desktop
                            </a>
                            ，确认启用 WSL 2 与 Linux containers（仅远程 SSH / SFTP 可免 Docker 直接使用）。
                        </li>
                        <li>
                            运行安装版或解压便携版，进入工作台点击「一键准备环境」（约 1 GB，支持断点续传与校验）。
                        </li>
                        <li>
                            在「连接与代理」配置第一跳线路与落地代理，核验两处出口后确认启用。
                        </li>
                        <li>
                            选择项目目录与授权模式，打开 Claude Code、Codex、Antigravity，或前往「远程 SSH」直连服务器。
                        </li>
                    </ol>
                    <a className="text-link" href={docs.quickstart}>
                        完整快速入门指南{" "}
                        <ArrowUpRight size={14} aria-hidden="true" />
                    </a>
                </div>
            </div>
        </section>
    );
}
