import { brand, docs, product } from "@/lib/content";

export function Footer() {
    return (
        <footer className="site-footer">
            <div className="container">
                <div className="footer-grid">
                    <div className="footer-brand">
                        <a href="#" className="brand">
                            <img
                                src={brand.logo}
                                alt=""
                                width="30"
                                height="30"
                            />
                            <span>{product.name}</span>
                        </a>
                        <p>
                            Windows AI 编程隔离工作台：Docker Linux 容器工作区、固定双跳代理核验、智能终端以及集成 SFTP 的远程 SSH 客户端。
                        </p>
                    </div>
                    <div className="footer-col">
                        <h4>核心功能</h4>
                        <ul>
                            <li>
                                <a href="#workspace">项目工作区</a>
                            </li>
                            <li>
                                <a href="#architecture">双跳代理与出口</a>
                            </li>
                            <li>
                                <a href="#terminal">智能粘贴终端</a>
                            </li>
                            <li>
                                <a href="#ssh">远程 SSH 与 SFTP</a>
                            </li>
                            <li>
                                <a href="#resources">资源与磁盘迁移</a>
                            </li>
                        </ul>
                    </div>
                    <div className="footer-col">
                        <h4>参考文档</h4>
                        <ul>
                            <li>
                                <a href={docs.quickstart}>快速入门指南</a>
                            </li>
                            <li>
                                <a href={docs.proxies}>代理配置说明</a>
                            </li>
                            <li>
                                <a href={docs.security}>隔离与安全模型</a>
                            </li>
                            <li>
                                <a href={docs.ssh}>SSH 与 SFTP 指南</a>
                            </li>
                            <li>
                                <a href={docs.terminal}>终端外观与性能</a>
                            </li>
                        </ul>
                    </div>
                    <div className="footer-col">
                        <h4>发布与源码</h4>
                        <ul>
                            <li>
                                <a href={product.release}>
                                    v{product.version} 正式版下载
                                </a>
                            </li>
                            <li>
                                <a href={docs.releaseNotes}>版本更新说明</a>
                            </li>
                            <li>
                                <a href={product.repository}>GitHub 仓库</a>
                            </li>
                            <li>
                                <a href={docs.issues}>反馈与支持</a>
                            </li>
                            <li>
                                <a href={docs.license}>PolyForm 非商业许可</a>
                            </li>
                        </ul>
                    </div>
                </div>
                <div className="footer-bottom">
                    <small>
                        © 2026 engeeeee · ENGE SPX v{product.version} (Windows x64)
                    </small>
                    <small>
                        PolyForm Noncommercial 1.0.0 · 正式域名 {product.site}
                    </small>
                </div>
            </div>
        </footer>
    );
}
