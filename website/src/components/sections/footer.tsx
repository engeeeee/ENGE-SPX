import { asset, docs, product } from "@/lib/content";

export function Footer() {
    return (
        <footer className="site-footer">
            <div className="container footer-inner">
                <a href="#" className="brand">
                    <img src={asset("/brand/logo.svg")} alt="" width="32" height="32" />
                    <span>{product.name}</span>
                </a>
                <nav className="footer-links" aria-label="页脚导航">
                    <a href={product.repository}>GitHub</a>
                    <a href={docs.quickstart}>文档</a>
                    <a href={docs.issues}>问题反馈</a>
                    <a href={docs.license}>许可</a>
                </nav>
                <small>© 2026 engeeeee</small>
            </div>
        </footer>
    );
}
