import { ArrowUpRight } from "lucide-react";
import { asset, docs, product } from "@/lib/content";

export function Footer() {
    return (
        <footer className="site-footer">
            <div className="container">
                <div className="footer-top">
                    <a href="#" className="brand">
                        <img
                            src={asset("/brand/logo.svg")}
                            alt=""
                            width="38"
                            height="38"
                        />
                        <span>ENGE SPX</span>
                    </a>
                    <p>
                        Windows AI 编程隔离工作台。
                        <br />
                        <span>容器工作区、智能终端与代理出口核验。</span>
                    </p>
                    <div className="footer-links">
                        <a
                            href={product.repository}
                            target="_blank"
                            rel="noreferrer"
                        >
                            GitHub
                            <ArrowUpRight size={12} />
                        </a>
                        <a
                            href={docs.quickstart}
                            target="_blank"
                            rel="noreferrer"
                        >
                            使用文档
                            <ArrowUpRight size={12} />
                        </a>
                        <a
                            href={docs.security}
                            target="_blank"
                            rel="noreferrer"
                        >
                            安全模型
                            <ArrowUpRight size={12} />
                        </a>
                        <a href={docs.license} target="_blank" rel="noreferrer">
                            许可说明
                            <ArrowUpRight size={12} />
                        </a>
                    </div>
                </div>
                <div className="footer-bottom">
                    <span>© 2026 engeeeee. ENGE SPX.</span>
                    <a href={docs.license} target="_blank" rel="noreferrer">
                        PolyForm Noncommercial 1.0.0
                    </a>
                    <span>
                        Windows x64 · Docker Desktop / WSL2
                        <span className="tiny-dot" />
                    </span>
                </div>
            </div>
        </footer>
    );
}
