import { Screenshot } from "@/components/interactions";
import { product } from "@/lib/content";

export function HeroSection() {
    return (
        <section className="hero container" aria-labelledby="hero-title">
            <div className="hero-heading">
                <div>
                    <p className="eyebrow">Windows x64 · <a href={product.release}>v{product.version}</a></p>
                    <h1 id="hero-title">Windows 上的<br />AI 编程隔离工作台</h1>
                </div>
                <div className="hero-lead">
                    <p>在 Docker 容器里运行 Claude Code、Codex 和 Antigravity。按工作区保存账号和浏览器资料，核对代理出口后启动。</p>
                    <div className="actions">
                        <a className="button button-primary" href={product.installer}>下载 Windows 版</a>
                        <a className="button button-secondary" href={product.repository}>GitHub</a>
                    </div>
                </div>
            </div>
            <div className="hero-stage">
                <Screenshot id="overview" priority />
            </div>
            <p className="image-caption">ENGE SPX 工作台 · Windows 实机截图 · v{product.screenshotVersion}</p>
        </section>
    );
}
