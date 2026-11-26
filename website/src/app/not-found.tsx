import { asset, brand } from "@/lib/content";
export default function NotFound() {
    return (
        <main className="not-found">
            <img
                src={brand.logo}
                width="64"
                height="64"
                alt="ENGE SPX"
            />
            <span className="eyebrow">404</span>
            <h1>找不到页面</h1>
            <a className="button button-primary" href={asset("/")}>
                返回 ENGE SPX 首页
            </a>
        </main>
    );
}
